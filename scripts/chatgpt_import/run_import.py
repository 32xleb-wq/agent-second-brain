"""Orchestrates the whole ChatGPT → Obsidian text import.

Designed to run unattended (systemd/tmux), resumable after interruption,
memory-safe (streams the export, one conversation at a time), and
idempotent (safe to re-run — already-imported conversations are skipped
via state.json, keyed by ChatGPT's own conversation id).

Usage:
    run_import.py [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import traceback
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import ijson

from extract_text import main as extract_main  # noqa: F401 (kept importable for reuse)
from extract_text import wanted as _wanted
from mdrender import render_conversation
from overview import write_overview
from state import load as load_state
from state import save as save_state
from zipscan import TruncatedArchive, extract_entry_to_file, iter_entries, open_zip, skip_entry_data

IMPORT_ROOT = Path("/home/secondbrain/imports/chatgpt-export")
ZIP_PATH = next(IMPORT_ROOT.glob("*.zip"))
EXTRACTED_DIR = IMPORT_ROOT / "extracted"
STATE_PATH = IMPORT_ROOT / "state" / "progress.json"
LOG_PATH = IMPORT_ROOT / "state" / "import.log"

VAULT_ROOT = Path("/home/secondbrain/projects/agent-second-brain/vault")
CHATS_DIR = VAULT_ROOT / "Imports" / "ChatGPT" / "chats"
OVERVIEW_PATH = VAULT_ROOT / "Imports" / "ChatGPT" / "00 — Обзор импорта.md"

SHARD_GLOB = "conversations-*.json"

logger = logging.getLogger("chatgpt_import")


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)
    logger.addHandler(sh)


def ensure_extracted() -> list[Path]:
    """Idempotent: only extracts entries that are missing or size-mismatched."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    extracted_now = []
    try:
        with open_zip(ZIP_PATH) as f:
            for entry in iter_entries(f):
                if not _wanted(entry.name):
                    skip_entry_data(f, entry)
                    continue
                dest = EXTRACTED_DIR / entry.name
                if dest.exists() and entry.usize is not None and dest.stat().st_size == entry.usize:
                    skip_entry_data(f, entry)
                    continue
                written = extract_entry_to_file(f, entry, dest)
                extracted_now.append(dest)
                logger.info("extracted %s (%s bytes)", entry.name, f"{written:,}")
    except TruncatedArchive:
        pass  # expected: archive ends inside the attachment dump we don't want
    return sorted(EXTRACTED_DIR.glob(SHARD_GLOB))


def iter_conversations(shard_paths: list[Path]):
    for shard in shard_paths:
        with open(shard, "rb") as f:
            for conv in ijson.items(f, "item", use_float=True):
                yield shard.name, conv


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="process at most N new conversations")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    setup_logging()
    logger.info("=== import run start (limit=%s dry_run=%s) ===", args.limit, args.dry_run)

    shard_paths = ensure_extracted()
    if not shard_paths:
        logger.error("no conversations-*.json found after extraction — aborting")
        return 1
    logger.info("shards: %s", [p.name for p in shard_paths])

    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state(STATE_PATH)

    newly_imported = 0
    already_done = 0
    failed_now = 0
    total_seen = 0
    t0 = time.time()

    for shard_name, conv in iter_conversations(shard_paths):
        total_seen += 1
        conv_id = conv.get("id") or conv.get("conversation_id") or f"{shard_name}:{total_seen}"

        if conv_id in state["done"]:
            already_done += 1
            continue

        # Self-healing dedupe: if state.json was lost but the file is
        # already on disk (deterministic name), don't re-render/duplicate.
        title_hint = (conv.get("title") or "").strip()
        if title_hint:
            from mdrender import slugify

            date_slug = ""
            if conv.get("create_time"):
                date_slug = datetime.fromtimestamp(conv["create_time"], tz=UTC).strftime("%Y-%m-%d")
            short_id = (conv_id or "no-id")[:8]
            base = f"{date_slug}-{slugify(title_hint)}-{short_id}"
            existing = sorted(p.name for p in CHATS_DIR.glob(f"{base}*.md"))
            if existing:
                state["done"][conv_id] = {
                    "title": title_hint,
                    "files": existing,
                    "tags": ["general"],
                    "tag_confidence": "preliminary",
                    "note": "recovered: file(s) already existed on disk (state.json rebuilt)",
                    "processed_at": datetime.now(tz=UTC).isoformat(),
                }
                already_done += 1
                continue

        if args.limit is not None and newly_imported >= args.limit:
            continue

        try:
            result = render_conversation(conv, zip_source=ZIP_PATH.name, imported_date=str(datetime.now(tz=UTC).date()))
            if not args.dry_run:
                for filename, content in result.files:
                    (CHATS_DIR / filename).write_text(content, encoding="utf-8")
                state["done"][conv_id] = {
                    "title": result.title,
                    "files": [fn for fn, _ in result.files],
                    "tags": result.tags,
                    "tag_confidence": result.tag_confidence,
                    "message_count": result.message_count,
                    "branch_count": result.branch_count,
                    "skipped_content_types": sorted(result.skipped_content_types),
                    "processed_at": datetime.now(tz=UTC).isoformat(),
                }
            newly_imported += 1
            if newly_imported % 25 == 0:
                logger.info("progress: %d newly imported, %d already done, %d failed (seen %d)",
                            newly_imported, already_done, failed_now, total_seen)
                if not args.dry_run:
                    save_state(STATE_PATH, state)
        except Exception as e:  # noqa: BLE001 - must never abort the whole batch
            failed_now += 1
            state["failed"][conv_id] = {
                "title": conv.get("title"),
                "shard": shard_name,
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(limit=5),
            }
            logger.warning("FAILED conversation %s (%s): %s", conv_id, conv.get("title"), e)

    if not args.dry_run:
        save_state(STATE_PATH, state)

    elapsed = time.time() - t0
    logger.info(
        "=== run done in %.1fs: seen=%d newly_imported=%d already_done=%d failed=%d ===",
        elapsed, total_seen, newly_imported, already_done, failed_now,
    )

    if not args.dry_run:
        write_overview(
            overview_path=OVERVIEW_PATH,
            state=state,
            total_seen=total_seen,
            zip_path=ZIP_PATH,
        )
        logger.info("overview note written: %s", OVERVIEW_PATH)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
