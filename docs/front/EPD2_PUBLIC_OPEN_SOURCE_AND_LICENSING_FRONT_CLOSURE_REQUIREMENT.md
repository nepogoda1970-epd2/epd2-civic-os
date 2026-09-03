# EPD² Public Open Source & Licensing — FRONT Closure Requirement

**Status:** APPROVED / MANDATORY FRONT-CLOSURE REQUIREMENT  
**Date:** 2026-09-03  
**Scope:** public website / public product information surface  
**Governance basis:** `FIR-OSS-007 — Open Trust Core & Commercial Operations Boundary`

## 1. Requirement

The EPD² FRONT layer MUST NOT be declared fully closed unless the public website contains a clearly accessible, non-misleading **Open Source & Licensing** information surface.

The public surface must explain, in plain language, the boundary between the independently verifiable open trust core and the commercial operational/enterprise layer.

## 2. Mandatory public content

The page or equivalent public section MUST state at least:

1. which verification-relevant components are open and independently inspectable;
2. which operational, managed, enterprise and support capabilities may remain commercial;
3. that the verification-relevant protocol semantics, cryptographic/reference verification code, canonical encodings/test vectors, minimal reference voting client, independent verifier, guardian/key-ceremony protocol/evidence, election-record/finalization semantics and public audit-integrity verification cannot be hidden behind a commercial agreement when they are required to establish cryptographic truth;
4. that managed hosting/orchestration, HA/resilience, enterprise/admin/guardian/operations UX, HSM/KMS and external/government integrations, observability, compliance tooling, hardened/certified distributions, SLA/support and professional services may be commercial where they are not required to establish cryptographic truth;
5. the current intended original-project licence baseline (`EUPL-1.2`, subject to final legal review) without implying that every repository artifact or third-party dependency is licensed identically;
6. links to the public source repository and, once available, the public verifier/reference-client resources;
7. a concise explanation that independent verifiability is available without purchasing a commercial operating agreement.

## 3. Mandatory product/UX properties

The information must be reachable from the public website without authentication and without a commercial contract.

It must not be buried only in legal fine print. A normal visitor, potential party member, auditor, partner or customer must be able to understand the open/commercial boundary from the public-facing product information.

German is the primary mandatory public language for the German party/product site. Any additional language version must preserve the same substantive boundary and must not weaken or expand the licensing claims.

## 4. Acceptance gate

Before **FRONT LAYER = CLOSED**, authoritative FRONT closure evidence MUST prove:

- the public Open Source & Licensing page/section exists;
- it is reachable from the public navigation or another clearly discoverable public path;
- the open-core/commercial boundary matches `FIR-OSS-007`;
- no commercial agreement is required to access verification-critical public information/code that must remain open;
- commercial capabilities are described without implying that cryptographic truth or independent verification itself is paywalled;
- the EUPL-1.2 statement carries the required legal-review qualification;
- repository/verifier/reference-client links are valid when those resources are published;
- accessibility and responsive browser checks pass;
- no production-readiness, legal-activation, BSI/Common Criteria or certification claim is inferred merely from this page.

Failure of this gate blocks final FRONT-layer closure.

## 5. Non-claims

This requirement does not itself:

- relicense existing source;
- decide licence treatment of third-party dependencies;
- declare a certified distribution available;
- make a BSI/Common Criteria claim;
- close any FRONT stage or the FRONT layer;
- replace `FIR-OSS-007` or the Master Future Implementation Register.

It is a mandatory public-surface implementation obligation derived from the approved open-trust-core/commercial-operations boundary.
