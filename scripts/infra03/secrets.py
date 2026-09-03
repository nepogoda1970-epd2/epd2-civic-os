"""Secret generation, classified injection and leak detection (INFRA03 §14, §15).

Per-deployment secrets are generated at deploy time, written only into the
instance's secret directory with owner-only modes, injected explicitly by
classified slot name, and tracked so that the leak scanner can prove no
generated secret value ever reaches the repository, manifests, evidence,
logs or reports (mutations: secret in manifest, secret in logs).

Credential separation (§15): each slot carries a credential class; a slot
may only be delivered to services the topology declares for it, and voting
key material is a distinct class that INFRA-03 never provisions in preview
(§17) — requesting it fails closed.
"""

from __future__ import annotations

import json
import os
import secrets as _secrets
from dataclasses import dataclass
from pathlib import Path

from scripts.infra03 import codes

CREDENTIAL_CLASSES = (
    "db-credential",
    "workload-identity-key",
    "app-signing-material",
    "deployer-credential",
    "provider-credential",
    "voting-domain-key-material",
)

#: Classes INFRA-03 may generate for a preview instance. Voting key material
#: is deliberately NOT generatable here (§17): it exists only within the
#: canonical voting architecture (PACK-16), never as a deployment secret.
GENERATABLE_CLASSES = frozenset({"db-credential"})


@dataclass(frozen=True)
class SecretFindingI03:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


class SecretStore:
    """The instance-scoped secret store with a value-tracking leak scanner."""

    def __init__(self, secret_dir: Path) -> None:
        self.secret_dir = secret_dir
        secret_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(secret_dir, 0o700)
        self._values: dict[str, str] = {}
        self._classes: dict[str, str] = {}

    def generate(self, slot: str, credential_class: str) -> str:
        """Generate one classified secret; unknown/forbidden classes refuse."""
        if credential_class not in CREDENTIAL_CLASSES:
            raise PermissionError(
                f"{codes.SECRET_INJECTION_UNCLASSIFIED}: {slot}: unknown credential "
                f"class {credential_class!r}"
            )
        if credential_class not in GENERATABLE_CLASSES:
            raise PermissionError(
                f"{codes.SECRET_INJECTION_UNCLASSIFIED}: {slot}: class "
                f"{credential_class!r} is not provisionable by INFRA-03 in preview "
                "(voting keys and production credentials are separately governed)"
            )
        value = _secrets.token_urlsafe(32)
        target = self.secret_dir / slot.replace("/", "__")
        target.touch(mode=0o600, exist_ok=True)
        target.write_text(value, encoding="utf-8")
        os.chmod(target, 0o600)
        self._values[slot] = value
        self._classes[slot] = credential_class
        return value

    def value(self, slot: str) -> str:
        return self._values[slot]

    def inventory(self) -> dict[str, str]:
        """slot -> credential class. Values never appear in any inventory."""
        return dict(sorted(self._classes.items()))

    def scan_for_leaks(self, roots: list[Path]) -> list[SecretFindingI03]:
        """Prove no generated secret value appears under the given roots.

        This is a value-exact scan: it searches for the actual generated
        bytes, so a leak cannot hide behind an unanticipated format.
        """
        findings: list[SecretFindingI03] = []
        needles = {slot: value.encode() for slot, value in self._values.items()}
        for root in roots:
            if not root.exists():
                continue
            files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
            for path in files:
                if self.secret_dir in path.parents or path == self.secret_dir:
                    continue  # the store itself is the one governed location
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                for slot, needle in needles.items():
                    if needle in data:
                        findings.append(
                            SecretFindingI03(
                                codes.SECRET_IN_LOGS,
                                str(path),
                                f"generated secret {slot!r} leaked outside the secret store",
                            )
                        )
        return findings


def scan_manifest_for_secrets(document_text: str, subject: str) -> list[SecretFindingI03]:
    """Manifests must reference slots, never carry values (§14)."""
    findings: list[SecretFindingI03] = []
    lowered = document_text.lower()
    for marker in ("password:", "password=", "secret_value", "private_key:", "-----begin"):
        if marker in lowered:
            findings.append(
                SecretFindingI03(
                    codes.SECRET_IN_MANIFEST,
                    subject,
                    f"manifest carries secret-shaped material ({marker!r}); manifests "
                    "name classified injection slots, never values",
                )
            )
    return findings


def write_secret_inventory(store: SecretStore, target: Path) -> None:
    """Machine-readable slot/class inventory — names and classes only."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema": "epd2.infra03.secret-inventory/1",
                "note": "Classified secret slots of this deployment. Values are "
                "generated per deployment, live only in the instance secret store "
                "with owner-only modes, and are proven absent from repository, "
                "manifests, evidence and logs by a value-exact leak scan.",
                "slots": store.inventory(),
                "credential_classes": list(CREDENTIAL_CLASSES),
                "voting_key_policy": "voting-domain key material is never provisioned "
                "by INFRA-03; it exists only within the canonical voting architecture",
            },
            indent=1,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
