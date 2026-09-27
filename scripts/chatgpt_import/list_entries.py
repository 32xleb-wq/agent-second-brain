"""Quick pass: enumerate every entry in the export zip (name + sizes only,
no decompression of content) and report where the archive stops being
readable, if it does. Read-only — the source zip is never modified."""

import sys
from collections import Counter
from pathlib import Path

from zipscan import TruncatedArchive, iter_entries, open_zip, skip_entry_data

ZIP_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def main() -> None:
    if not ZIP_PATH:
        print("usage: list_entries.py <zip-path>")
        raise SystemExit(2)

    by_ext = Counter()
    by_ext_bytes = Counter()
    names: list[tuple[str, int | None]] = []
    count = 0
    truncated_at = None

    with open_zip(ZIP_PATH) as f:
        try:
            for entry in iter_entries(f):
                count += 1
                ext = entry.name.rsplit(".", 1)[-1].lower() if "." in entry.name else "(none)"
                by_ext[ext] += 1
                if entry.usize is not None:
                    by_ext_bytes[ext] += entry.usize
                names.append((entry.name, entry.usize))
                skip_entry_data(f, entry)
        except TruncatedArchive as e:
            truncated_at = (str(e), f.tell())

    print(f"entries read cleanly: {count}")
    if truncated_at:
        print(f"STOPPED: {truncated_at[0]} (file offset {truncated_at[1]})")
    else:
        print("reached central directory / EOF cleanly (no truncation detected)")

    print("\nby extension (count, total uncompressed bytes where known):")
    for ext, c in by_ext.most_common(30):
        print(f"  {ext:12s} {c:6d}  {by_ext_bytes[ext]:>14,d} bytes")

    print("\ntop-level json-ish files (likely text, not in a subfolder):")
    for name, usize in names:
        if "/" not in name and name.lower().endswith((".json", ".html", ".htm")):
            print(f"  {name:40s} {usize if usize is not None else '?':>14}")


if __name__ == "__main__":
    main()
