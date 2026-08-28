from __future__ import annotations

from pathlib import Path
import hashlib
import json
import textwrap

ROOT = Path('.')
MASTER = ROOT / 'docs/roadmap/EPD2_MASTER_FUTURE_IMPLEMENTATION_REGISTER.md'
CONTROL = ROOT / 'docs/roadmap/EPD2_PROGRAM_CONTROL_REGISTER.md'
PROFILE_MD = ROOT / 'docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.md'
PROFILE_JSON = ROOT / 'docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json'

master = MASTER.read_text(encoding='utf-8')
control = CONTROL.read_text(encoding='utf-8')

assert 'FIR-TRUST-003' not in master, 'FIR-TRUST-003 already exists'
assert '**V22**' in control, 'expected V22 control baseline'
assert 'API-02 = ACTIVE / IN DEVELOPMENT' in control
assert 'API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED' in control

profile_md = r'''# EPD² Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility 0.1

**Status:** governed target profile supporting `FIR-TRUST-003`; not implemented, not production activated  
**Date:** 2026-08-28  
**Scope:** generic EPD² platform cryptography, identity/runtime assertions, workload identity, regional trust, audit/evidence signing and data-key classes.  
**Exclusion:** the isolated voting trust domain keeps its PACK-16 cryptographic profile and trustee/key-ceremony rules; this document does not replace them.

## 1. Why this profile exists

V20-V22 established who may request, approve, generate, hold, rotate, revoke and recover credentials and keys, and how central trust may delegate bounded regional trust. V23 now fixes the **cryptographic contract** those controls operate against before API-02/API-03 are sealed and before INFRA selects a concrete HSM/KMS/PKI provider.

Core rule:

```text
key class -> one purpose family -> one approved algorithm profile -> one custody profile
```

Possession of a private key never creates political or organizational competence. `OrganizationalAuthority` remains authoritative and every runtime assertion is only a bounded derivative.

## 2. Standards baseline and revalidation rule

The profile is designed against the current project reference set as of 2026-08-28:

- BSI TR-02102-1, Version 2025-01 — cryptographic mechanisms and key lengths;
- BSI TR-02102-2, Version 2025-1 — TLS usage recommendations;
- RFC 7518 — JSON Web Algorithms;
- RFC 7638 — JWK Thumbprints;
- RFC 8725 / BCP 225 — JWT Best Current Practices;
- W3C Web Authentication Level 3;
- NIST FIPS 186-5 — RSA/ECDSA/EdDSA digital signatures;
- NIST FIPS 203 — ML-KEM;
- NIST FIPS 204 — ML-DSA.

Production activation MUST re-check the then-current BSI guidance, browser/authenticator interoperability, provider certifications and relevant legal/eIDAS requirements. A newer rule may **tighten** this profile without weakening an already-required control; incompatible algorithm changes require a governed profile revision and migration evidence.

## 3. Algorithm status model

Every algorithm in an implementation registry has one status per use class:

```text
MANDATORY_BASELINE
ALLOWED_SCOPED
COMPATIBILITY_ONLY
MIGRATION_CANDIDATE
PROHIBITED
```

A verifier uses an explicit allow-list for the exact artifact class. It MUST NOT infer acceptable algorithms from the token/key alone.

Each key is bound to exactly one signing/encryption algorithm and one key-use family. Algorithm confusion and cross-protocol key reuse are prohibited.

## 4. Platform baseline algorithms

### 4.1 Hashes

- `SHA-256` — mandatory baseline for ordinary digests, JWK thumbprints, runtime identifiers and P-256 profiles.
- `SHA-384` — mandatory baseline for P-384/high-impact trust and audit-signing profiles.
- `SHA-512` — allowed only where an owning approved protocol explicitly requires it.
- `SHA-1` and `MD5` — prohibited for new signatures, integrity protection, key derivation or security decisions.

### 4.2 Symmetric encryption and KDF

- `AES-256-GCM` — mandatory baseline for new application/envelope data encryption where EPD² owns the cipher choice.
- Nonce reuse under one AES-GCM key is prohibited. Nonces are generated/allocated by the accepted cryptographic provider/runtime and are never manually recycled.
- `HKDF-SHA-256` / `HKDF-SHA-384` — mandatory derivation profiles where an owning protocol requires HKDF.
- KEK wrapping uses an HSM/KMS provider-native authenticated wrapping mechanism or a separately approved standards-based wrapping profile; `AES-KWP` is the preferred portable profile where provider support and interoperability require a portable representation.
- ECB, DES, 3DES, RC4 and unauthenticated application CBC encryption are prohibited for new EPD² cryptographic protection.

### 4.3 Signatures

- `ES256` = ECDSA P-256 + SHA-256 — mandatory baseline for short-lived JOSE runtime assertions and ordinary service assertions.
- `ES384` = ECDSA P-384 + SHA-384 — mandatory baseline for generic EPD² root/intermediate/regional trust signing and high-impact audit/evidence signing.
- `Ed25519` / `EdDSA` — allowed only for an explicitly governed scoped profile, including existing voting-domain lineage and compatible WebAuthn authenticators; it is not the default generic platform issuer algorithm.
- `PS256` / `PS384` — compatibility-only for an external integration that cannot use the baseline ECDSA profile and only after explicit approval.
- `RS256` and other PKCS#1 v1.5 signature profiles — verify-only/compatibility-only where unavoidable for an external legacy trust chain; no new generic EPD² issuer key is generated for them.
- DSA — prohibited for new signing.
- JOSE `alg=none` — prohibited in all EPD² authorization/service/security assertions.
- `HS256/HS384/HS512` — prohibited for generic cross-service or organizational authorization assertions because shared verifier secrets collapse issuer/verifier separation. HMAC may still be used as a protocol-internal MAC where an owning approved protocol explicitly requires it.

ECDSA signing must use a vetted library/provider/HSM. Application code must never construct ECDSA nonce arithmetic itself. Deterministic ECDSA according to RFC 6979 is preferred where the provider exposes it; otherwise the accepted provider/HSM must supply a validated unique-nonce implementation.

### 4.4 Post-quantum migration candidates

The generic platform MUST be crypto-agile for post-quantum migration but MUST NOT activate a PQ algorithm merely because this profile names it.

Initial migration candidates:

- `ML-KEM-768` — key-establishment migration candidate;
- `ML-DSA-65` — signature migration candidate.

Their status is `MIGRATION_CANDIDATE`, not production default. Hybrid or pure-PQ activation requires a later governed profile specifying wire formats, certificate/token representation, interoperability, downgrade resistance, key sizes, HSM/provider support, BSI assessment and integrated migration tests.

## 5. Canonical key classes

| Key class | Purpose | Baseline algorithm / format | Private-key boundary | Public / verification representation | Initial cryptoperiod rule |
| --- | --- | --- | --- | --- | --- |
| `ROOT_TRUST_SIGNING` | Generic platform root of trust | ECDSA P-384 / SHA-384; X.509 v3 trust anchor where PKI is used | Offline/highly protected HSM; non-exportable; class-specific `m-of-n` custody | X.509 trust anchor + SHA-256 fingerprint | active key target <= 5 years; shorter allowed; extension requires governed profile decision |
| `PLATFORM_INTERMEDIATE_SIGNING` | Signs constrained platform/purpose issuers | ECDSA P-384 / SHA-384; X.509 v3 CA | HSM/KMS; non-exportable | X.509 CA chain + fingerprint | <= 12 months |
| `REGIONAL_ISSUER_SIGNING` | Bounded Land issuer; may certify only approved descendant/runtime signer classes | ECDSA P-384 / SHA-384; constrained X.509 v3 issuer profile | Regional protected HSM/KMS boundary; never receives root key | X.509 constrained chain / issuer registry | <= 90 days |
| `AUTHORITY_ASSERTION_SIGNING` | Short-lived runtime projection of current `OrganizationalAuthority` | JWS `ES256` | HSM/KMS/protected signer; new key ID per rotation | JWK/JWKS, `alg=ES256`, RFC 7638 SHA-256 thumbprint | signing key <= 30 days; runtime assertion default 300 s, hard max 600 s |
| `SERVICE_ASSERTION_SIGNING` | Short-lived service-to-service assertion where signed assertions are used | JWS `ES256` | Workload/KMS signer, non-exportable where supported | JWK/JWKS bound to service issuer/audience | signing key <= 30 days; assertion default 300 s, hard max 900 s |
| `WORKLOAD_MTLS_LEAF` | Machine/workload authentication | X.509 v3 ECDSA P-256 leaf; TLS 1.3 preferred | Workload identity agent/HSM/KMS; machine-bound, no human download | X.509 chain; SAN is authoritative workload identity carrier | target <= 24 h; longer fallback requires documented exception and automated revocation |
| `PUBLIC_EDGE_TLS` | Public browser-facing HTTPS | Public-CA X.509; TLS 1.3 preferred; algorithms constrained by current BSI/public-PKI profile | Edge/provider protected key store | Public certificate chain | provider/BSI policy; not tied to EPD² private root |
| `AUDIT_EVIDENCE_SIGNING` | High-impact audit batch/evidence digest signing | ECDSA P-384 / SHA-384; detached signature profile | Isolated audit signer/HSM/KMS | Verification key/certificate + external timestamp/anchor evidence | <= 90 days; old public keys retained for verification under retention policy |
| `DATA_KEK` | Wraps data-encryption keys | 256-bit AES KEK; authenticated provider wrapping / approved AES-KWP profile | KMS/HSM only; plaintext KEK export prohibited | key/version handle and attestation metadata, no public key | <= 180 days target; rewrap before retirement |
| `DATA_DEK` | Data/object/batch encryption | AES-256-GCM | Generated in approved crypto boundary; wrapped at rest | wrapped key reference/version only | object/batch/policy bounded; never reused with nonce collision |
| `PROVIDER_CLIENT_SECRET` | Unavoidable external client secret | >=256 CSPRNG bits, opaque base64url/secret-manager value | Secret manager/provider boundary | no public representation | <= 90 days target or provider-shorter rule; automated rotation preferred |
| `HUMAN_PASSKEY` | Human authentication | WebAuthn; `ES256` mandatory offered profile; `EdDSA` allowed; `RS256` compatibility-only | User authenticator/device; private key never enters EPD² backend | COSE public key + credential metadata | no forced periodic rotation solely by age; revoke/replace on compromise/loss/policy event |
| `RECOVERY_MATERIAL` | Root/key-custody recovery where adopted | HSM-wrapped or threshold-protected material; no generic plaintext key file | Offline/recovery custody with separate quorum | metadata/evidence only | ceremony/policy bound; rotation mandatory after use |
| `OFFICIAL_SIGNATURE_SEAL_PROVIDER` | Legally required advanced/qualified signature, seal or trusted timestamp | Provider/eIDAS profile, not internal EPD² root by default | Qualified/approved provider or governed signing device | provider certificate/validation evidence | provider/legal profile |
| `VOTING_*` | Ballot/trustee/election cryptography | **Excluded from this generic profile** | Voting trust domain only | Voting-specific | PACK-16/voting governance only |

Cryptoperiod values above are initial **ceilings/targets for the generic profile**, not proof of provider readiness. INFRA/SEC may shorten them. Lengthening a stated ceiling requires a governed V23-profile revision or explicitly recorded exceptional profile with security review.

## 6. Trust hierarchy and key non-transfer

Target generic hierarchy:

```text
ROOT_TRUST_SIGNING (offline HSM, m-of-n)
        |
        +--> PLATFORM_INTERMEDIATE_SIGNING
                  |
                  +--> BUND/PURPOSE issuer(s)
                  |
                  +--> REGIONAL_ISSUER_SIGNING: LAND BERLIN
                  |          |
                  |          +--> AUTHORITY_ASSERTION_SIGNING (short-lived signer)
                  |          +--> permitted descendant signer only if delegation policy allows
                  |
                  +--> REGIONAL_ISSUER_SIGNING: LAND BAYERN
```

The root key is never copied into Bund/Land/Kreis/Ort infrastructure. A regional issuer receives only its own private key and a constrained certificate/issuer record. A runtime signer receives only its own key. Parent keys certify children; they are not distributed downward.

## 7. X.509 profile

Where X.509 is used:

- certificate version: v3;
- `BasicConstraints` and CA/path-length rules are explicit;
- `KeyUsage` and `ExtendedKeyUsage` are minimal and class-specific;
- `SubjectAltName` carries workload/service identity where appropriate; Common Name alone is not authorization identity;
- issuer, serial, validity, AKI/SKI and policy identifiers are validated;
- path building uses configured trust anchors only;
- revocation/freshness is governed by the accepted PKI design and must fail safely for consequential machine authorization;
- regional CA/issuer constraints must prevent cross-Land or root-like issuance;
- public-edge certificates use a public/approved CA path and MUST NOT expose or depend on the private organizational root merely for website TLS.

## 8. JOSE / JWT / JWK profile

Signed runtime assertions use compact or JSON JWS only where the owning API contract selects JWT/JWS. JWT is not mandatory for every artifact.

### Mandatory header validation

- exact `alg` allow-list by artifact class;
- exact `typ`, e.g. `epd2-authority+jwt` or `epd2-service+jwt`;
- mandatory opaque `kid`;
- unknown critical headers fail closed;
- `alg=none` rejected;
- `jku` / `x5u` received from an untrusted token are never followed dynamically;
- verifier trust locations are preconfigured/governed, not token-selected.

### Mandatory claims for authority assertions

At least:

- `iss`;
- `aud`;
- `iat`;
- `exp`;
- `jti`;
- authority ID;
- authority/state version or equivalent freshness reference;
- exact organization/scope;
- exact capability/action projection;
- purpose where applicable;
- source RuleVersion / policy reference where required.

A JWT claim is not the authoritative source of office. Consequential actions re-check current authority/restriction state according to V19-V22.

### Mandatory claims for service assertions

At least:

- `iss` service/workload identity;
- `sub` only where needed and scoped;
- exact `aud`;
- `iat` / `exp`;
- unique `jti` or equivalent replay handle where replay protection is required;
- environment;
- service credential/key version;
- intended purpose/scope.

Cross-environment and cross-audience reuse is rejected.

### Key IDs and thumbprints

- `kid` is an immutable opaque identifier generated from at least 128 bits of CSPRNG entropy and base64url encoded without semantic role/scope information;
- every new key version receives a new `kid`;
- `kid` reuse after revoke/destroy is prohibited;
- RFC 7638 SHA-256 JWK thumbprint is recorded separately as the public-key fingerprint; it may be used for verification/correlation but does not replace lifecycle metadata;
- unknown `kid` may trigger at most a refresh from the issuer's **trusted configured** JWKS location, after which it fails closed if still unknown.

## 9. JWKS / trust-set publication

A governed JWKS/trust set must expose only public verification material and lifecycle metadata safe for verifiers.

A rollover follows:

```text
NEW KEY GENERATED
-> PUBLIC KEY STAGED
-> VERIFIERS OBSERVE NEW KID
-> NEW KEY ACTIVE_SIGNING
-> OLD KEY VERIFY_ONLY
-> bounded artifact/cache lifetime
-> OLD KEY RETIRED/REVOKED
```

Indefinite dual-signing or indefinite dual-validity is prohibited. A compromised key may skip the normal overlap and move directly to revoke/deny handling.

## 10. Key lifecycle states

The common registry must be able to express at least:

```text
GENERATED
STAGED
ACTIVE_SIGNING
VERIFY_ONLY
COMPROMISED
REVOKED
RETIRED
DESTROYED
```

An implementation may refine names but must preserve the semantics. `COMPROMISED`, `REVOKED`, `RETIRED` and `DESTROYED` keys never return to signing-active state under the same key ID.

## 11. Data encryption profile

For EPD²-owned application encryption:

```text
plaintext
  -> AES-256-GCM with unique nonce and DATA_DEK
  -> wrapped DATA_DEK under versioned DATA_KEK
  -> ciphertext + nonce + authenticated context + key-version references
```

Authenticated context SHOULD bind record/domain/version metadata required to prevent ciphertext substitution across contexts without leaking protected identity into general indexes/logs.

KEK rotation rewraps DEKs or follows the accepted equivalent envelope design; it does not require decrypting all business plaintext into an administrator-visible workspace.

## 12. Human passkey profile

- WebAuthn/passkey private keys are authenticator-generated and non-exported to EPD² by design;
- `ES256` is the mandatory offered baseline for new enrollment interoperability;
- `EdDSA` may be accepted where the authenticator/browser/provider stack supports the standard COSE identifier and the implementation is tested;
- `RS256` is compatibility-only, not the preferred new-credential profile;
- attestation policy is separately governed; lack of attestation MUST NOT be silently interpreted as identity proof;
- credential recovery creates a new credential ID and does not resurrect suspended `OrganizationalAuthority`.

## 13. Service-to-service profile and API-03 gate

API-03 may use one or both of the following **approved patterns** according to its stage contract:

1. **mTLS workload identity** using `WORKLOAD_MTLS_LEAF`;
2. **short-lived signed service assertion** using `SERVICE_ASSERTION_SIGNING` / `ES256` with strict issuer/audience/purpose/replay validation.

Long-lived shared API keys are not an acceptable primary S2S architecture.

**API-03 C1 seal gate:** API-03 MUST NOT be sealed C1 until its exact final credential/trust mechanism is reconciled with this V23 profile **and** onto the exact independently accepted API-02 bytes required by Program Control. PRE-SEAL development may continue, but no PRE-SEAL evidence becomes acceptance merely because V23 exists.

## 14. API-02 reconciliation gate

API-02 is already `ACTIVE / IN DEVELOPMENT`. V23 does not reopen API-01 or invalidate work by assertion. Before API-02 acceptance, the final candidate must demonstrate/reconcile that:

- passkey/WebAuthn algorithm negotiation follows the human-passkey profile;
- any JWT/JWS authority/session helper artifact uses an explicit per-artifact algorithm allow-list and typing;
- no stale signed assertion can override current authority/session/restriction state;
- key IDs, issuer/audience and expiry validation match this profile;
- no generic symmetric JWT secret becomes a universal authorization key;
- any deviation is documented as an explicit governed profile exception before acceptance.

## 15. TLS profile

- TLS 1.3 is preferred for EPD²-managed service and external connections;
- TLS 1.2 is compatibility-only where required and must follow the then-current BSI TR-02102-2 profile;
- TLS 1.0/1.1 and SSL are prohibited;
- exact cipher-suite/group configuration is INFRA-owned but MUST remain inside the current BSI-approved set and this profile's no-legacy/no-downgrade rules;
- workload identity and public browser TLS remain separate certificate purposes.

## 16. Crypto agility and algorithm migration

Every cryptographic consumer must support a governed migration state:

```text
CURRENT
-> STAGED_NEXT
-> DUAL_VERIFY
-> NEW_ACTIVE
-> OLD_VERIFY_ONLY
-> RETIRED
```

Rules:

- dual verification is time-bounded;
- dual signing is prohibited by default and requires a profile-specific migration decision;
- artifact metadata identifies the exact algorithm/profile version;
- a verifier never chooses an algorithm because the attacker supplied it;
- downgrade to `COMPATIBILITY_ONLY` or `PROHIBITED` algorithm is rejected unless a named external-compatibility profile authorizes that exact path;
- migration evidence includes verifier convergence, rollback safety and old-key rejection at cutoff.

## 17. Prohibited implementation patterns

The following are prohibited for generic platform cryptography:

- handwritten production cryptographic primitives when a vetted provider/library exists;
- root/intermediate/regional private keys in repository files, container images, `.env` files, tickets, chat, e-mail or ordinary document stores;
- generic `master-key.pem` downloaded to an administrator laptop;
- one symmetric JWT key shared by unrelated issuers/verifiers;
- dynamic trust of `jku`/`x5u` from an untrusted token;
- accepting whatever `alg` the token declares;
- reuse of one signing key across unrelated artifact/protocol classes;
- key ID reuse after rotation/revocation;
- plaintext backup/escrow of root/KEK material;
- certificate CN-only authorization;
- indefinite trust/cache validity during disconnected operation;
- using the generic platform root to mint voting authority.

## 18. Machine-readable registry

The companion file
`docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json`
is the machine-readable planning registry for class IDs, algorithms, formats and major cryptoperiod/TTL constraints. The Markdown profile is normative where prose and JSON interpretation differ until a later formal schema is adopted.

## 19. Provider boundary

V23 selects **algorithms and formats**, not products.

INFRA later selects and proves:

- HSM/KMS/PKI provider(s);
- key generation APIs and attestation;
- non-exportability guarantees;
- multi-region/regional boundaries;
- certificate automation and revocation mechanism;
- secret manager;
- audit anchor/timestamp provider;
- PQ/hybrid provider capability when activated.

A product name is not compliance evidence.

## 20. Voting carve-out

PACK-16's voting cryptographic profile, ElectionGuard-derived finite-field parameters, guardian thresholds, voting checkpoint signature decisions and election key ceremony remain governed by the voting domain. V23 does not replace them with ES256/ES384 or generic regional issuer rules.

Shared implementation primitives may be reused only where the voting design explicitly allows them without introducing identity, platform-admin or regional-issuer authority into WS-03.

## 21. Acceptance criteria

`FIR-TRUST-003` is not complete until integrated acceptance proves at least that:

1. every production key has a registered class, purpose, algorithm, key ID/version, owner/custody profile and lifecycle state;
2. no generic root/intermediate/regional private key is exportable to political/ordinary administrators;
3. root/intermediate/regional trust uses the approved P-384/ES384 profile or an explicitly governed successor migration profile;
4. authority/service JWS uses ES256 with strict artifact-specific algorithm allow-list, typing, issuer/audience/expiry/key validation;
5. `alg=none`, HS* authorization-token confusion and attacker-selected trust URLs are rejected;
6. every key is restricted to one algorithm/use family;
7. an unknown/revoked `kid` fails closed after the permitted trusted-set refresh behavior;
8. runtime authority assertions expire within the profile limit and cannot override current suspended/revoked authority;
9. workload identity uses short-lived X.509/mTLS or the separately approved service-assertion path rather than unmanaged shared secrets;
10. regional issuers cannot mint Bund, cross-Land, root or voting authority;
11. AES-GCM nonce reuse is prevented and envelope-key rotation preserves decryptability until governed rewrap/retention completion;
12. audit signing and external anchoring are independent from the administrators whose actions are audited;
13. WebAuthn private keys remain in authenticators and recovery creates new credential identity;
14. crypto-agility migration can stage a successor algorithm/key without indefinite dual validity or downgrade;
15. prohibited/compatibility algorithms cannot be activated by configuration alone;
16. PQC algorithms remain inactive until an explicit migration profile is accepted, while schemas/trust registries can represent successor/hybrid algorithms without redesign;
17. API-02 acceptance demonstrates V23 reconciliation;
18. API-03 C1 seal demonstrates exact V23 S2S reconciliation after authoritative API-02 acceptance;
19. INFRA/OPS later prove provider custody, rotation, revocation, recovery and cryptoperiod operations rather than merely naming a provider;
20. voting-domain cryptography remains isolated and unchanged unless its own governed profile changes.
'''

