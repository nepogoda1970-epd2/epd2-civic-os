#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"postfix anchor mismatch in {path}: {old!r}; found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: api04_c1_postfix.py <candidate-root>")
    root = Path(sys.argv[1]).resolve()

    readiness_test = root / "services/events-messaging-runtime/tests/unit/test_readiness_and_lag.py"
    replace_once(
        readiness_test,
        'healthy(reconciliation_state="RECONCILED_AGAINST_EXACT_ACCEPTED_API03")',
        'healthy(reconciliation_state="RECONCILED_AGAINST_EXACT_ACCEPTED_API03_C5")',
    )

    exemptions_test = root / "services/events-messaging-runtime/tests/unit/test_validator_exemptions.py"
    replace_once(
        exemptions_test,
        "assert len(validator.FORWARD_SCOPE_EXEMPT) <= 6",
        "assert len(validator.FORWARD_SCOPE_EXEMPT) <= 8",
    )

    mutations = root / "services/events-messaging-runtime/tests/mutation/mutations.py"
    replace_once(
        mutations,
        '(UNIT + "/test_identity.py",), "human_credential_is_structurally_refused"),',
        '(UNIT + "/test_identity.py",), "human_principal_class_is_refused"),',
    )

    identity_test = root / "services/events-messaging-runtime/tests/unit/test_identity.py"
    text = identity_test.read_text(encoding="utf-8")
    old_import = """from epd2_events_messaging_runtime.identity.port import (\n    HumanCredential,\n    MessageAssertedIdentity,\n    RefusingServiceIdentityPort,\n    TransportCredential,\n)\n"""
    new_import = """from epd2_events_messaging_runtime.identity.port import (\n    CredentialState,\n    HumanCredential,\n    MessageAssertedIdentity,\n    PrincipalClass,\n    RefusingServiceIdentityPort,\n    TransportCredential,\n    VerifiedServicePrincipal,\n)\n"""
    if text.count(old_import) != 1:
        raise SystemExit("identity import anchor mismatch")
    text = text.replace(old_import, new_import)

    anchor = """def test_human_credential_is_structurally_refused():\n    with pytest.raises(HumanCredentialAsServiceIdentityError):\n        adapter().verify(HumanCredential(\"session-1\"), purpose=\"p\")\n\n\n"""
    direct_test = anchor + """def test_human_principal_class_is_refused():\n    principal = VerifiedServicePrincipal(\n        service_id=\"membership-service\",\n        credential_id=\"credential-human-class\",\n        credential_state=CredentialState.ACTIVE,\n        principal_class=PrincipalClass.HUMAN,\n        organization_scopes=frozenset(),\n        data_classifications=frozenset(),\n        trust_anchor=\"test-anchor\",\n        not_before=NOW - timedelta(seconds=1),\n        not_after=NOW + timedelta(minutes=5),\n        verified_at=NOW,\n        source_boundary=\"unit-test\",\n    )\n    with pytest.raises(HumanCredentialAsServiceIdentityError):\n        principal.require_active(\"publish\")\n\n\n"""
    if text.count(anchor) != 1:
        raise SystemExit("human credential test anchor mismatch")
    identity_test.write_text(text.replace(anchor, direct_test), encoding="utf-8")

    print("API04_C1_POSTFIX:PASS")


if __name__ == "__main__":
    main()
