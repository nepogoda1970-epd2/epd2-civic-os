/**
 * The WS-04 runtime ports.
 *
 * A port is a shape the interface may talk to. Declaring one is not a claim
 * that a route exists: at this baseline every port is satisfied in production
 * by a controlled unavailability, because no accepted executable contract
 * exists behind any of them. The names come from the FRONT-05 working stage
 * contract; the fail-closed answers come from the accepted API and PACK state
 * recorded in `domain/capabilities.ts`.
 *
 * Note what the signatures do *not* contain. There is no port that takes a
 * list of mandate identifiers, no port that returns an approval, no port that
 * mutates a register, and no port that reaches the voting domain. Those are
 * prohibitions, so they are enforced by the absence of a callable shape rather
 * than by a check inside one.
 */

import type { ScopeBound } from "../domain/scope";
import type {
  CaseDetail,
  CaseSummary,
  ConflictRestriction,
  DeclarationRecord,
  DeviationRecord,
  MandateScope,
  MandateSession,
  PositionRecord,
  PublicationProposal,
  Result,
} from "../domain/types";
import type { DeclarationDraft } from "../domain/declaration";
import type { DeviationDraft } from "../domain/deviation";

export type RuntimeProfile = "production" | "governed_test";

/** Identity and mandate binding. */
export type MandateSessionPort = {
  readonly current: (signal?: AbortSignal) => Promise<Result<MandateSession>>;
  /** Observe a step-up outcome. The client never decides that one occurred. */
  readonly observeStepUp: (
    signal?: AbortSignal,
  ) => Promise<Result<MandateSession>>;
  readonly signOut: () => Promise<Result<null>>;
};

export type MandateScopePort = {
  /** Exactly one scope. There is no `list` operation, deliberately. */
  readonly resolve: (signal?: AbortSignal) => Promise<Result<MandateScope>>;
};

/** Case desk. Every read is scope-bound at the type level. */
export type CaseDeskPort = {
  readonly list: (
    scope: ScopeBound<{ readonly state: string | null; readonly page: number }>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly CaseSummary[]>>;
  readonly read: (
    scope: ScopeBound<{ readonly caseId: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<CaseDetail>>;
  /**
   * Search is scope-bound and server-side. There is no variant that omits the
   * scope, so an unscoped query cannot be expressed.
   */
  readonly search: (
    scope: ScopeBound<{ readonly query: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly CaseSummary[]>>;
  /**
   * A transition carries a version precondition. `Result<never>` records that
   * no success value exists at this baseline: a caller cannot destructure a
   * pretend outcome.
   */
  readonly transition: (
    scope: ScopeBound<{
      readonly caseId: string;
      readonly event: string;
      readonly ifVersion: string;
    }>,
  ) => Promise<Result<never>>;
  /** Read-back after an uncertain transition. Never an automatic retry. */
  readonly reread: (
    scope: ScopeBound<{ readonly caseId: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<CaseDetail>>;
};

export type PositionPort = {
  readonly list: (
    scope: ScopeBound<Record<string, never>>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly PositionRecord[]>>;
  readonly save: (
    scope: ScopeBound<{
      readonly positionId: string | null;
      readonly body: string;
    }>,
  ) => Promise<Result<never>>;
  readonly submitInternal: (
    scope: ScopeBound<{
      readonly positionId: string;
      readonly ifVersion: string;
    }>,
  ) => Promise<Result<never>>;
};

export type DeviationPort = {
  readonly list: (
    scope: ScopeBound<Record<string, never>>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly DeviationRecord[]>>;
  readonly record: (
    scope: ScopeBound<{ readonly draft: DeviationDraft }>,
  ) => Promise<Result<never>>;
  /** Resolve a referenced governed decision. Blocked; references stay unverified. */
  readonly resolveDecision: (
    reference: string,
    signal?: AbortSignal,
  ) => Promise<Result<never>>;
};

export type DeclarationPort = {
  readonly list: (
    scope: ScopeBound<Record<string, never>>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly DeclarationRecord[]>>;
  readonly submit: (
    scope: ScopeBound<{ readonly draft: DeclarationDraft }>,
  ) => Promise<Result<never>>;
};

/**
 * Publication. There is a `propose` and there is no `approve`. The absence is
 * the control: no amount of client-side state can reach an approval, because
 * no operation exists that would return one.
 */
export type PublicationPort = {
  readonly propose: (
    scope: ScopeBound<{
      readonly sourceKind: PublicationProposal["sourceKind"];
      readonly sourceId: string;
    }>,
  ) => Promise<Result<never>>;
  readonly withdraw: (
    scope: ScopeBound<{ readonly proposalId: string }>,
  ) => Promise<Result<never>>;
  readonly observe: (
    scope: ScopeBound<{ readonly proposalId: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<PublicationProposal>>;
};

export type ConflictPort = {
  readonly restrictions: (
    scope: ScopeBound<Record<string, never>>,
    signal?: AbortSignal,
  ) => Promise<Result<readonly ConflictRestriction[]>>;
  /** Proposal only, by the conflict officer. No self-clearing operation exists. */
  readonly recordAssessmentProposal: (
    scope: ScopeBound<{
      readonly restrictionId: string;
      readonly note: string;
    }>,
  ) => Promise<Result<never>>;
};

/** Read-only reference over protected registers. No mutation shape exists. */
export type RegistryReferencePort = {
  readonly read: (
    scope: ScopeBound<{ readonly registry: string; readonly key: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<never>>;
};

/** Display of an eligibility decision made elsewhere. No decision operation. */
export type EligibilityDisplayPort = {
  readonly observe: (
    scope: ScopeBound<{ readonly subjectRef: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<never>>;
};

export type AuditPort = {
  readonly read: (
    scope: ScopeBound<{ readonly since: string }>,
    signal?: AbortSignal,
  ) => Promise<Result<never>>;
};

export type RepresentativeRuntime = {
  readonly profile: RuntimeProfile;
  readonly session: MandateSessionPort;
  readonly scope: MandateScopePort;
  readonly cases: CaseDeskPort;
  readonly positions: PositionPort;
  readonly deviations: DeviationPort;
  readonly declarations: DeclarationPort;
  readonly publication: PublicationPort;
  readonly conflict: ConflictPort;
  readonly registry: RegistryReferencePort;
  readonly eligibility: EligibilityDisplayPort;
  readonly audit: AuditPort;
};
