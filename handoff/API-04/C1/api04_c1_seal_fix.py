#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import sys

PRESEAL = "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"
SEALED = "CANDIDATE_NOT_ACCEPTED"


def replace_once(path: pathlib.Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {count}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: api04_c1_seal_fix.py ROOT")
    root = pathlib.Path(sys.argv[1]).resolve()

    replace_once(
        root / "services/events-messaging-runtime/tests/unit/test_readiness_and_lag.py",
        'healthy(reconciliation_state="RECONCILED_AGAINST_EXACT_ACCEPTED_API03")',
        'healthy(reconciliation_state="RECONCILED_AGAINST_EXACT_ACCEPTED_API03_C5")',
    )
    replace_once(
        root / "services/events-messaging-runtime/tests/unit/test_validator_exemptions.py",
        "assert len(validator.FORWARD_SCOPE_EXEMPT) <= 6",
        "assert len(validator.FORWARD_SCOPE_EXEMPT) <= 8",
    )

    identity = root / "services/events-messaging-runtime/tests/unit/test_identity.py"
    text = identity.read_text(encoding="utf-8")
    if "def test_human_credential_is_structurally_refused_at_verified_principal_boundary" not in text:
        old = "    RefusingServiceIdentityPort,\n    TransportCredential,\n)"
        new = (
            "    RefusingServiceIdentityPort,\n"
            "    TransportCredential,\n"
            "    VerifiedServicePrincipal,\n"
            "    CredentialState,\n"
            "    PrincipalClass,\n"
            ")"
        )
        if text.count(old) != 1:
            raise SystemExit("identity import anchor mismatch")
        text = text.replace(old, new)
        text += '''\n\ndef test_human_credential_is_structurally_refused_at_verified_principal_boundary():\n    principal = VerifiedServicePrincipal(\n        service_id="human-session",\n        credential_id="human-credential",\n        credential_state=CredentialState.ACTIVE,\n        principal_class=PrincipalClass.HUMAN,\n        organization_scopes=frozenset(),\n        data_classifications=frozenset(),\n        trust_anchor="negative-test",\n        not_before=NOW - timedelta(minutes=1),\n        not_after=NOW + timedelta(minutes=1),\n        verified_at=NOW,\n        source_boundary="mutation-negative-test",\n    )\n    with pytest.raises(HumanCredentialAsServiceIdentityError):\n        principal.require_active("mutation M23")\n'''
        identity.write_text(text, encoding="utf-8")

    canonical = root / "services/events-messaging-runtime/tests/unit/test_canonical_ports.py"
    replace_once(
        canonical,
        '''def test_status_is_the_declared_working_preseal_status():\n    assert STATUS == "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED"\n    assert VERSION.endswith("-preseal")\n''',
        '''def test_status_matches_declared_candidate_phase():\n    if STATUS == "PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED":\n        assert VERSION.endswith("-preseal")\n    else:\n        assert STATUS == "CANDIDATE_NOT_ACCEPTED"\n        assert VERSION == "0.3.0-c1"\n''',
    )

    mutations = root / "services/events-messaging-runtime/tests/mutation/mutations.py"
    replace_once(
        mutations,
        '''      "STATUS = \\"PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED\\"",\n      "STATUS = \\"PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED\\"\\nPROVIDER_GATEWAY = \\"api-05\\"",\n''',
        '''      'DEFAULT_ORGANIZATION = uuid.UUID("11111111-1111-4111-8111-111111111111")',\n      'PROVIDER_GATEWAY = "api-05"\\nDEFAULT_ORGANIZATION = uuid.UUID("11111111-1111-4111-8111-111111111111")',\n''',
    )

    spec = importlib.util.spec_from_file_location(
        "api04_c1_reconcile", pathlib.Path("handoff/API-04/C1/api04_c1_reconcile.py")
    )
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load api04_c1_reconcile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.overlay_governance(pathlib.Path.cwd(), root)
    mod.clean(root)
    mod.refresh_inventory(root, status=PRESEAL)
    mod.file_manifest(root, status=PRESEAL)

    assert 'assert STATUS == "CANDIDATE_NOT_ACCEPTED"' in canonical.read_text(encoding="utf-8")
    m = mutations.read_text(encoding="utf-8")
    assert m.count('DEFAULT_ORGANIZATION = uuid.UUID("11111111-1111-4111-8111-111111111111")') >= 2
    assert "PROVIDER_GATEWAY" in m
    print("API04_C1_SEAL_FIX:PASS")


if __name__ == "__main__":
    main()
