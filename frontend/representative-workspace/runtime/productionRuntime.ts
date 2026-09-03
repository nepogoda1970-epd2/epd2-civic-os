/**
 * The production adapter.
 *
 * Every operation maps to an exact accepted external contract or returns a
 * controlled unavailability. At the FRONT-05 entering baseline the second
 * branch is the only one taken, and the constants below record precisely why.
 *
 * There is no `fetch` in this file, and no URL string. That is not an oversight
 * and not a placeholder: issuing a request would require a route, and no
 * accepted executable route exists for anything WS-04 would call. The static
 * validator asserts the absence, so a speculative call cannot be added without
 * failing a gate.
 */

import {
  WS04_CAPABILITIES,
  anyNetworkCapabilityExecutable,
} from "../domain/capabilities";
import { productionUnavailable } from "./unavailable";
import type {
  AuditPort,
  CaseDeskPort,
  ConflictPort,
  DeclarationPort,
  DeviationPort,
  EligibilityDisplayPort,
  MandateScopePort,
  MandateSessionPort,
  PositionPort,
  PublicationPort,
  RegistryReferencePort,
  RepresentativeRuntime,
} from "./ports";

/**
 * Exact accepted lineage this adapter is pinned to. A mutation that changes one
 * of these values is detected, which is why they are written out rather than
 * described.
 */
export const ACCEPTED_LINEAGE = Object.freeze({
  front04C2Sha256:
    "1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8",
  front04C2SourceTreeDigest:
    "eee6bf1e80f9e5b5ce18618611513b871b195a163e98948d55d99f61276f2f2e",
  front04C2StageContractDigest:
    "b5bfab8f8d74cfe0028a435a6bfbf94d116ff232781c55b5f72532caded76cc2",
  front04C2AuthoritativeRun: 33569268417,
  front04C2AuthoritativeJob: 100059427183,
  front04C2ReviewedCommit: "66a65f2303d2a0d18fb8396887a35d6c14df1d92",
  front03C1Sha256:
    "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26",
  front02C21Sha256:
    "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179",
  enteringCanonicalMain: "217559b7",
} as const);

/**
 * The predecessor programme state, as recorded in the accepted records. WS-04
 * depends on units that are not merely incomplete but, in two cases, not
 * started at all.
 */
export const PREDECESSOR_STATE = Object.freeze({
  ARCH: "CLOSED",
  DATA: "CLOSED",
  API: "API-02 ACTIVE / IN DEVELOPMENT",
  INFRA: "NOT_STARTED",
  OPS: "NOT_STARTED",
  CTRL: "NOT_STARTED",
} as const);

/**
 * The operations WS-04 would call if they existed. Every one is
 * specification-level, unaccepted, or absent, and the source column says which.
 * These strings are never used to build a request; they exist so the boundary
 * is explicit about what is missing rather than silently empty.
 */
export const SPECIFICATION_ONLY_OPERATIONS = Object.freeze([
  "GET /representative/mandates/{mandate_id}",
  "GET /representative/mandates/{mandate_id}/cases",
  "GET /representative/mandates/{mandate_id}/cases/{case_id}",
  "POST /representative/mandates/{mandate_id}/cases/{case_id}/transitions",
  "GET /representative/mandates/{mandate_id}/cases/search",
  "GET /representative/mandates/{mandate_id}/positions",
  "PUT /representative/mandates/{mandate_id}/positions/{position_id}",
  "POST /representative/mandates/{mandate_id}/positions/{position_id}/submit",
  "GET /representative/mandates/{mandate_id}/deviations",
  "POST /representative/mandates/{mandate_id}/deviations",
  "GET /representative/mandates/{mandate_id}/declarations",
  "POST /representative/mandates/{mandate_id}/declarations",
  "POST /representative/mandates/{mandate_id}/publication-proposals",
  "GET /representative/mandates/{mandate_id}/publication-proposals/{proposal_id}",
  "GET /representative/mandates/{mandate_id}/conflict-restrictions",
] as const);

