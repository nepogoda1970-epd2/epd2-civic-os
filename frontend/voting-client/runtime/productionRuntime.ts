/**
 * The production adapter.
 *
 * Every operation maps to an exact accepted external contract or returns a
 * controlled unavailability.  At the FRONT-04 entering baseline the second
 * branch is the only one taken, and the constants below record precisely why.
 *
 * There is no `fetch` in this file.  That is not an oversight and not a
 * placeholder: issuing a request would require a route, and every route this
 * client would need is specification-level.  The static validator asserts the
 * absence, so a speculative call cannot be added without failing a gate.
 */

import {
  BALLOT_CRYPTO_RUNTIME,
  WS03_CAPABILITIES,
} from "../domain/capabilities";
import type {
  BallotStyle,
  ElectionContext,
  Receipt,
  Result,
  VotingContext,
} from "../domain/types";
import { PRODUCTION_REFUSALS, unavailable } from "./unavailable";
import type { VotingRuntime } from "./ports";

/**
 * Exact accepted lineage this adapter is pinned to.  A mutation that changes
 * one of these values is detected, which is the point of writing them out.
 */
export const ACCEPTED_LINEAGE = Object.freeze({
  api02C13Sha256:
    "9363561271f0f92d2afc42ccbb0d792cb5461c97c19a5f46a6fa51408bdfc6a9",
  api02C13AcceptanceRun: 33497989489,
  api02C13AcceptanceJob: 99824485228,
  api03C5Sha256:
    "5fb769cd387c7bcf10b9783d05fce44066985c7408a015cb4c670419ce316b55",
  front02C21Sha256:
    "aaf980a2cd3b3b06d48218adaa68d109c8770e6abfcbef230197b51a87006179",
  front03C1Sha256:
    "fec7b19d77c27cbc3ef8a34e433f5aef94ef7853f76d3212bed6acd682497c26",
  front03C1AcceptanceRun: 33528038712,
  front03C1AcceptanceJob: 99923795567,
  enteringCanonicalMain: "c333b9dd12e0c13dd402222cc958d95e779b8488",
} as const);

/**
 * The identity-side route that *is* accepted.  It is recorded here so the
 * boundary is explicit about what exists, and it is deliberately not called:
 * it is a WS-02 operation requiring a Member session, an object version, an
 * idempotency key and a bound high-assurance step-up, none of which exist on
 * this side of the boundary and none of which WS-03 may hold.
 */
export const ACCEPTED_IDENTITY_SIDE_ROUTE = Object.freeze({
  method: "POST",
  path: "/api/v1/identity/voting-handoff",
  owner: "API-02 C13 / identity-service",
  ingressClass: "MEMBER",
  callableFromWs03: false,
  reason:
    "Issuance is a WS-02 Member operation. WS-03 holds no session, no object version and no step-up binding, and must not.",
} as const);

/**
 * Specification-level operations that must never be treated as runtime.  The
 * list exists so a gate can assert that none of them is called.
 */
export const SPECIFICATION_ONLY_OPERATIONS = Object.freeze([
  "GET /elections/{election_context_id}/manifest",
  "GET /elections/{election_context_id}/parameters",
  "GET /elections/{election_context_id}/joint-key",
  "GET /elections/{election_context_id}/ballot-styles/{ballot_style_id}",
  "POST /elections/{election_context_id}/capability/probe",
  "POST /elections/{election_context_id}/ballots",
  "POST /elections/{election_context_id}/public-challenges",
  "GET /elections/{election_context_id}/submissions/{retry_token}",
  "GET /elections/{election_context_id}/receipts/{confirmation_code}",
  "GET /elections/{election_context_id}/confirmations/{confirmation_code}",
] as const);

export const SPECIFICATION_SOURCE =
  "docs/packs/PACK-16/PACK-16C-API-CATALOG.md — no endpoint is implemented in that round";

/** No service-to-service authority exists in the browser. */
export const BROWSER_AUTHORITY = Object.freeze({
  servicePrivateKey: false,
  mtlsClientSecret: false,
  s2sBearerCredential: false,
  serviceAssertion: false,
  backendSigningKey: false,
  privilegedApiToken: false,
  authorizationHeader: false,
  memberSessionCookie: false,
} as const);

export function createProductionRuntime(): VotingRuntime {
  return Object.freeze({
    profile: "production" as const,
    handoff: Object.freeze({
      async consume(): Promise<Result<VotingContext>> {
        return unavailable<VotingContext>(PRODUCTION_REFUSALS.handoffChannel);
      },
    }),
    electionManifest: Object.freeze({
      async read(): Promise<Result<ElectionContext>> {
        return unavailable<ElectionContext>(
          PRODUCTION_REFUSALS.electionContext,
        );
      },
    }),
    ballotStyle: Object.freeze({
      async read(): Promise<Result<BallotStyle>> {
        return unavailable<BallotStyle>(PRODUCTION_REFUSALS.ballotStyle);
      },
    }),
    crypto: Object.freeze({
      async prepareEnvelope(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.crypto);
      },
    }),
    submission: Object.freeze({
      async submit(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.submission);
      },
      async status(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.submissionStatus);
      },
    }),
    receipt: Object.freeze({
      async readReceipt(): Promise<Result<Receipt>> {
        return unavailable<Receipt>(PRODUCTION_REFUSALS.receipt);
      },
      async confirmRecordedAsCast(): Promise<Result<never>> {
        return unavailable<never>(PRODUCTION_REFUSALS.recordedAsCast);
      },
    }),
  });
}

/** Re-exported so a single import proves the crypto position in one place. */
export const PRODUCTION_BALLOT_CRYPTO_RUNTIME = BALLOT_CRYPTO_RUNTIME;

export function productionCapabilityCount(): number {
  return WS03_CAPABILITIES.length;
}