profile_json = {
    "profile_id": "EPD2-CRYPTO-GENERIC-0.1",
    "status": "governed_target_not_activated",
    "date": "2026-08-28",
    "fir": "FIR-TRUST-003",
    "voting_domain_excluded": True,
    "algorithm_statuses": [
        "MANDATORY_BASELINE",
        "ALLOWED_SCOPED",
        "COMPATIBILITY_ONLY",
        "MIGRATION_CANDIDATE",
        "PROHIBITED",
    ],
    "algorithms": {
        "ES256": {"status": "MANDATORY_BASELINE", "uses": ["authority_assertion", "service_assertion", "passkey_preferred"]},
        "ES384": {"status": "MANDATORY_BASELINE", "uses": ["root_trust", "platform_intermediate", "regional_issuer", "audit_evidence"]},
        "Ed25519": {"status": "ALLOWED_SCOPED", "uses": ["explicit_detached_signature_profile", "compatible_webauthn", "existing_voting_lineage"]},
        "PS256_PS384": {"status": "COMPATIBILITY_ONLY", "uses": ["approved_external_integration"]},
        "RS256": {"status": "COMPATIBILITY_ONLY", "uses": ["legacy_external_verify", "webauthn_fallback_if_required"]},
        "JOSE_NONE": {"status": "PROHIBITED", "uses": []},
        "JOSE_HS_FOR_AUTHORITY": {"status": "PROHIBITED", "uses": []},
        "SHA256": {"status": "MANDATORY_BASELINE", "uses": ["digest", "jwk_thumbprint", "p256"]},
        "SHA384": {"status": "MANDATORY_BASELINE", "uses": ["p384", "high_impact_audit"]},
        "SHA1_MD5": {"status": "PROHIBITED", "uses": []},
        "AES_256_GCM": {"status": "MANDATORY_BASELINE", "uses": ["application_data_encryption", "envelope_data_encryption"]},
        "HKDF_SHA256_SHA384": {"status": "MANDATORY_BASELINE", "uses": ["approved_protocol_kdf"]},
        "ML_KEM_768": {"status": "MIGRATION_CANDIDATE", "uses": ["future_pq_key_establishment"]},
        "ML_DSA_65": {"status": "MIGRATION_CANDIDATE", "uses": ["future_pq_signatures"]},
    },
    "key_classes": [
        {"id": "ROOT_TRUST_SIGNING", "algorithm": "ES384", "format": "X509_V3_TRUST_ANCHOR", "private_boundary": "OFFLINE_HSM_M_OF_N_NON_EXPORTABLE", "max_active_days": 1826},
        {"id": "PLATFORM_INTERMEDIATE_SIGNING", "algorithm": "ES384", "format": "X509_V3_CA", "private_boundary": "HSM_KMS_NON_EXPORTABLE", "max_active_days": 365},
        {"id": "REGIONAL_ISSUER_SIGNING", "algorithm": "ES384", "format": "X509_V3_CONSTRAINED_CA", "private_boundary": "REGIONAL_HSM_KMS_NON_EXPORTABLE", "max_active_days": 90},
        {"id": "AUTHORITY_ASSERTION_SIGNING", "algorithm": "ES256", "format": "JWS_JWT_JWK_JWKS", "private_boundary": "HSM_KMS_PROTECTED_SIGNER", "max_active_days": 30, "assertion_default_ttl_seconds": 300, "assertion_hard_max_ttl_seconds": 600},
        {"id": "SERVICE_ASSERTION_SIGNING", "algorithm": "ES256", "format": "JWS_JWT_JWK_JWKS", "private_boundary": "WORKLOAD_OR_KMS_SIGNER", "max_active_days": 30, "assertion_default_ttl_seconds": 300, "assertion_hard_max_ttl_seconds": 900},
        {"id": "WORKLOAD_MTLS_LEAF", "algorithm": "ECDSA_P256", "format": "X509_V3", "private_boundary": "WORKLOAD_HSM_KMS_AGENT", "target_lifetime_hours": 24},
        {"id": "PUBLIC_EDGE_TLS", "algorithm": "CURRENT_BSI_PUBLIC_PKI_PROFILE", "format": "PUBLIC_CA_X509", "private_boundary": "EDGE_PROVIDER_PROTECTED", "cryptoperiod": "PROVIDER_BSI_POLICY"},
        {"id": "AUDIT_EVIDENCE_SIGNING", "algorithm": "ES384", "format": "DETACHED_SIGNATURE_PLUS_EXTERNAL_ANCHOR", "private_boundary": "ISOLATED_AUDIT_HSM_KMS", "max_active_days": 90},
        {"id": "DATA_KEK", "algorithm": "AES_256", "format": "KMS_HSM_WRAP_HANDLE", "private_boundary": "KMS_HSM_ONLY", "target_max_active_days": 180},
        {"id": "DATA_DEK", "algorithm": "AES_256_GCM", "format": "WRAPPED_KEY_REFERENCE", "private_boundary": "APPROVED_CRYPTO_BOUNDARY", "cryptoperiod": "OBJECT_BATCH_POLICY"},
        {"id": "PROVIDER_CLIENT_SECRET", "algorithm": "CSPRNG_256_BITS_MIN", "format": "OPAQUE_SECRET", "private_boundary": "SECRET_MANAGER_PROVIDER", "target_max_active_days": 90},
        {"id": "HUMAN_PASSKEY", "algorithm": "WEBAUTHN_ES256_BASELINE", "format": "COSE_PUBLIC_KEY", "private_boundary": "USER_AUTHENTICATOR", "age_rotation": "NOT_REQUIRED_SOLELY_BY_AGE"},
        {"id": "RECOVERY_MATERIAL", "algorithm": "THRESHOLD_OR_HSM_WRAPPED_PROFILE", "format": "NO_GENERIC_PLAINTEXT_FILE", "private_boundary": "OFFLINE_RECOVERY_CUSTODY", "cryptoperiod": "CEREMONY_POLICY_AND_ROTATE_AFTER_USE"},
        {"id": "OFFICIAL_SIGNATURE_SEAL_PROVIDER", "algorithm": "EIDAS_APPROVED_PROVIDER_PROFILE", "format": "PROVIDER_CERT_VALIDATION_EVIDENCE", "private_boundary": "QUALIFIED_APPROVED_PROVIDER_OR_SIGNING_DEVICE", "cryptoperiod": "PROVIDER_LEGAL_POLICY"},
        {"id": "VOTING_*", "algorithm": "PACK16_VOTING_PROFILE", "format": "VOTING_DOMAIN_ONLY", "private_boundary": "VOTING_TRUST_DOMAIN", "excluded_from_generic_profile": True},
    ],
    "jose": {
        "authority_typ": "epd2-authority+jwt",
        "service_typ": "epd2-service+jwt",
        "dynamic_jku_x5u_trust": False,
        "alg_none": False,
        "generic_hs_authorization": False,
        "kid_min_entropy_bits": 128,
        "kid_reuse": False,
        "jwk_thumbprint_hash": "SHA-256",
        "unknown_kid_behavior": "ONE_REFRESH_FROM_CONFIGURED_TRUSTED_ISSUER_THEN_FAIL_CLOSED",
    },
    "tls": {"preferred": "TLS1.3", "compatibility_only": "TLS1.2_CURRENT_BSI_PROFILE", "prohibited": ["TLS1.0", "TLS1.1", "SSLv2", "SSLv3"]},
    "crypto_agility": {"states": ["CURRENT", "STAGED_NEXT", "DUAL_VERIFY", "NEW_ACTIVE", "OLD_VERIFY_ONLY", "RETIRED"], "dual_signing_default": "PROHIBITED", "dual_verification": "BOUNDED_ONLY"},
    "api_gates": {
        "API_02": "MUST_RECONCILE_BEFORE_ACCEPTANCE",
        "API_03_PRESEAL": "MAY_CONTINUE",
        "API_03_C1": "BLOCKED_UNTIL_V23_RECONCILIATION_AND_EXACT_ACCEPTED_API02_BYTES",
    },
    "provider_selection": "DEFERRED_TO_INFRA",
}

