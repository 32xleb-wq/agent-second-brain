"""Phase 1/2 shared step: pull only the text-bearing JSON entries out of the
export zip onto local disk, streaming (never holding a whole entry in
memory). Attachments (*.dat) and the standalone chat.html viewer are
skipped entirely — we only need conversations-*.json.

Idempotent: if a target file already exists with the expected size, it is
left alone (safe to re-run after an interruption).
"""

import sys
from pathlib import Path

from zipscan import TruncatedArchive, extract_entry_to_file, iter_entries, open_zip, skip_entry_data

TEXT_ENTRY_PREFIXES = ("conversations-",)
TEXT_ENTRY_EXACT = {"ads.json"}  # tiny, harmless, kept for completeness of the record


def wanted(name: str) -> bool:
    if name in TEXT_ENTRY_EXACT:
        return True
    return any(name.startswith(p) and name.endswith(".json") for p in TEXT_ENTRY_PREFIXES)


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: extract_text.py <zip-path> <dest-dir>")
        raise SystemExit(2)
    zip_path = Path(sys.argv[1])
    dest_dir = Path(sys.argv[2])
    dest_dir.mkdir(parents=True, exist_ok=True)

    extracted = []
    try:
        with open_zip(zip_path) as f:
            for entry in iter_entries(f):
                if not wanted(entry.name):
                    skip_entry_data(f, entry)
                    continue
                dest = dest_dir / entry.name
                if dest.exists() and entry.usize is not None and dest.stat().st_size == entry.usize:
                    print(f"skip (already extracted): {entry.name}")
                    skip_entry_data(f, entry)
                    continue
                written = extract_entry_to_file(f, entry, dest)
                extracted.append((entry.name, written))
                print(f"extracted: {entry.name} -> {written:,} bytes")
    except TruncatedArchive as e:
        # Expected once we've collected every conversations-*.json: the
        # archive breaks off inside the (unwanted) attachment dump that
        # follows. Only a problem if we hadn't already found our files.
        print(f"(stopped skipping past attachments — archive ends there: {e})")

    print(f"\ndone. {len(extracted)} file(s) newly extracted into {dest_dir}")


if __name__ == "__main__":
    main()
