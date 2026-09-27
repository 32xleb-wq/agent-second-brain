"""Read-only access to the configured Obsidian vault for the dashboard.

Every function here reads straight from disk on each call — nothing is
cached or baked into source code. Parsing is deterministic (regex/markdown
only, no model calls). Values the source text leaves unclear are surfaced
as "не указано" (missing) or "требует уточнения" (present but ambiguous),
per the same convention already used in finances/defi-log.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import yaml

from d_brain.config import get_settings

NOT_SPECIFIED = "не указано"
NEEDS_CLARIFICATION = "требует уточнения"

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_BULLET_RE = re.compile(r"^\s*-\s+(.*\S)\s*$")
_CHECKBOX_RE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.*\S)\s*$")
_PLACEHOLDER_RE = re.compile(r"^(Task|Metric)\s*\d+$", re.IGNORECASE)
# number (with optional thousands spaces) + an alphabetic unit right after it,
# e.g. "4 766 USDT" or "12 монет" — deliberately excludes bare "%" and single
# letter leverage markers like "6x" (unit must be 2+ letters) so we don't
# mislabel an APY or a leverage multiplier as an amount.
_AMOUNT_RE = re.compile(r"(~?\d[\d\s]{0,9}\d|\d)\s?([A-Za-zА-Яа-яЁё]{2,10})")


def vault_root() -> Path:
    return get_settings().vault_path


class VaultPathError(ValueError):
    pass


def safe_vault_path(rel_path: str) -> Path:
    """Resolve rel_path inside the vault, rejecting escapes and dotfiles/dirs."""
    root = vault_root().resolve()
    if not rel_path or rel_path.startswith("/") or "\x00" in rel_path:
        raise VaultPathError("invalid path")
    parts = Path(rel_path).parts
    if any(p in ("..", ".") or p.startswith(".") for p in parts):
        raise VaultPathError("path not allowed")
    target = (root / rel_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise VaultPathError("path escapes vault") from exc
    if not target.is_file():
        raise VaultPathError("not found")
    return target


def note_href(rel_path: str, back: str) -> str:
    return f"/obsidian/note?path={quote(rel_path)}&back={quote(back)}"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm_text = text[4:end]
            body_start = text.find("\n", end + 1)
            body = text[body_start + 1 :] if body_start != -1 else ""
            try:
                fm = yaml.safe_load(fm_text) or {}
            except yaml.YAMLError:
                fm = {}
            if not isinstance(fm, dict):
                fm = {}
            return fm, body
    return {}, text


# ── generic markdown structure parsing ─────────────────────────────────


def parse_checkboxes(text: str) -> list[dict]:
    """Extract '- [ ]'/'- [x]' items with their nearest H2/H3 heading."""
    h2 = h3 = None
    items = []
    for idx, line in enumerate(text.splitlines()):
        hm = _HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            heading_text = hm.group(2).strip()
            if level <= 2:
                h2, h3 = heading_text, None
            elif level == 3:
                h3 = heading_text
            continue
        cm = _CHECKBOX_RE.match(line)
        if cm:
            items.append(
                {
                    "done": cm.group(1).lower() == "x",
                    "text": cm.group(2).strip(),
                    "h2": h2,
                    "h3": h3,
                    "line": idx + 1,
                }
            )
    return items


def parse_sections(text: str) -> list[dict]:
    """Single pass: pull out markdown tables, dated bullet groups, and
    plain bullet groups, each tagged with the nearest preceding heading."""
    lines = text.splitlines()
    n = len(lines)
    blocks: list[dict] = []
    current_heading: str | None = None
    i = 0
    while i < n:
        line = lines[i]
        hm = _HEADING_RE.match(line)
        if hm:
            current_heading = hm.group(2).strip()
            i += 1
            continue

        if _TABLE_ROW_RE.match(line) and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]):
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            j = i + 2
            rows = []
            while j < n and _TABLE_ROW_RE.match(lines[j]):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            blocks.append(
                {"type": "table", "title": current_heading, "headers": headers, "rows": rows}
            )
            i = j
            continue

        if current_heading and _DATE_ONLY_RE.match(current_heading):
            date = current_heading
            items = []
            j = i
            while j < n and not _HEADING_RE.match(lines[j]):
                bm = _BULLET_RE.match(lines[j])
                if bm:
                    items.append({"text": bm.group(1).strip(), "line": j + 1})
                j += 1
            if items:
                blocks.append({"type": "journal_day", "date": date, "items": items})
            i = j
            current_heading = None
            continue

        bm = _BULLET_RE.match(line)
        if bm:
            items = []
            j = i
            while j < n:
                bm2 = _BULLET_RE.match(lines[j])
                if not bm2:
                    break
                items.append({"text": bm2.group(1).strip(), "line": j + 1})
                j += 1
            blocks.append({"type": "bullets", "title": current_heading, "items": items})
            i = j
            continue

        i += 1
    return blocks


def _is_placeholder_row(headers: list[str], row: list[str]) -> bool:
    body_cells = row[:-1] if len(row) > 1 else row
    return all(c in ("—", "-", "") for c in body_cells)


def _best_effort_action(text: str) -> str:
    for sep in (" — ", ", ", ". "):
        if sep in text:
            head = text.split(sep, 1)[0].strip()
            if 3 <= len(head) <= 60:
                return head
    return NEEDS_CLARIFICATION


def _best_effort_amount(text: str) -> str:
    for m in _AMOUNT_RE.finditer(text):
        unit = m.group(2).lower()
        if unit in ("x", "х"):
            continue
        value = m.group(0).strip()
        start = m.start()
        if start > 0 and text[start - 1] == "~":
            value = "~" + value
        return value
    return NOT_SPECIFIED


# ── section data classes ────────────────────────────────────────────────


@dataclass
class ReadResult:
    label: str
    source_path: str
    exists: bool = True
    error: str | None = None
    data: object = field(default=None)


# ── Tasks ────────────────────────────────────────────────────────────────

_WEEKLY_PRIORITY = {
    "Must Do (Non-negotiable)": "Обязательно",
    "Should Do (Important)": "Важно",
    "Could Do (If time permits)": "Если будет время",
}


def _tasks_from_file(rel_path: str, label: str) -> ReadResult:
    path = vault_root() / rel_path
    if not path.exists():
        return ReadResult(label=label, source_path=rel_path, exists=False)
    try:
        _, body = split_frontmatter(_read_text(path))
        raw_items = parse_checkboxes(body)
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
        return ReadResult(label=label, source_path=rel_path, error=str(exc))

    tasks = []
    for it in raw_items:
        text = it["text"]
        if _PLACEHOLDER_RE.match(text.strip()):
            continue
        due_match = _ISO_DATE_RE.search(text)
        due = due_match.group(0) if due_match else None
        priority = _WEEKLY_PRIORITY.get(it["h3"] or "")
        if priority is None and it["h3"] and it["h3"].lower().startswith("priority"):
            priority = it["h3"]
        context = " → ".join(p for p in (it["h2"], it["h3"]) if p)
        tasks.append(
            {
                "text": text,
                "done": it["done"],
                "priority": priority or "не указан",
                "due": due or "не указан",
                "context": context or "—",
                "source_path": rel_path,
                "source_label": label,
                "note_href": note_href(rel_path, "/tasks"),
                "line": it["line"],
            }
        )
    return ReadResult(label=label, source_path=rel_path, data=tasks)


def get_tasks() -> dict:
    results = [
        _tasks_from_file("goals/3-weekly.md", "Неделя"),
        _tasks_from_file("goals/2-monthly.md", "Месяц"),
    ]
    all_tasks = []
    errors = []
    missing = []
    for r in results:
        if r.error:
            errors.append({"label": r.label, "source_path": r.source_path, "error": r.error})
        elif not r.exists:
            missing.append({"label": r.label, "source_path": r.source_path})
        else:
            all_tasks.extend(r.data)
    open_tasks = [t for t in all_tasks if not t["done"]]
    done_tasks = [t for t in all_tasks if t["done"]]
    return {"open": open_tasks, "done": done_tasks, "errors": errors, "missing": missing}


# ── DeFi ─────────────────────────────────────────────────────────────────


def get_defi() -> dict:
    rel_path = "finances/defi-log.md"
    path = vault_root() / rel_path
    if not path.exists():
        return {"exists": False, "source_path": rel_path, "error": None}
    try:
        _, body = split_frontmatter(_read_text(path))
        blocks = parse_sections(body)
    except Exception as exc:  # noqa: BLE001
        return {"exists": True, "source_path": rel_path, "error": str(exc)}

    tables = []
    journal_rows = []
    bullet_sections = []

    for b in blocks:
        if b["type"] == "table":
            rows = b["rows"]
            is_empty = len(rows) == 0 or (len(rows) == 1 and _is_placeholder_row(b["headers"], rows[0]))
            tables.append(
                {
                    "title": b["title"] or "Таблица",
                    "headers": b["headers"],
                    "rows": [] if is_empty else rows,
                    "empty": is_empty,
                    "empty_note": rows[0][-1] if is_empty and rows else None,
                }
            )
        elif b["type"] == "journal_day":
            for item in b["items"]:
                text = item["text"]
                journal_rows.append(
                    {
                        "date": b["date"],
                        "action": _best_effort_action(text),
                        "platform": NEEDS_CLARIFICATION,
                        "asset": NEEDS_CLARIFICATION,
                        "amount": _best_effort_amount(text),
                        "note": text,
                        "source_path": rel_path,
                        "note_href": note_href(rel_path, "/defi"),
                        "line": item["line"],
                    }
                )
        elif b["type"] == "bullets":
            bullet_sections.append(
                {
                    "title": b["title"] or "Заметки",
                    # NB: key is "entries", not "items" — a dict has a
                    # built-in .items() method, so Jinja's `bs.items` would
                    # resolve to that method instead of this list.
                    "entries": [i["text"] for i in b["items"]],
                }
            )

    journal_rows.sort(key=lambda r: r["date"], reverse=True)

    return {
        "exists": True,
        "source_path": rel_path,
        "error": None,
        "tables": tables,
        "journal_rows": journal_rows,
        "bullet_sections": bullet_sections,
        "note_href": note_href(rel_path, "/defi"),
    }


# ── Content ──────────────────────────────────────────────────────────────


def _content_from_markdown_dir(rel_dir: str, item_type: str) -> ReadResult:
    dir_path = vault_root() / rel_dir
    if not dir_path.exists():
        return ReadResult(label=item_type, source_path=rel_dir, exists=False)
    try:
        items = []
        for f in sorted(dir_path.glob("*.md")):
            fm, _ = split_frontmatter(_read_text(f))
            rel_path = f"{rel_dir}/{f.name}"
            items.append(
                {
                    "type": item_type,
                    "title": fm.get("title") or f.stem,
                    "excerpt": fm.get("excerpt") or fm.get("description") or "",
                    "date": str(fm.get("publishedAt") or fm.get("updated") or ""),
                    "tags": fm.get("tags") or [],
                    "source_path": rel_path,
                    "note_href": note_href(rel_path, "/content"),
                    "mtime": f.stat().st_mtime,
                }
            )
        return ReadResult(label=item_type, source_path=rel_dir, data=items)
    except Exception as exc:  # noqa: BLE001
        return ReadResult(label=item_type, source_path=rel_dir, error=str(exc))


def _content_from_canvas_dir(rel_dir: str) -> ReadResult:
    import json

    dir_path = vault_root() / rel_dir
    if not dir_path.exists():
        return ReadResult(label="Идея (майнд-карта)", source_path=rel_dir, exists=False)
    try:
        items = []
        for f in sorted(dir_path.glob("*.canvas")):
            try:
                data = json.loads(_read_text(f))
                node_count = len(data.get("nodes", []))
            except (json.JSONDecodeError, OSError):
                node_count = None
            rel_path = f"{rel_dir}/{f.name}"
            items.append(
                {
                    "type": "Идея (майнд-карта)",
                    "title": f.stem.replace("-", " "),
                    "excerpt": f"{node_count} узлов" if node_count is not None else "",
                    "date": "",
                    "tags": [],
                    "source_path": rel_path,
                    "note_href": note_href(rel_path, "/content"),
                    "mtime": f.stat().st_mtime,
                }
            )
        return ReadResult(label="Идея (майнд-карта)", source_path=rel_dir, data=items)
    except Exception as exc:  # noqa: BLE001
        return ReadResult(label="Идея (майнд-карта)", source_path=rel_dir, error=str(exc))


def get_content() -> dict:
    sources = [
        _content_from_markdown_dir("blog", "Статья"),
        _content_from_markdown_dir("thoughts/ideas", "Идея"),
        _content_from_canvas_dir("canvases"),
    ]
    groups = []
    for r in sources:
        groups.append(
            {
                "label": r.label,
                "source_path": r.source_path,
                "exists": r.exists,
                "error": r.error,
                # NB: "notes", not "items" — see the bullet_sections comment above.
                "notes": sorted(r.data or [], key=lambda x: x.get("mtime", 0), reverse=True),
            }
        )
    return {"groups": groups}


# ── Obsidian overview ────────────────────────────────────────────────────


def _is_hidden(rel_parts: tuple[str, ...]) -> bool:
    return any(p.startswith(".") for p in rel_parts)


def get_obsidian_overview() -> dict:
    root = vault_root()
    if not root.exists():
        return {"exists": False, "error": None}
    try:
        folders: dict[str, int] = {}
        all_notes: list[tuple[Path, float]] = []
        for path in root.rglob("*.md"):
            rel = path.relative_to(root)
            if _is_hidden(rel.parts):
                continue
            top = rel.parts[0] if len(rel.parts) > 1 else "(корень)"
            folders[top] = folders.get(top, 0) + 1
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            all_notes.append((rel, mtime))

        all_notes.sort(key=lambda x: x[1], reverse=True)
        recent = [
            {
                "rel_path": str(rel),
                "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                "note_href": note_href(str(rel), "/obsidian"),
            }
            for rel, mtime in all_notes[:12]
        ]
        return {
            "exists": True,
            "error": None,
            "total_notes": len(all_notes),
            "folders": sorted(folders.items(), key=lambda kv: kv[0]),
            "recent": recent,
        }
    except Exception as exc:  # noqa: BLE001
        return {"exists": True, "error": str(exc)}


# ── Note reader (shared by Content + Obsidian) ──────────────────────────


def read_note(rel_path: str) -> dict:
    path = safe_vault_path(rel_path)
    if path.suffix == ".canvas":
        import json

        raw = _read_text(path)
        try:
            data = json.loads(raw)
            texts = [
                n.get("text", "")
                for n in data.get("nodes", [])
                if n.get("type") == "text" and n.get("text")
            ]
            return {"kind": "canvas", "title": path.stem, "texts": texts}
        except json.JSONDecodeError as exc:
            return {"kind": "canvas", "title": path.stem, "error": str(exc)}

    if path.suffix != ".md":
        raise VaultPathError("unsupported file type")

    import markdown as md

    fm, body = split_frontmatter(_read_text(path))
    html = md.markdown(body, extensions=["tables", "fenced_code", "sane_lists"])
    title = fm.get("title") or path.stem
    return {"kind": "markdown", "title": title, "frontmatter": fm, "html": html}


# ── Home summary ─────────────────────────────────────────────────────────


def get_home_summary() -> dict:
    tasks = get_tasks()
    defi = get_defi()
    content = get_content()

    latest_defi = list(defi.get("journal_rows") or [])[:3]
    latest_content = []
    for g in content["groups"]:
        latest_content.extend(g["notes"])
    latest_content.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    latest_content = latest_content[:3]

    return {
        "open_tasks": tasks["open"][:6],
        "open_tasks_total": len(tasks["open"]),
        "tasks_errors": tasks["errors"],
        "defi_rows": latest_defi,
        "defi_error": defi.get("error"),
        "defi_exists": defi.get("exists", True),
        "content_items": latest_content,
    }
