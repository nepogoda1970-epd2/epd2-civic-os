#!/usr/bin/env python3
"""Apply an EPD2 zsp2 sparse exact-byte ZIP patch.

Temporary verification transport only.  The patch is accepted only when both
its base SHA-256 and reconstructed target SHA-256 match the values sealed in
the patch itself.  It does not unzip or repack the governed candidate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply(base_path: Path, patch_path: Path, output_path: Path) -> None:
    base = base_path.read_bytes()
    with zipfile.ZipFile(patch_path) as archive:
        meta = json.loads(archive.read("m"))
        ranges = zlib.decompress(archive.read("r"))
        skeleton = zlib.decompress(archive.read("s"))

    if meta.get("f") != "epd2.zsp2":
        raise SystemExit("unsupported sparse patch format")
    if sha256(base) != meta["b"] or len(base) != meta["bs"]:
        raise SystemExit("base archive identity mismatch")
    if sha256(skeleton) != meta["s"] or len(skeleton) != meta["ts"]:
        raise SystemExit("patch skeleton integrity mismatch")
    if len(ranges) != meta["n"] * 24:
        raise SystemExit("patch copy-range table malformed")

    result = bytearray(skeleton)
    for index in range(meta["n"]):
        target_offset, base_offset, length = struct.unpack_from("<QQQ", ranges, index * 24)
        result[target_offset : target_offset + length] = base[base_offset : base_offset + length]

    digest = sha256(result)
    if digest != meta["t"]:
        raise SystemExit(f"reconstructed target SHA-256 mismatch: {digest}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result)
    print(f"{digest}  {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: tmp_apply_zip_sparse_patch.py BASE.zsp-source PATCH.zsp OUTPUT.zip")
    apply(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
