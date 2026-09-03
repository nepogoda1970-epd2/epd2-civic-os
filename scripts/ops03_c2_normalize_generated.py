from __future__ import annotations

import pathlib
import sys


def normalize_api06_binding(root: pathlib.Path) -> None:
    path = root / "packages/python/epd2-qualification/src/epd2_qualification/api06_binding.py"
    text = path.read_text(encoding="utf-8")

    old_sha = (
        '        raise RuntimeError(\n'
        '            f"accepted API-06 candidate SHA mismatch: {observed_sha} != {ACCEPTED_API06_CANDIDATE_SHA256}"\n'
        '        )\n'
    )
    new_sha = (
        '        raise RuntimeError(\n'
        '            "accepted API-06 candidate SHA mismatch: "\n'
        '            f"{observed_sha} != {ACCEPTED_API06_CANDIDATE_SHA256}"\n'
        '        )\n'
    )
    if old_sha not in text:
        raise RuntimeError("API-06 SHA mismatch normalization anchor not found")
    text = text.replace(old_sha, new_sha, 1)

    old_size = (
        '        raise RuntimeError(\n'
        '            f"accepted API-06 candidate size mismatch: {observed_size} != {ACCEPTED_API06_CANDIDATE_SIZE_BYTES}"\n'
        '        )\n'
    )
    new_size = (
        '        raise RuntimeError(\n'
        '            "accepted API-06 candidate size mismatch: "\n'
        '            f"{observed_size} != {ACCEPTED_API06_CANDIDATE_SIZE_BYTES}"\n'
        '        )\n'
    )
    if old_size not in text:
        raise RuntimeError("API-06 size mismatch normalization anchor not found")
    text = text.replace(old_size, new_size, 1)
    path.write_text(text, encoding="utf-8")


def normalize_validator(root: pathlib.Path) -> None:
    path = root / "scripts/validation/validate_ops03.py"
    text = path.read_text(encoding="utf-8")
    stale = "    ACCEPTED_API05_CANDIDATE_SHA256,\n"
    if stale not in text:
        raise RuntimeError("stale API-05 import normalization anchor not found")
    path.write_text(text.replace(stale, "", 1), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c2_normalize_generated.py ROOT")
    root = pathlib.Path(sys.argv[1]).resolve()
    normalize_api06_binding(root)
    normalize_validator(root)
    print("OPS03_C2_GENERATED_NORMALIZATION:PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
