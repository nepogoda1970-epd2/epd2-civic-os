/**
 * The WS-03 capability register.
 *
 * Every capability the Voting Client could exercise is listed with one
 * controlled status and the exact reason.  Nothing in the interface may call a
 * capability active that is not `AVAILABLE_ACCEPTED_RUNTIME` here, and the
 * static validator cross-checks this table against
 * `docs/frontend/FRONT-04-CAPABILITY-STATUS-MATRIX.csv`.
 *
 * The statuses below are the honest answer at the FRONT-04 entering baseline:
 * the only accepted runtime voting route in the programme is API-02 C13's
 * identity-side issuance, which is a WS-02 operation.  No accepted executable
 * contract exists for anything WS-03 would call, so every network capability
 * is blocked and the interface implements the safe state instead.
 */

import type { CapabilityStatus } from "./types";

export type CapabilityId =
  | "handoff_consumption"
  | "election_context"
  | "ballot_style"
  | "public_election_parameters"
  | "public_joint_key"
  | "capability_probe"
  | "ballot_crypto"
  | "ballot_submission"
  | "submission_recovery"
  | "local_diagnostic_challenge"
  | "public_evidentiary_challenge"
  | "receipt_presentation"
  | "receipt_verification"
  | "recorded_as_cast_verification"
  | "accessibility_assistance"
  | "governed_fallback";

export type CapabilityRecord = {
  readonly id: CapabilityId;
  readonly status: CapabilityStatus;
  readonly owner: string;
  readonly reason: string;
  readonly frontendBehaviour: string;
};

export const WS03_CAPABILITIES: readonly CapabilityRecord[] = Object.freeze([
  {
    id: "handoff_consumption",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "API-02 / identity boundary",
    reason:
      "The accepted API-02 C13 route POST /api/v1/identity/voting-handoff is the identity-side issuance operation and is a WS-02 call. No accepted executable route exists for presenting or redeeming a handoff from a WS-03 browser.",
    frontendBehaviour:
      "The credential surface verifies a presented handoff with the exact accepted semantics and refuses every channel, so no context is ever established from the browser alone.",
  },
  {
    id: "election_context",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C / voting runtime",
    reason:
      "GET /elections/{election_context_id}/manifest is specification-level in PACK-16C, which states that no endpoint is implemented in that round.",
    frontendBehaviour:
      "Election context is unavailable; the surface says so and offers the governed fallback.",
  },
  {
    id: "ballot_style",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C / voting runtime",
    reason:
      "GET /elections/{election_context_id}/ballot-styles/{ballot_style_id} is specification-level only.",
    frontendBehaviour:
      "No ballot style is fetched in production. The renderer exists and is exercised only under the governed test profile.",
  },
  {
    id: "public_election_parameters",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16B / PACK-16C",
    reason:
      "GET /elections/{election_context_id}/parameters is specification-level only.",
    frontendBehaviour: "Unavailable; no parameter set is assumed.",
  },
  {
    id: "public_joint_key",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16B / PACK-16C",
    reason:
      "GET /elections/{election_context_id}/joint-key is specification-level only.",
    frontendBehaviour: "Unavailable; no key material is fetched or held.",
  },
  {
    id: "capability_probe",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C",
    reason:
      "POST /elections/{election_context_id}/capability/probe is specification-level only.",
    frontendBehaviour:
      "Unavailable; eligibility is never inferred in the browser.",
  },
  {
    id: "ballot_crypto",
    status: "BLOCKED_CRYPTO",
    owner: "PACK-16D reference implementation",
    reason:
      "The only ballot encryption, proof and confirmation-code implementation in the programme is the PACK-16D Python reference implementation, explicitly not production code. No browser-capable governed implementation exists, and FRONT-04 may not reimplement the scheme.",
    frontendBehaviour:
      "No encryption is performed and none is simulated. Cast and public challenge are unavailable in every profile.",
  },
  {
    id: "ballot_submission",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C",
    reason:
      "POST /elections/{election_context_id}/ballots is specification-level only, and PACK-03's castVote is contract-only with no deployed service.",
    frontendBehaviour: "Submission is unavailable; no request is made.",
  },
  {
    id: "submission_recovery",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C",
    reason:
      "GET /elections/{election_context_id}/submissions/{retry_token} is specification-level only.",
    frontendBehaviour:
      "The uncertain-submission state is implemented and reachable, and it offers governed recovery guidance instead of an automatic retry.",
  },
  {
    id: "local_diagnostic_challenge",
    status: "BLOCKED_CRYPTO",
    owner: "PACK-16C / PACK-16D",
    reason:
      "A local diagnostic challenge is a client-local re-encryption check. Without a governed browser cryptographic implementation it cannot be performed, and a simulated one would be the fake the specification warns about.",
    frontendBehaviour:
      "The action is named and explained but unavailable; it is never presented as performed.",
  },
  {
    id: "public_evidentiary_challenge",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C",
    reason:
      "POST /elections/{election_context_id}/public-challenges is specification-level only, and the ballot cryptography it requires is blocked.",
    frontendBehaviour:
      "The action is named, distinguished from the local check and from the final cast, and unavailable.",
  },
  {
    id: "receipt_presentation",
    status: "LIMITED",
    owner: "FRONT-04",
    reason:
      "The receipt renderer and its minimisation rules are implemented and tested, but no accepted runtime returns a receipt, so no real receipt is ever presented.",
    frontendBehaviour:
      "The surface renders the permitted fields only, and in production has nothing to render.",
  },
  {
    id: "receipt_verification",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C / PACK-17",
    reason:
      "GET /elections/{election_context_id}/receipts/{confirmation_code} is specification-level only.",
    frontendBehaviour:
      "The confirmation-code entry path exists, is keyboard-operable and accessible, and returns controlled unavailability.",
  },
  {
    id: "recorded_as_cast_verification",
    status: "BLOCKED_RUNTIME_CONTRACT",
    owner: "PACK-16C / PACK-17",
    reason:
      "Recorded-as-cast verification runs against a separate verification origin whose operational owner is PACK-17. PACK-17 is not started and its documents are absent from the canonical tree.",
    frontendBehaviour:
      "Unavailable; the surface states the publication position honestly and never claims a lookup succeeded.",
  },
  {
    id: "accessibility_assistance",
    status: "AVAILABLE_ACCEPTED_RUNTIME",
    owner: "FRONT-04",
    reason:
      "Assistance is entirely client-side presentation help and requires no external contract.",
    frontendBehaviour:
      "Available to both roles, and structurally unable to read or change selections.",
  },
  {
    id: "governed_fallback",
    status: "AVAILABLE_ACCEPTED_RUNTIME",
    owner: "FRONT-04",
    reason:
      "The fallback is static governed text naming the offline path; it requires no external contract.",
    frontendBehaviour: "Always reachable from every failure state.",
  },
] as const);

export function capability(id: CapabilityId): CapabilityRecord {
  const found = WS03_CAPABILITIES.find((record) => record.id === id);
  if (!found) throw new Error(`unknown capability: ${id}`);
  return found;
}

export function capabilityStatus(id: CapabilityId): CapabilityStatus {
  return capability(id).status;
}

/** No capability that is not an accepted runtime may be executed. */
export function capabilityExecutable(id: CapabilityId): boolean {
  return capabilityStatus(id) === "AVAILABLE_ACCEPTED_RUNTIME";
}

export const BALLOT_CRYPTO_RUNTIME = "BLOCKED" as const;
