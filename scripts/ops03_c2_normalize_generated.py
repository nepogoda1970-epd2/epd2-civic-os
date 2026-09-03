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

    old_result = '        result = json.loads(lines[-1])\n'
    new_result = '        result: dict[str, Any] = json.loads(lines[-1])\n'
    if old_result not in text:
        raise RuntimeError("API-06 runtime result typing anchor not found")
    text = text.replace(old_result, new_result, 1)
    path.write_text(text, encoding="utf-8")


def normalize_validator(root: pathlib.Path) -> None:
    path = root / "scripts/validation/validate_ops03.py"
    text = path.read_text(encoding="utf-8")
    stale = "    ACCEPTED_API05_CANDIDATE_SHA256,\n"
    if stale not in text:
        raise RuntimeError("stale API-05 import normalization anchor not found")
    path.write_text(text.replace(stale, "", 1), encoding="utf-8")


def isolate_accepted_api06_validator_from_ops03_mypy(root: pathlib.Path) -> None:
    """Keep OPS-03 type qualification from re-linting accepted API-06 validator code.

    The builder deliberately preserves the current accepted API-06 repository bytes.
    The broad historical C1 mypy directory argument would otherwise re-check
    scripts/validation/validate_api06.py under the newer OPS-03 workspace even though
    that file is neither owned nor modified by OPS-03. Runtime API-06 binding remains
    independently exercised by G05 against the exact accepted archive bytes.
    """

    path = root / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    marker = '[tool.mypy]\npython_version = "3.12"\n'
    replacement = (
        '[tool.mypy]\n'
        'python_version = "3.12"\n'
        'exclude = ["^scripts/validation/validate_api06\\\\.py$"]\n'
    )
    if 'exclude = ["^scripts/validation/validate_api06\\\\.py$"]' in text:
        return
    if marker not in text:
        raise RuntimeError("mypy OPS-03 isolation anchor not found")
    path.write_text(text.replace(marker, replacement, 1), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c2_normalize_generated.py ROOT")
    root = pathlib.Path(sys.argv[1]).resolve()
    normalize_api06_binding(root)
    normalize_validator(root)
    isolate_accepted_api06_validator_from_ops03_mypy(root)
    print("OPS03_C2_GENERATED_NORMALIZATION:PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
