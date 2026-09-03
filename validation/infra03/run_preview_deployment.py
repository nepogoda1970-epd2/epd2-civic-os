#!/usr/bin/env python3
"""The canonical deterministic preview deployment runner (INFRA03 §32).

One command deploys, verifies, probes, and can safely destroy or reset the
preview environment::

    uv run python validation/infra03/run_preview_deployment.py deploy \
        --artifact <EPD2_INFRA02_..._CANDIDATE_0.1.zip> [--instance-base DIR]

    uv run python validation/infra03/run_preview_deployment.py destroy \
        --instance-dir DIR --environment preview --instance-id ID

Deploy verifies the baseline topology and the exact approved artifact
digest, provisions trust/secrets/PostgreSQL, starts the declared services,
waits for truthful readiness, runs the liveness/readiness/identity probes,
emits machine-readable evidence, and exits non-zero on any failure — a
failed deploy claims nothing and leaves a stopped, known state (§43).
Destroy/reset demand the explicit environment and instance identity and
refuse ambiguous or production-like targets (§47).

The full gate suite (G01..G42) is executed by
``uv run python -m scripts.infra03.gates --artifact <zip>``, which drives
this same deployment machinery — there is no second deployment
implementation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.infra03.supervisor import (  # noqa: E402
    PreviewInstance,
    Supervisor,
    new_instance,
    stale_state_check,
)
from scripts.infra03.topology import load_topology  # noqa: E402


def _emit(payload: dict[str, object], output: Path | None) -> None:
    text = json.dumps(payload, indent=1, sort_keys=True)
    if output is not None:
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


def cmd_deploy(args: argparse.Namespace) -> int:
    artifact = Path(args.artifact).resolve()
    base = (
        Path(args.instance_base).resolve()
        if args.instance_base
        else Path("/tmp/epd2-infra03-preview")
    )
    instance = new_instance(base)
    clean_findings = [f.describe() for f in stale_state_check(instance.instance_dir)]
    if clean_findings:
        _emit({"outcome": "REFUSED", "findings": clean_findings}, None)
        return 2
    supervisor = Supervisor(REPO_ROOT, instance)
    topology = load_topology(REPO_ROOT)
    started = datetime.now(tz=UTC).isoformat(timespec="seconds")
    evidence, findings = supervisor.deploy(topology, artifact)
    probes: dict[str, object] = {}
    if not findings:
        for name in sorted(supervisor.services):
            status, _payload = supervisor._probe_service(name, "/readyz")
            _, identity = supervisor._probe_service(name, "/identity")
            probes[name] = {
                "ready_status": status,
                "observed_app_digest": identity.get("observed_app_digest"),
            }
        drift = [f.describe() for f in supervisor.drift_scan()]
    else:
        drift = []
        supervisor.stop_all()
    outcome = {
        "schema": "epd2.infra03.preview-deploy-run/1",
        "started_at": started,
        "finished_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "instance_dir": str(instance.instance_dir),
        "instance_id": instance.instance_id,
        "environment": instance.environment,
        "steps": evidence.get("steps", []),
        "release_digest": evidence.get("release_digest"),
        "readiness_probes": probes,
        "drift_scan": drift,
        "findings": [f.describe() for f in findings],
        "outcome": "DEPLOYED_READY" if not findings and not drift else "FAILED_STOPPED",
        "disclaimer": "PREVIEW RUNTIME ONLY. NOT PRODUCTION. NOT AN ACCEPTANCE RESULT.",
    }
    _emit(outcome, Path(args.evidence_out) if args.evidence_out else None)
    if findings or drift:
        return 1
    if args.keep_running:
        print(
            f"preview instance {instance.instance_id} left running at "
            f"{instance.instance_dir} (destroy with the destroy command)",
            file=sys.stderr,
        )
        return 0
    supervisor.stop_all()
    return 0


def _bound_supervisor(args: argparse.Namespace) -> tuple[Supervisor, dict[str, str]]:
    instance_dir = Path(args.instance_dir).resolve()
    marker = json.loads((instance_dir / "instance.json").read_text(encoding="utf-8"))
    instance = PreviewInstance(instance_dir, environment=str(marker.get("environment")))
    instance.instance_id = str(marker.get("instance_id"))
    supervisor = Supervisor(REPO_ROOT, instance)
    return supervisor, marker


def cmd_destroy(args: argparse.Namespace) -> int:
    supervisor, _ = _bound_supervisor(args)
    findings = supervisor.verify_destroy_target(args.environment, args.instance_id)
    if findings:
        _emit({"outcome": "REFUSED", "findings": [f.describe() for f in findings]}, None)
        return 2
    import shutil

    supervisor.stop_all()
    shutil.rmtree(supervisor.instance.instance_dir, ignore_errors=True)
    _emit({"outcome": "DESTROYED", "instance_id": args.instance_id}, None)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_preview_deployment")
    sub = parser.add_subparsers(dest="command", required=True)

    deploy = sub.add_parser("deploy", help="deterministic preview deployment")
    deploy.add_argument("--artifact", required=True, help="exact accepted INFRA-02 candidate ZIP")
    deploy.add_argument("--instance-base", default=None)
    deploy.add_argument("--evidence-out", default=None)
    deploy.add_argument("--keep-running", action="store_true")
    deploy.set_defaults(func=cmd_deploy)

    destroy = sub.add_parser("destroy", help="destroy one preview instance (explicit identity)")
    destroy.add_argument("--instance-dir", required=True)
    destroy.add_argument("--environment", required=True)
    destroy.add_argument("--instance-id", required=True)
    destroy.set_defaults(func=cmd_destroy)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