export const SPECIFICATION_SOURCE = Object.freeze({
  desk: "representative-desk-service exists only inside the unaccepted PACK-29 candidate archive; FIR-REP-001..004 are recorded as 'captured'.",
  mandate:
    "office-mandate-service exists only inside the unaccepted PACK-20 candidate archive.",
  compliance:
    "compliance-service (PACK-09) defines RepresentationMandate as legal power of attorney, not an elected mandate.",
  transparency:
    "transparency-service (PACK-13) has the single publication state PUBLISHED and a caller-supplied actor_is_authorized boolean; it has no proposal model.",
  control: "CTRL is NOT_STARTED and no control-plane code is present.",
  http: "Every contracts/openapi/pack-*.yaml states that no production HTTP server ships in that pack.",
} as const);

/** No service-to-service authority exists in the browser. */
export const BROWSER_AUTHORITY = Object.freeze({
  servicePrivateKey: false,
  mtlsClientSecret: false,
  s2sBearerCredential: false,
  serviceAssertion: false,
  backendSigningKey: false,
  privilegedApiToken: false,
  registryWriteCredential: false,
  publicationApprovalCredential: false,
} as const);

/**
 * Asserted at module load. If a future change marks a network capability
 * executable while this adapter still cannot reach one, the workspace refuses
 * to start rather than presenting a capability it does not have.
 */
function assertNoExecutableNetworkCapability(): void {
  if (anyNetworkCapabilityExecutable()) {
    throw new Error(
      "WS-04 production adapter: a network capability is marked executable but no accepted runtime exists.",
    );
  }
}

export function createProductionRuntime(): RepresentativeRuntime {
  assertNoExecutableNetworkCapability();

  const session: MandateSessionPort = {
    current: async () => productionUnavailable("session"),
    observeStepUp: async () => productionUnavailable("stepUp"),
    signOut: async () => productionUnavailable("session"),
  };

  const scope: MandateScopePort = {
    resolve: async () => productionUnavailable("scope"),
  };

  const cases: CaseDeskPort = {
    list: async () => productionUnavailable("caseList"),
    read: async () => productionUnavailable("caseDetail"),
    search: async () => productionUnavailable("caseSearch"),
    transition: async () => productionUnavailable("caseMutation"),
    reread: async () => productionUnavailable("caseDetail"),
  };

  const positions: PositionPort = {
    list: async () => productionUnavailable("position"),
    save: async () => productionUnavailable("positionWrite"),
    submitInternal: async () => productionUnavailable("positionWrite"),
  };

  const deviations: DeviationPort = {
    list: async () => productionUnavailable("deviation"),
    record: async () => productionUnavailable("deviation"),
    resolveDecision: async () => productionUnavailable("decisionReference"),
  };

  const declarations: DeclarationPort = {
    list: async () => productionUnavailable("declaration"),
    submit: async () => productionUnavailable("declaration"),
  };

  const publication: PublicationPort = {
    propose: async () => productionUnavailable("publicationProposal"),
    withdraw: async () => productionUnavailable("publicationProposal"),
    observe: async () => productionUnavailable("publicationState"),
  };

  const conflict: ConflictPort = {
    restrictions: async () => productionUnavailable("conflict"),
    recordAssessmentProposal: async () => productionUnavailable("conflict"),
  };

  const registry: RegistryReferencePort = {
    read: async () => productionUnavailable("registry"),
  };

  const eligibility: EligibilityDisplayPort = {
    observe: async () => productionUnavailable("eligibility"),
  };

  const audit: AuditPort = {
    read: async () => productionUnavailable("audit"),
  };

  return Object.freeze({
    profile: "production",
    session,
    scope,
    cases,
    positions,
    deviations,
    declarations,
    publication,
    conflict,
    registry,
    eligibility,
    audit,
  });
}

/** Used by the workspace status surface, so the state is never implicit. */
export function productionCapabilitySummary(): {
  readonly total: number;
  readonly blocked: number;
  readonly executable: number;
} {
  const total = WS04_CAPABILITIES.length;
  const blocked = WS04_CAPABILITIES.filter(
    (c) => c.status === "BLOCKED_BY_DEPENDENCY",
  ).length;
  const executable = WS04_CAPABILITIES.filter(
    (c) => c.status === "SUPPORTED_REAL_PATH",
  ).length;
  return { total, blocked, executable };
}
