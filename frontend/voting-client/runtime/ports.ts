/**
 * The WS-03 runtime ports.
 *
 * A port is a shape the interface can talk to.  It is *not* a claim that a
 * route exists: every one of these is satisfied in production by a controlled
 * unavailability, because no accepted executable contract exists behind any of
 * them.  The names come from the stage contract; the fail-closed answers come
 * from the accepted API and PACK state.
 */

import type {
  BallotDraft,
  BallotStyle,
  ElectionContext,
  Receipt,
  Result,
  SubmissionClass,
  VotingContext,
} from "../domain/types";

export type RuntimeProfile = "production" | "governed_test";

export type VotingHandoffPort = {
  /** Present a handoff artifact received through a permitted channel. */
  readonly consume: (presented: unknown) => Promise<Result<VotingContext>>;
};

export type ElectionManifestPort = {
  readonly read: (
    context: VotingContext,
    signal?: AbortSignal,
  ) => Promise<Result<ElectionContext>>;
};

export type BallotStylePort = {
  readonly read: (
    context: VotingContext,
    signal?: AbortSignal,
  ) => Promise<Result<BallotStyle>>;
};

export type VotingCryptoPort = {
  /**
   * Produce the encrypted ballot envelope.  There is deliberately no
   * fallback implementation: if this port is unavailable, the journey stops.
   */
  readonly prepareEnvelope: (
    context: VotingContext,
    draft: BallotDraft,
  ) => Promise<Result<never>>;
};

export type BallotSubmissionPort = {
  readonly submit: (
    context: VotingContext,
    submissionClass: SubmissionClass,
    retryToken: string,
  ) => Promise<Result<never>>;
  /** Status by retry token — never an automatic resubmission. */
  readonly status: (
    context: VotingContext,
    retryToken: string,
  ) => Promise<Result<never>>;
};

export type ReceiptVerificationPort = {
  readonly readReceipt: (
    confirmationCode: string,
    signal?: AbortSignal,
  ) => Promise<Result<Receipt>>;
  readonly confirmRecordedAsCast: (
    confirmationCode: string,
    signal?: AbortSignal,
  ) => Promise<Result<never>>;
};

export type VotingRuntime = {
  readonly profile: RuntimeProfile;
  readonly handoff: VotingHandoffPort;
  readonly electionManifest: ElectionManifestPort;
  readonly ballotStyle: BallotStylePort;
  readonly crypto: VotingCryptoPort;
  readonly submission: BallotSubmissionPort;
  readonly receipt: ReceiptVerificationPort;
};
