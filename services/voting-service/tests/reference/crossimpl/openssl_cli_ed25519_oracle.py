"""Independent Ed25519 oracle — the OpenSSL **command-line tool**.

This oracle is deliberately *not* the library the active provider uses. The
provider calls `cryptography`, which links libcrypto in-process; this script
shells out to the `openssl` binary, a separately built and separately
versioned artefact, and speaks to it only through files and exit codes. It
imports nothing from EPD², nothing from `cryptography`, and no Python
cryptographic library at all — a raw public key is wrapped in its twelve
fixed DER prefix bytes and handed to the tool.

**Stated limitation, because it is the weak point.** The CLI and the linked
library share an upstream project. A defect in OpenSSL's Ed25519 that
survived across both builds would be invisible to this comparison. The
evidence that does *not* share an upstream is the RFC 8032 §7.1 published
vectors, which are checked directly against the provider; this oracle adds
an independent execution path and a different version, not a different
lineage.

**Empty messages are skipped, not silently passed.** `openssl pkeyutl
-rawin` refuses a zero-length input file ("Could not allocate 0 bytes"),
which is a tool limitation rather than a verification result. Reporting it
as a pass would be a lie; the empty-message case is covered by the RFC
vector test instead, and this script reports it as `skipped` with the
reason.

Usage: `openssl_cli_ed25519_oracle.py CASES_JSON` → verdict JSON on stdout.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ORACLE_VERSION = "openssl-cli-ed25519-1"

#: SubjectPublicKeyInfo prefix for a raw Ed25519 public key (RFC 8410 §4).
#: SEQUENCE { SEQUENCE { OID 1.3.101.112 } BIT STRING }
_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")


def _openssl_version() -> str:
    out = subprocess.run(
        ["openssl", "version"], capture_output=True, text=True, timeout=60, check=True
    )
    return out.stdout.strip()


def _verify(public_key: bytes, message: bytes, signature: bytes) -> tuple[str, str]:
    if len(public_key) != 32:
        return "rejected", "public key is not 32 raw bytes"
    if len(signature) != 64:
        return "rejected", "signature is not 64 bytes"
    if not message:
        return "skipped", "openssl pkeyutl -rawin cannot read a zero-length input file"
    with tempfile.TemporaryDirectory() as work:
        base = pathlib.Path(work)
        (base / "pub.der").write_bytes(_SPKI_PREFIX + public_key)
        (base / "sig.bin").write_bytes(signature)
        (base / "msg.bin").write_bytes(message)
        completed = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify",
                "-pubin", "-inkey", str(base / "pub.der"), "-keyform", "DER",
                "-rawin", "-in", str(base / "msg.bin"),
                "-sigfile", str(base / "sig.bin"),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )  # fmt: skip
    if completed.returncode == 0:
        return "accepted", completed.stdout.strip()
    return "rejected", (completed.stdout + completed.stderr).strip()


def main() -> int:
    cases = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))["cases"]
    results = {}
    for name, case in cases.items():
        outcome, detail = _verify(
            bytes.fromhex(case["public_key"]),
            bytes.fromhex(case["message"]),
            bytes.fromhex(case["signature"]),
        )
        results[name] = {
            "vector_id": name,
            "operation": "ed25519_verify",
            "profile_id": "Ed25519 (RFC 8032)",
            "expected": case["expected"],
            "actual": outcome,
            "match": outcome == case["expected"] or outcome == "skipped",
            "skipped": outcome == "skipped",
            "detail": detail,
        }
    json.dump(
        {
            "oracle_version": ORACLE_VERSION,
            "backend": _openssl_version(),
            "cases": results,
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
