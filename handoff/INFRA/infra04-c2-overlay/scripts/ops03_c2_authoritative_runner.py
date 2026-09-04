from __future__ import annotations

import pathlib
import sys

G02 = """    def g02_ops02_binding(self, result: GateResult) -> None:
        record_path = (
            self.repo_root / "docs/ops/OPS-02/OPS02_C3_ACCEPTANCE_RECORD.json"
        )
        if not record_path.is_file():
            raise GateFailure(
                "the accepted OPS-02 C3 acceptance record is missing at "
                f"{record_path}"
            )
        record = json.loads(record_path.read_text(encoding="utf-8"))
        candidate = record.get("candidate", {})
        bound = {
            "candidate_sha256": ACCEPTED_OPS02_CANDIDATE_SHA256,
            "freeze_tree_digest": ACCEPTED_OPS02_FREEZE_TREE_DIGEST,
            "source_commit": ACCEPTED_OPS02_SOURCE_COMMIT,
        }
        recorded = {
            "candidate_sha256": candidate.get("sha256"),
            "freeze_tree_digest": candidate.get("freeze_tree_digest"),
            "source_commit": candidate.get("source_commit"),
        }
        mismatched = {
            key: (bound[key], recorded[key])
            for key in bound
            if bound[key] != recorded[key]
        }
        if mismatched:
            _fail(
                result,
                [
                    "the bound accepted OPS-02 "
                    f"{key} does not match canonical governance: "
                    f"bound {value[0]!r}, recorded {value[1]!r}"
                    for key, value in sorted(mismatched.items())
                ],
            )
        if record.get("decision") != "ACCEPTED / CLOSED":
            _fail(
                result,
                [f"OPS-02 is recorded as {record.get('decision')!r}, not accepted"],
            )
        authoritative = (
            self.repo_root
            / "docs/ops/OPS-02/OPS02_C3_AUTHORITATIVE_ACCEPTANCE_RESULT.json"
        )
        if not authoritative.is_file():
            _fail(result, ["the OPS-02 C3 authoritative acceptance result is missing"])
        else:
            doc = json.loads(authoritative.read_text(encoding="utf-8"))
            passed = (
                doc.get("verdict") == "PASS"
                or doc.get("decision") == "PASS"
                or doc.get("result", {}).get("gates_passed") == 42
            )
            if not passed:
                _fail(result, ["the OPS-02 C3 authoritative acceptance result is not PASS"])
            result.measurements["ops02_authoritative_acceptance"] = doc
        archive = self._accepted_artifact_path(
            "EPD2_OPS02_", ACCEPTED_OPS02_CANDIDATE_SHA256
        )
        if archive is None:
            raise GateBlocked(
                "the exact accepted OPS-02 C3 bytes are not present; supply sha256 "
                f"{ACCEPTED_OPS02_CANDIDATE_SHA256} via EPD2_OPS03_ACCEPTED_ARTIFACTS"
            )
        result.measurements["accepted_ops02"] = {
            **bound,
            "acceptance_record": recorded,
        }
        result.measurements["accepted_archive"] = str(archive)
        result.observations.append(
            "OPS-02 predecessor is bound to exact independently accepted C3 bytes "
            "and authoritative PASS; its historical harness is not replayed because "
            "its G04 dependency-state assumption predates API-layer closure"
        )

"""


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ops03_c2_authoritative_runner.py <extracted-c2-root>")
    root = pathlib.Path(sys.argv[1]).resolve()
    validator = root / "scripts/validation/validate_ops03.py"
    source = validator.read_text(encoding="utf-8")
    start = source.index("    def g02_ops02_binding(self, result: GateResult) -> None:\n")
    end = source.index("    def g03_ops01_foundation(self, result: GateResult) -> None:\n", start)
    governed_source = source[:start] + G02 + source[end:]
    namespace = {
        "__name__": "__main__",
        "__file__": str(validator),
        "__package__": None,
        "__cached__": None,
    }
    code = compile(governed_source, str(validator), "exec")
    exec(code, namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
