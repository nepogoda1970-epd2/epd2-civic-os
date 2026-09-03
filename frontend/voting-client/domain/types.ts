/**
 * WS-03 domain types.
 *
 * This module is pure: it imports no React, performs no I/O and knows nothing
 * about a transport.  The separation is a FRONT-04 requirement and is asserted
 * by the static validator.
 */

import type { VotingRole } from "../policies/supportRole";

/** The controlled capability vocabulary of section 27 of the stage contract. */
export const CAPABILITY_STATUSES = Object.freeze([
  "AVAILABLE_ACCEPTED_RUNTIME",
  "AVAILABLE_REFERENCE_ONLY",
  "LIMITED",
  "BLOCKED_RUNTIME_CONTRACT",
  "BLOCKED_CRYPTO",
  "BLOCKED_INFRA",
  "BLOCKED_LEGAL",
  "BLOCKED_SECURITY_REVIEW",
  "PLANNED",
] as const);

export type CapabilityStatus = (typeof CAPABILITY_STATUSES)[number];

export function capabilityIsExecutable(status: CapabilityStatus): boolean {
  return status === "AVAILABLE_ACCEPTED_RUNTIME";
}

/**
 * The journey states.  `submitted` and `submission_uncertain` are distinct on
 * purpose: the second is the state in which the client knows only that it does
 * not know, and it must never be collapsed into either success or failure.
 */
export const JOURNEY_STATES = Object.freeze([
  "not_started",
  "credential_accepted",
  "prepared",
  "reviewed",
  "submitted",
  "submission_uncertain",
  "accepted",
  "receipt_available",
  "verified",
  "failed",
  "cancelled",
  "expired",
] as const);

export type JourneyState = (typeof JOURNEY_STATES)[number];

/** States in which the voter's ballot is known to have been committed. */
export const COMMITTED_STATES = Object.freeze([
  "accepted",
  "receipt_available",
  "verified",
] as const);

/** States in which nothing was committed and the entitlement is intact. */
export const UNCOMMITTED_STATES = Object.freeze([
  "not_started",
  "credential_accepted",
  "prepared",
  "reviewed",
  "cancelled",
] as const);

export type CommitKnowledge = "committed" | "not_committed" | "unknown";

export function commitKnowledge(state: JourneyState): CommitKnowledge {
  if ((COMMITTED_STATES as readonly string[]).includes(state))
    return "committed";
  if ((UNCOMMITTED_STATES as readonly string[]).includes(state)) {
    return "not_committed";
  }
  // submitted, submission_uncertain, failed and expired are deliberately
  // "unknown" until an authoritative answer exists.  `failed` is unknown
  // rather than not_committed because a failure observed in the browser does
  // not prove what the server did.
  return "unknown";
}

/** A refusal that is safe to render.  It carries no detail that discloses. */
export type SafeRefusal = {
  readonly kind:
    | "unavailable"
    | "blocked"
    | "refused"
    | "invalid"
    | "expired"
    | "conflict"
    | "uncertain"
    | "not_found";
  readonly reasonCode: string;
  readonly safeMessage: string;
  readonly commitKnowledge: CommitKnowledge;
  readonly entitlementKnownIntact: boolean;
  readonly nextSafeAction: string;
};

export type Result<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: SafeRefusal };

/** The voting-scoped context.  Note the absence of any voter identifier. */
export type VotingContext = {
  readonly votingContextId: string;
  readonly audienceOrigin: string;
  readonly purpose: "voting_entry";
  readonly expiresAt: string;
  readonly role: VotingRole;
};

export type ElectionContext = {
  readonly electionContextReference: string;
  readonly title: string;
  readonly activationStatus:
    "PLANNED" | "PROTOTYPE_NOT_ACTIVATED" | "LEGALLY_INACTIVE";
  readonly manifestDigest?: string;
  readonly parameterSetId?: string;
  readonly protocolProfileId?: string;
};

export type BallotOption = {
  readonly optionId: string;
  readonly label: string;
  readonly description?: string;
};

export type BallotContest = {
  readonly contestId: string;
  readonly title: string;
  readonly instruction: string;
  readonly selectionLimit: number;
  readonly options: readonly BallotOption[];
};

export type BallotStyle = {
  readonly ballotStyleId: string;
  readonly schemaVersion: string;
  readonly contests: readonly BallotContest[];
};

/** A voter's selections.  Held in memory, never serialised to storage. */
export type BallotSelection = {
  readonly contestId: string;
  readonly optionIds: readonly string[];
};

export type BallotDraft = {
  readonly ballotStyleId: string;
  readonly selections: readonly BallotSelection[];
};

/** The submission classes of the PACK-16C two-tier model. */
export const SUBMISSION_CLASSES = Object.freeze([
  "local_diagnostic_challenge",
  "public_evidentiary_challenge",
  "final_cast",
] as const);

export type SubmissionClass = (typeof SUBMISSION_CLASSES)[number];

export const NETWORK_SUBMISSION_CLASSES = Object.freeze([
  "public_evidentiary_challenge",
  "final_cast",
] as const);

export function submissionClassCreatesNetworkArtefact(
  submissionClass: SubmissionClass,
): boolean {
  return (NETWORK_SUBMISSION_CLASSES as readonly string[]).includes(
    submissionClass,
  );
}

export const PUBLICATION_STATUSES = Object.freeze([
  "ACCEPTED_PENDING_BATCH_COMMITMENT",
  "COMMITTED",
  "PUBLISHED_AFTER_CLOSURE",
  "PUBLICATION_DISPUTED",
] as const);

export type PublicationStatus = (typeof PUBLICATION_STATUSES)[number];

/**
 * The receipt, restricted to the seven fields PACK-16C permits plus the
 * explicit not-counted marker a public challenge receipt carries.  The type is
 * closed: a field that is not here cannot be added by a caller.
 */
export type Receipt = {
  readonly electionContextReference: string;
  readonly confirmationCode: string;
  readonly boardCheckpointReference: string;
  readonly sealedBatchReference: string;
  readonly publicationStatus: PublicationStatus;
  readonly verificationInstructions: string;
  readonly receiptSchemaVersion: string;
  readonly countingStatus: "COUNTED_IF_PUBLISHED" | "NOT_COUNTED";
};
