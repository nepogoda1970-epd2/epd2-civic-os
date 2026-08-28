# EPD² Open Trust Core & Commercial Operations Boundary 0.1

**Status:** governed proposal supporting `FIR-OSS-007`; not itself a software-release, licensing-activation or commercial-product decision  
**Date:** 2026-08-29  
**Purpose:** define the mandatory boundary between publicly inspectable trust-critical material and commercially operable infrastructure/services without weakening independent verification, voting isolation, audit integrity or existing EUPL obligations.

## 1. Governing principle

EPD² uses an Open Trust Core model:

> Trust-critical correctness must remain independently inspectable and reproducible. Commercial value may be created around deployment, integration, resilience, compliance, support and operational responsibility, but not by making correctness depend on a closed component.

A closed or commercially licensed component may improve availability, convenience, scale, observability, integration or assurance operations. It must not be necessary to establish the cryptographic truth of an election, to independently verify the published election record, to validate a key ceremony against its public protocol, or to verify the integrity claims of published audit evidence.

## 2. Mandatory Public Trust Core

The following classes are public and independently reviewable when applicable to the implemented voting/trust profile:

- protocol specifications and canonical state/record semantics;
- threat model, security claims, limitations and residual-risk statements;
- mathematical definitions and proofs used to justify protocol properties;
- cryptographic core or a complete reference implementation sufficient for independent verification;
- canonical encoding, domain separation and public test vectors;
- client cryptographic core / SDK needed to construct and verify protocol artefacts;
- a minimal reference voting client sufficient to exercise the public protocol without proprietary infrastructure;
- independent verifier code that consumes public election artefacts only;
- reproducible or independently verifiable verifier/build instructions, with containerized one-command verification where practical;
- key/guardian ceremony specification, transcript/evidence format and reference ceremony tooling/scripts;
- public election-record specification, tally/finalization semantics, publication commitments and verification rules;
- public audit-evidence integrity format, hash/anchor verification semantics and independent verification tooling;
- public schemas, protocol versioning rules, compatibility rules and public security/vulnerability-reporting process.

The Public Trust Core must expose enough information for an independent expert to determine what the system proves, what it does not prove, and whether a published result conforms to the governed protocol without access to EPD² private infrastructure.

## 3. Commercial / Enterprise Operations layer

Subject to the software licence, third-party licence obligations, copyright ownership and a separate commercial/legal review, EPD² may commercialize operational capabilities such as:

- managed hosting / SaaS and deployment automation;
- production orchestration and election-lifecycle operations tooling, provided the governing state machine and verification-relevant semantics remain public;
- high-availability, disaster-recovery and multi-region infrastructure;
- enterprise administration UX and workflow convenience;
- Guardian operational UX, provided guardian cryptographic behaviour and ceremony/verifier semantics remain in the Public Trust Core;
- HSM/KMS vendor adapters and enterprise/government infrastructure integrations;
- compliance workflow tooling and evidence packaging;
- observability, monitoring, incident integration and operational dashboards;
- WORM/audit-storage infrastructure and commercial external anchoring services, provided the evidence format and independent integrity verification remain public;
- hardened/certified distributions, deployment profiles and release qualification;
- SLA, long-term support, maintenance, professional services and certification assistance.

This section does **not** declare any existing EUPL-covered EPD² source proprietary. A proprietary or differently licensed commercial component is permitted only where it is legally a separate work/component or service and where EUPL-1.2, dependency, copyright, network-communication and derivative-work obligations are fully satisfied. Commercial packaging may not be used to evade an applicable source-availability obligation.

## 4. Non-negotiable boundary test

For every component proposed for the commercial/closed side, the following question is mandatory:

> If this component is unavailable, unauditable or malicious, can an independent verifier still detect a false election result or a violation of the governed public protocol from the published trust artefacts?

If the answer is **no**, the trust-critical portion of that component belongs in the Public Trust Core.

A closed component may:

- accelerate or automate a governed process;
- scale or replicate it;
- monitor it;
- integrate it with enterprise/government systems;
- package compliance evidence;
- provide operational convenience and SLA.

A closed component must not:

- define secret acceptance rules for ballots or election records;
- be the only implementation able to verify a result;
- introduce an undisclosed emergency-decrypt or bypass path;
- bypass guardian quorum, ceremony or finalization rules;
- make a result verifiable only to the operator;
- hide verification-relevant state-machine transitions or finalization semantics;
- make audit integrity provable only with proprietary credentials or operator-only data;
- weaken PACK-15/16 unlinkability, voting-domain isolation or the separation between voting keys and generic platform trust.

## 5. Voting-domain placement

