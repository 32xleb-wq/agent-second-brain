"""Sequential, memory-safe reader for the ChatGPT export zip.

The archive's central directory is missing/corrupted (the transfer to the
VPS was very likely interrupted — no PK\\x01\\x02 / PK\\x05\\x06 signature
exists anywhere in the last 10 MB of the file), so Python's stdlib
`zipfile` refuses to open it at all.

ZIP local file headers are self-describing (name, compression method, and
for this archive — verified on its first entry — a known compressed size
up front, general-purpose flag bit 3 *not* set). That means we can walk
the file entry by entry from byte 0, without ever needing the central
directory, and without ever holding more than one entry's data in memory
at a time. We stop cleanly the moment we hit something that isn't a valid
local file header — that boundary is exactly where the transfer broke.

This also happens to satisfy the "don't load the whole export into
memory" requirement for free.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

LOCAL_HEADER_SIG = b"PK\x03\x04"
CENTRAL_DIR_SIG = b"PK\x01\x02"
EOCD_SIG = b"PK\x05\x06"
DATA_DESCRIPTOR_SIG = b"PK\x07\x08"

_LOCAL_HEADER_STRUCT = struct.Struct("<HHHHHIIIHH")
# version, flags, method, mtime, mdate, crc32, csize, usize, fname_len, extra_len

_CHUNK = 1024 * 1024  # 1 MiB streaming buffer


@dataclass
class ZipEntry:
    name: str
    method: int
    flags: int
    csize: int | None  # None when only knowable via streaming decompression
    usize: int | None
    data_offset: int
    has_data_descriptor: bool


class TruncatedArchive(Exception):
    """Raised when the scanner runs off the end of readable local entries."""

    def __init__(self, message: str, entries_read: int, offset: int):
        super().__init__(message)
        self.entries_read = entries_read
        self.offset = offset


def _read_exact(f: BinaryIO, n: int) -> bytes:
    data = f.read(n)
    if len(data) != n:
        raise EOFError(f"expected {n} bytes, got {len(data)}")
    return data


def iter_entries(f: BinaryIO) -> Iterator[ZipEntry]:
    """Yield ZipEntry headers in file order. Does NOT read entry data —
    caller must consume/skip it (see stream_entry_data / skip_entry_data)
    before requesting the next entry."""
    while True:
        offset = f.tell()
        sig = f.read(4)
        if sig == CENTRAL_DIR_SIG or sig == EOCD_SIG or sig == b"":
            return  # clean end: central directory (or EOF) reached
        if sig != LOCAL_HEADER_SIG:
            raise TruncatedArchive(
                f"unexpected bytes at offset {offset} (not a local file header)",
                entries_read=-1,
                offset=offset,
            )
        fields = _LOCAL_HEADER_STRUCT.unpack(_read_exact(f, _LOCAL_HEADER_STRUCT.size))
        _version, flags, method, _mtime, _mdate, _crc32, csize, usize, fname_len, extra_len = fields
        name = _read_exact(f, fname_len).decode("utf-8", errors="replace")
        f.read(extra_len)  # extra field, unused
        has_descriptor = bool(flags & 0x08)
        yield ZipEntry(
            name=name,
            method=method,
            flags=flags,
            csize=None if has_descriptor or csize == 0xFFFFFFFF else csize,
            usize=None if has_descriptor or usize == 0xFFFFFFFF else usize,
            data_offset=f.tell(),
            has_data_descriptor=has_descriptor,
        )


def skip_entry_data(f: BinaryIO, entry: ZipEntry) -> None:
    """Advance the file pointer past this entry's data (+ data descriptor
    if present), without decompressing/storing anything."""
    for _ in stream_entry_data(f, entry):
        pass


def stream_entry_data(f: BinaryIO, entry: ZipEntry) -> Iterator[bytes]:
    """Yield decompressed chunks for one entry. Leaves the file positioned
    at the start of the next local header on completion."""
    if entry.method not in (0, 8):
        raise ValueError(f"unsupported compression method {entry.method} for {entry.name!r}")

    if entry.csize is not None:
        # Known size up front — the common, fast path for this archive.
        remaining = entry.csize
        decomp = zlib.decompressobj(-15) if entry.method == 8 else None
        while remaining > 0:
            chunk = f.read(min(_CHUNK, remaining))
            if not chunk:
                raise TruncatedArchive(
                    f"EOF mid-entry {entry.name!r} ({remaining} bytes still expected)",
                    entries_read=-1,
                    offset=f.tell(),
                )
            remaining -= len(chunk)
            yield decomp.decompress(chunk) if decomp else chunk
        if decomp:
            yield decomp.flush()
        return

    # Data-descriptor case (size unknown at header time): decompress until
    # the raw-deflate stream signals its own end, then consume the
    # descriptor that follows.
    if entry.method != 8:
        raise ValueError(f"stored entry with unknown size not supported: {entry.name!r}")
    decomp = zlib.decompressobj(-15)
    tail = b""
    while not decomp.eof:
        chunk = f.read(_CHUNK)
        if not chunk:
            raise TruncatedArchive(
                f"EOF before end-of-stream marker in {entry.name!r}",
                entries_read=-1,
                offset=f.tell(),
            )
        yield decomp.decompress(chunk)
        tail = decomp.unused_data
    # rewind to right after the compressed stream ends
    f.seek(f.tell() - len(tail))
    descriptor = _read_exact(f, 4)
    if descriptor == DATA_DESCRIPTOR_SIG:
        f.read(12)  # crc32, csize, usize (4 bytes each)
    else:
        f.read(8)  # descriptor without signature: crc32, csize, usize - 4 already read as csize's first bytes...
        # NB: without the signature the 4 bytes we just read as `descriptor`
        # are actually the crc32 field itself — nothing further to skip
        # beyond the remaining 8 bytes (csize, usize).


def extract_entry_to_file(f: BinaryIO, entry: ZipEntry, dest: Path) -> int:
    """Stream one entry's decompressed bytes straight to disk. Returns the
    number of bytes written. Never holds the full entry in memory."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(dest, "wb") as out:
        for chunk in stream_entry_data(f, entry):
            out.write(chunk)
            written += len(chunk)
    return written


def open_zip(path: Path) -> BinaryIO:
    return open(path, "rb")