PROFILE_MD.parent.mkdir(parents=True, exist_ok=True)
PROFILE_MD.write_text(profile_md.rstrip() + '\n', encoding='utf-8')
PROFILE_JSON.write_text(json.dumps(profile_json, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

master_add = r'''## V23 governance maintenance record — Cryptographic key classes, algorithm profiles and crypto-agility (2026-08-28)

**Round:** documentation/governance only. No API, INFRA, OPS, CTRL, FRONT, SEC or PILOT stage is accepted or closed by this update. No HSM/KMS/PKI provider is selected or activated and no voting cryptographic profile is changed.

**New FIR ID created:** `FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility` — status `approved`, priority `critical`.

**Governed profile artifacts:**

- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.md`;
- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json`.

**Scope:** the generic EPD² platform now has a governed target crypto profile before API-02/API-03 closure: ES384/P-384 for generic root/intermediate/regional trust and high-impact audit signing; ES256/P-256 for short-lived authority and service JWS assertions; X.509/mTLS for workload identity; WebAuthn ES256 as the mandatory offered passkey baseline with scoped compatibility options; AES-256-GCM for EPD²-owned application/envelope data encryption; strict JOSE/JWKS typing/allow-list/key-ID/trust-location rules; explicit crypto-agility; and ML-KEM-768/ML-DSA-65 as inactive migration candidates rather than current defaults. Provider selection remains INFRA-owned.

**API sequencing refinement:** API-02 is already active and must reconcile the final accepted candidate with this profile before acceptance. API-03 PRE-SEAL development may continue, but API-03 C1 seal is blocked until its exact service-to-service credential/trust mechanism is reconciled with this V23 profile and onto the exact independently accepted API-02 bytes required by Program Control.

**Voting boundary:** PACK-16 voting cryptography, trustee/quorum rules and voting key ceremonies remain governed by the isolated voting domain and are not replaced by this generic profile.

**Execution state:** unchanged. `API-02 = ACTIVE / IN DEVELOPMENT`; `API-03 = PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`.

## FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility

**Status:** approved  
**Priority:** critical  
**Domain:** cryptographic trust / key classes / algorithm policy / runtime assertions / workload identity / data encryption / crypto-agility  
**Target:** API + identity/session runtime + service identity + organization/governance + INFRA + OPS + CTRL + SEC + FINAL INTEGRATION; voting remains a separate domain profile

EPD² must use an explicit cryptographic class/profile registry rather than allowing each service, token, certificate or operator to choose algorithms ad hoc.

Core invariant:

```text
key class -> one purpose family -> one approved algorithm profile -> one custody profile
```

A key or valid cryptographic signature proves only the cryptographic statement defined by its profile. It never creates political, legal or organizational competence by itself.

### Generic platform baseline

- generic root/intermediate/regional trust: ECDSA P-384 + SHA-384 / `ES384`, X.509 v3 where PKI applies;
- short-lived `OrganizationalAuthority` runtime projections: JWS `ES256`, explicit `typ`, `iss`, `aud`, `exp`, `jti`, `kid`, authority/state freshness and exact scope/capability binding;
- short-lived service assertions where used: JWS `ES256` with exact service issuer/audience/environment/purpose and replay controls;
- workload identity: short-lived X.509 v3 mTLS leaf credentials, ECDSA P-256 baseline, TLS 1.3 preferred;
- human authentication: WebAuthn/passkey with ES256 as the mandatory offered baseline; EdDSA allowed where explicitly supported; RS256 compatibility-only;
- EPD²-owned data encryption: AES-256-GCM with unique nonce per key and versioned envelope keys; KEK held in HSM/KMS;
- high-impact audit/evidence signing: P-384/SHA-384 plus the V22 external anchor/timestamp/countersignature requirement;
- legal advanced/qualified signatures, seals and trusted timestamps: separately governed provider/eIDAS profile, not silently equated to the internal platform root;
- voting cryptography: excluded and unchanged under PACK-16/voting governance.

### Algorithm controls

Implementations must classify algorithms as `MANDATORY_BASELINE`, `ALLOWED_SCOPED`, `COMPATIBILITY_ONLY`, `MIGRATION_CANDIDATE` or `PROHIBITED` per use class.

At minimum:

- `alg=none` is prohibited for EPD² authorization/service/security assertions;
- generic HS* JWT authorization is prohibited;
- SHA-1/MD5, DSA, DES/3DES, RC4, ECB and new unauthenticated application CBC are prohibited;
- RSA-PKCS1-v1_5 signature profiles are compatibility/verify-only, not new generic issuer defaults;
- a key is bound to one algorithm and one purpose family;
- verifiers use exact allow-lists and never accept an algorithm because the untrusted artifact requested it;
- untrusted `jku`/`x5u` cannot select verifier trust locations;
- unknown `kid` fails closed after at most one refresh from the configured trusted issuer location.

### Key identifiers and lifecycle

Every new key version gets a new opaque `kid` with at least 128 bits of CSPRNG entropy. `kid` is never reused after rotation/revocation. RFC 7638 SHA-256 JWK thumbprint is stored separately as public-key fingerprint where JWK is used.

The registry must represent at least `GENERATED`, `STAGED`, `ACTIVE_SIGNING`, `VERIFY_ONLY`, `COMPROMISED`, `REVOKED`, `RETIRED` and `DESTROYED`. A compromised/revoked/retired/destroyed key never returns to signing-active state under the same ID.

### Initial generic cryptoperiod constraints

The governed profile artifact sets initial ceilings/targets by key class, including root <= 5 years, platform intermediate <= 12 months, regional issuer <= 90 days, runtime authority/service signer <= 30 days, authority assertion default 5 minutes/hard max 10 minutes, service assertion default 5 minutes/hard max 15 minutes, workload mTLS target <= 24 hours, audit signer <= 90 days and data KEK target <= 180 days. INFRA/SEC may shorten these. Lengthening a stated ceiling requires a governed profile revision/exception with security review.

Human passkeys are not force-rotated solely because of age; compromise, loss, assurance or policy events drive replacement.

### Crypto-agility and PQC

Consumers must support the governed migration sequence:

```text
CURRENT -> STAGED_NEXT -> DUAL_VERIFY -> NEW_ACTIVE -> OLD_VERIFY_ONLY -> RETIRED
```

Dual verification is bounded. Dual signing is prohibited by default unless a migration profile explicitly requires it. Downgrade to compatibility/prohibited algorithms fails closed.

`ML-KEM-768` and `ML-DSA-65` are recorded as `MIGRATION_CANDIDATE` only. No pure-PQ or hybrid activation is authorized by this FIR. The data model/trust registry must nevertheless be able to represent successor/hybrid profiles without architectural redesign.

### API gates

Before API-02 acceptance, its final candidate must reconcile passkey algorithm negotiation, any JWT/JWS helper/runtime artifacts, key ID handling, issuer/audience/expiry validation and current-state authorization with the V23 profile.

API-03 PRE-SEAL work may continue. API-03 C1 seal MUST NOT occur until:

1. authoritative API-02 is independently accepted;
2. API-03 is reconciled onto those exact accepted API-02 bytes;
3. the exact S2S mechanism selects only V23-approved workload mTLS and/or short-lived ES256 service assertion profiles;
4. trust generation, audience, replay, expiry, revocation and key-rotation behavior are demonstrated against the V23 profile.

### Provider boundary

V23 selects algorithms, formats and class semantics. INFRA selects concrete HSM/KMS/PKI/secret-manager/timestamp providers later and must prove non-exportability, generation, attestation, regional isolation, automation, revocation and recovery properties. Product branding is not acceptance evidence.

### Governing artifacts and acceptance

Detailed requirements, class table, format rules, JOSE/JWKS/X.509 profile, cryptoperiods, prohibited patterns, PQ migration boundary and acceptance criteria are governed by:

- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.md`;
- `docs/governance/EPD2_CRYPTOGRAPHIC_KEY_CLASSES_ALGORITHM_PROFILE_0.1.json`.

This FIR is not complete until the integrated baseline proves class registration, algorithm allow-listing, custody/non-exportability, bounded cryptoperiod and rotation, stale/revoked rejection, regional scope confinement, data-encryption nonce/key safety, crypto-agile migration, audit independence and the API-02/API-03 gates without weakening the isolated voting domain.
'''

master = master.rstrip() + '\n\n---\n\n' + master_add.rstrip() + '\n'
MASTER.write_text(master, encoding='utf-8')
master_sha256 = hashlib.sha256(master.encode('utf-8')).hexdigest()

control = control.replace(
    'Current Master maintenance level established by project governance work: **V22**',
    'Current Master maintenance level established by project governance work: **V23**',
    1,
)
control = control.replace('**Updated:** 2026-08-27', '**Updated:** 2026-08-28', 1)

v23_note = f'''**Documentation-only V23 governance update (2026-08-28):** `FIR-TRUST-003 — Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility` is now recorded as an approved critical future requirement. The generic platform baseline fixes ES384/P-384 for root/intermediate/regional trust and high-impact audit signing; ES256/P-256 for short-lived authority/service JWS assertions; X.509/mTLS workload identity; WebAuthn ES256 as the mandatory offered passkey profile; AES-256-GCM application/envelope encryption; strict JOSE/JWKS key/algorithm/trust-location validation; class-specific cryptoperiod ceilings; and an inactive ML-KEM-768/ML-DSA-65 migration track. Concrete HSM/KMS/PKI provider selection remains INFRA-owned and PACK-16 voting cryptography is unchanged. Canonical Master SHA-256 after this update: `{master_sha256}`. API-02 remains `ACTIVE / IN DEVELOPMENT` and must reconcile with V23 before acceptance. API-03 remains `PARALLEL_WORKING_PRESEAL_NOT_ACCEPTED`; PRE-SEAL work may continue, but API-03 C1 seal is blocked until exact V23 S2S reconciliation on the exact independently accepted API-02 bytes. This documentation update implements/activates no provider and accepts/closes no implementation stage.'''

marker = '**API-02 execution-state reconciliation (2026-08-27):**'
assert marker in control
assert 'Documentation-only V23 governance update' not in control
control = control.replace(marker, v23_note + '\n\n' + marker, 1)
CONTROL.write_text(control, encoding='utf-8')

print('V23 profile written')
print('MASTER_SHA256=' + master_sha256)
print('PROFILE_MD_SHA256=' + hashlib.sha256(PROFILE_MD.read_bytes()).hexdigest())
print('PROFILE_JSON_SHA256=' + hashlib.sha256(PROFILE_JSON.read_bytes()).hexdigest())
