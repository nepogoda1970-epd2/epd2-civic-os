"""Trust material generation and delivery (INFRA03 §16, §23, §24).

Per-deployment ephemeral PKI: three separate certificate authorities —
``application-ca`` (east-west mTLS between non-voting services),
``data-ca`` (PostgreSQL server identity) and ``voting-ca`` (the voting
segment's own trust domain) — with per-service server and client
certificates carrying the workload identity in the subject CN and SANs.

Rules enforced here and verified by the gates:

- keys and certificates are generated at deploy time into the instance's
  trust directory with owner-only modes; nothing is ever committed to the
  repository or embedded in manifests (mutation: secret in manifest);
- there is no universal shared service certificate: every service gets its
  own key pair per role (server/client), and a certificate presented for a
  workload identity other than its own is refused
  (:data:`codes.WORKLOAD_IDENTITY_MISMATCH` /
  :data:`codes.UNIVERSAL_SERVICE_CERT`);
- wrong CA, expired and hostname-mismatched material fails closed
  (:data:`codes.UNTRUSTED_CA`, :data:`codes.TRUST_MATERIAL_INVALID`,
  :data:`codes.HOSTNAME_MISMATCH`);
- the voting CA is a separate trust domain: application-CA identities are
  not valid in the voting segment (§17, §20).

Production key custody, HSM/KMS and PKI lifecycle remain outside INFRA-03's
authority; this module provisions preview-instance trust only.
"""

from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from scripts.infra03 import codes

CA_NAMES = ("application-ca", "data-ca", "voting-ca")

_ONE_DAY = datetime.timedelta(days=1)


@dataclass(frozen=True)
class TrustFinding:
    code: str
    subject: str
    detail: str

    def describe(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def _write_private(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.write_bytes(data)
    os.chmod(path, 0o600)


def _key_pem(key: ec.EllipticCurvePrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _name(common_name: str) -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EPD2 preview instance"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )


class TrustAuthority:
    """One deployment-scoped CA that can issue workload certificates."""

    def __init__(self, name: str, directory: Path, validity_days: int = 7) -> None:
        self.name = name
        self.directory = directory
        self.validity_days = validity_days
        self._key = ec.generate_private_key(ec.SECP256R1())
        now = datetime.datetime.now(datetime.UTC)
        builder = (
            x509.CertificateBuilder()
            .subject_name(_name(f"epd2-preview {name}"))
            .issuer_name(_name(f"epd2-preview {name}"))
            .public_key(self._key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - _ONE_DAY)
            .not_valid_after(now + datetime.timedelta(days=validity_days))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        )
        self.certificate = builder.sign(self._key, hashes.SHA256())
        directory.mkdir(parents=True, exist_ok=True)
        self.cert_path = directory / f"{name}.crt"
        self.cert_path.write_bytes(self.certificate.public_bytes(serialization.Encoding.PEM))
        _write_private(directory / f"{name}.key", _key_pem(self._key))

    def issue(
        self,
        workload: str,
        usage: str,
        hostnames: tuple[str, ...] = ("localhost",),
        expired: bool = False,
    ) -> tuple[Path, Path]:
        """Issue one workload certificate (usage: 'server' or 'client').

        Returns (cert_path, key_path). ``expired`` exists only so the gate
        suite can prove that expired material is refused.
        """
        key = ec.generate_private_key(ec.SECP256R1())
        now = datetime.datetime.now(datetime.UTC)
        not_after = now - _ONE_DAY if expired else now + datetime.timedelta(days=self.validity_days)
        eku = (
            ExtendedKeyUsageOID.SERVER_AUTH
            if usage == "server"
            else ExtendedKeyUsageOID.CLIENT_AUTH
        )
        sans: list[x509.GeneralName] = [x509.DNSName(host) for host in hostnames]
        sans.append(x509.DNSName(workload))
        builder = (
            x509.CertificateBuilder()
            .subject_name(_name(workload))
            .issuer_name(self.certificate.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - _ONE_DAY)
            .not_valid_after(not_after)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([eku]), critical=False)
            .add_extension(x509.SubjectAlternativeName(sans), critical=False)
        )
        certificate = builder.sign(self._key, hashes.SHA256())
        cert_path = self.directory / f"{usage}-{workload}.crt"
        key_path = self.directory / f"{usage}-{workload}.key"
        cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        _write_private(key_path, _key_pem(key))
        return cert_path, key_path


def provision_trust(trust_dir: Path) -> dict[str, TrustAuthority]:
    """Create the three deployment CAs. Nothing here is ever committed."""
    return {name: TrustAuthority(name, trust_dir / name) for name in CA_NAMES}


def peer_workload_identity(certificate_der: bytes) -> str:
    """The workload identity a presented client certificate asserts (CN)."""
    certificate = x509.load_der_x509_certificate(certificate_der)
    attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(attrs[0].value) if attrs else ""


def verify_trust_layout(trust_dir: Path) -> list[TrustFinding]:
    """Fail-closed structural verification of provisioned trust material."""
    findings: list[TrustFinding] = []
    for ca_name in CA_NAMES:
        ca_cert = trust_dir / ca_name / f"{ca_name}.crt"
        if not ca_cert.is_file():
            findings.append(
                TrustFinding(codes.TRUST_MATERIAL_INVALID, ca_name, "CA certificate absent")
            )
            continue
        certificate = x509.load_pem_x509_certificate(ca_cert.read_bytes())
        now = datetime.datetime.now(datetime.UTC)
        if certificate.not_valid_after_utc < now:
            findings.append(TrustFinding(codes.TRUST_MATERIAL_INVALID, ca_name, "CA expired"))
        constraints = certificate.extensions.get_extension_for_class(x509.BasicConstraints).value
        if not constraints.ca:
            findings.append(
                TrustFinding(codes.TRUST_MATERIAL_INVALID, ca_name, "CA lacks the CA constraint")
            )
        for key_file in (trust_dir / ca_name).glob("*.key"):
            mode = key_file.stat().st_mode & 0o777
            if mode & 0o077:
                findings.append(
                    TrustFinding(
                        codes.TRUST_MATERIAL_INVALID,
                        str(key_file.name),
                        f"private key mode {oct(mode)} is not owner-only",
                    )
                )
    # No universal certificate: every service key pair must be distinct.
    seen: dict[bytes, str] = {}
    for cert_file in sorted(trust_dir.rglob("*.crt")):
        certificate = x509.load_pem_x509_certificate(cert_file.read_bytes())
        spki = certificate.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        if spki in seen:
            findings.append(
                TrustFinding(
                    codes.UNIVERSAL_SERVICE_CERT,
                    cert_file.name,
                    f"shares a key pair with {seen[spki]}; one certificate per workload "
                    "identity is mandatory",
                )
            )
        else:
            seen[spki] = cert_file.name
    return findings
