# EPD² Cryptographic Key Classes, Algorithm Profiles & Crypto-Agility 0.1

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