This model does not rename EPD² as a voting-only platform and does not merge the Voting Trust Domain into the generic Civic OS trust hierarchy.

PACK-15/16 voting isolation remains controlling. `FIR-TRUST-003` generic root/intermediate/regional algorithms do not replace PACK-16 voting cryptography, trustee/quorum rules or election key ceremony.

The Public Trust Core for voting must include every verification-relevant protocol element required to reproduce and independently verify the election record. Production guardian custody, HSM integration and operational ceremony execution may use commercial tooling, but the underlying ceremony protocol, evidence requirements and verification logic remain public.

## 6. Audit placement

Commercial audit infrastructure may provide storage, WORM retention, indexing, SIEM integration, alerting and external anchoring services.

The following remain public trust semantics:

- canonical evidence/digest rules;
- chain/batch integrity rules;
- anchor/timestamp verification semantics;
- verifier inputs and outputs;
- proof that historical evidence cannot be silently rewritten without detection.

No proprietary audit backend may become the sole authority capable of deciding whether published evidence is authentic.

## 7. Licensing boundary

`FIR-OSS-001` remains controlling: the intended licence baseline for original EPD² software is **EUPL-1.2**, subject to the already-required final legal review before public release.

This model does not replace EUPL-1.2 with Apache-2.0 and does not grant automatic relicensing rights.

`FIR-OSS-002` through `FIR-OSS-006` remain in force, including source-availability obligations where applicable, dependency compatibility, contribution provenance, trademark/official-instance separation, reproducible verification and the public security process.

A future dual-licensing, separate-enterprise-codebase or alternative commercial licensing model requires a separate governed decision and legal/copyright review. It must not retroactively remove rights already granted under EUPL-1.2 or conceal source that the applicable licence requires to be available.

## 8. Release and provenance requirements

A public trust release must bind, as applicable:

- exact protocol/profile version;
- exact source revision;
- signed release manifest;
- source-to-binary or source-to-container provenance;
- verifier build/run instructions;
- public test-vector catalogue;
- election-record schema/profile;
- known limitations and non-verified claims;
- security advisory and vulnerability disclosure channel.

Official EPD² branding, certification and official-instance status remain separate from open-source rights under `FIR-OSS-005`.

## 9. Acceptance criteria

`FIR-OSS-007` is complete only when the exact release/deployment model proves all of the following:

1. all trust-critical election semantics required for independent verification are publicly specified;
2. an independent verifier can validate a conforming published election record without private EPD² infrastructure, operator credentials or proprietary verification services;
3. verification-relevant cryptographic core, canonical encoding and test vectors are publicly available under the governed licensing model;
4. key/guardian ceremony rules and evidence verification are publicly specified and independently testable;
5. a minimal public reference client can exercise the protocol sufficiently to validate the public specification rather than merely displaying a vendor API;
6. public audit-evidence integrity semantics and verification tooling do not depend on a proprietary backend;
7. every commercial/closed component passes the non-negotiable boundary test in § 4;
8. no commercial component can introduce an undetectable alternate ballot acceptance, tally, finalization, decrypt, quorum-bypass or result-signing path;
9. EUPL-1.2 and third-party licence obligations are demonstrably satisfied for every released or network-provided component to which they apply;
10. public/open status is kept separate from official-instance, certification, legal activation and production-readiness claims.

## 10. Execution placement

- **PACK-15/16 lineage:** preserve voting separation and map trust-critical reference components/artefacts to the Public Trust Core; do not retroactively claim previously closed work re-licensed or production-ready.
- **API:** public protocol/API schemas where they are verification-relevant; commercial gateway/operational convenience must not create hidden trust semantics.
- **INFRA:** concrete managed deployment, HA, HSM/KMS, WORM storage and enterprise connectors may implement commercial operations, subject to the boundary test.
- **OPS:** SLA, runbooks, support, release qualification and managed ceremony/election operations.
- **CTRL/FRONT:** enterprise admin/guardian UX may be commercial, while public verification journeys and public reference tooling remain available.
- **SEC:** test for hidden trust dependencies, closed-component result substitution, verifier dependence, alternate finalization, emergency decrypt, ceremony bypass and source/binary divergence.
- **FINAL INTEGRATION:** prove that the public verification path reaches the same final trust artefacts produced by the production deployment.

## 11. Status boundary

This document is governance only. It does not:

- publish source code by itself;
- alter an existing software licence by itself;
- create a proprietary enterprise product by itself;
- accept or close PACK-16, PACK-17, API, INFRA, OPS, CTRL, FRONT or SEC;
- certify a voting system;
- activate public elections;
- select a commercial HSM/KMS, audit, cloud or hosting provider.
