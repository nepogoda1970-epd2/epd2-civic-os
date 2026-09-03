/**
 * WS-04 domain types.
 *
 * Pure: no React, no I/O, no transport. The separation is a stage-contract
 * requirement and the validator asserts it.
 */

import type {
  AssuranceLevel,
  AuthorityRequirement,
  ActionImpact,
  Ws04Role,
} from "../policies/authority";
import type { PublicationState } from "../policies/boundaries";

/** The controlled capability vocabulary of the FRONT-05 working contract. */
export const CAPABILITY_STATUSES = Object.freeze([
  "SUPPORTED_REAL_PATH",
  "SUPPORTED_WITH_DECLARED_LIMITATION",
  "BLOCKED_BY_DEPENDENCY",
  "UNSUPPORTED",
] as const);

export type CapabilityStatus = (typeof CAPABILITY_STATUSES)[number];

export function capabilityIsExecutable(status: CapabilityStatus): boolean {
  return status === "SUPPORTED_REAL_PATH";
}

/**
 * Session states. Unlike WS-03, this workspace holds an identity session — so
 * the interesting states are the ones where it stops being sufficient.
 */
export const SESSION_STATES = Object.freeze([
  "anonymous",
  "authenticated",
  "stepped_up",
  "step_up_required",
  "expired",
  "revoked",
  "scope_changed",
  "authority_suspended",
  "authority_expired",
] as const);

export type SessionState = (typeof SESSION_STATES)[number];

export const SESSION_STATES_PERMITTING_WORK = Object.freeze([
  "authenticated",
  "stepped_up",
] as const);

export function sessionPermitsWork(state: SessionState): boolean {
  return (SESSION_STATES_PERMITTING_WORK as readonly string[]).includes(state);
}

/**
 * The mandate scope. Every route and action binds to exactly one, and there is
 * no value meaning "all".
 */
export type MandateScope = {
  readonly mandateId: string;
  readonly organizationId: string;
  readonly label: string;
  readonly level: string;
  readonly authorityActive: boolean;
  readonly authorityExpiresAt?: string;
};

/**
 * The session projection the interface is allowed to see. Deliberately minimal:
 * no account reference, no member number, no person identifier.
 */
export type MandateSession = {
  readonly state: SessionState;
  readonly role: Ws04Role | null;
  readonly assurance: AssuranceLevel;
  readonly scope: MandateScope | null;
  readonly displayName: string | null;
  readonly conflictRestricted: boolean;
};

/** A refusal that is safe to render. */
export type SafeRefusal = {
  readonly kind:
    | "unauthenticated"
    | "forbidden"
    | "step_up_required"
    | "scope_mismatch"
    | "conflict_restricted"
    | "authority_revoked"
    | "authority_expired"
    | "not_found"
    | "conflict_stale"
    | "unavailable"
    | "blocked"
    | "rate_limited"
    | "maintenance";
  readonly reasonCode: string;
  readonly safeMessage: string;
  readonly committed: "committed" | "not_committed" | "unknown";
  readonly nextSafeAction: string;
  /** True when the refusal must not disclose whether the resource exists. */
  readonly nonDisclosing: boolean;
};

export type Result<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: SafeRefusal };

/** Case intake states. Taken from the target model, not invented per surface. */
export const CASE_STATES = Object.freeze([
  "new",
  "assigned",
  "triaged",
  "awaiting_response",
  "closed",
  "archived",
  "unavailable",
] as const);

export type CaseState = (typeof CASE_STATES)[number];

export type CaseSummary = {
  readonly caseId: string;
  readonly reference: string;
  readonly subject: string;
  readonly state: CaseState;
  readonly receivedAt: string;
  readonly mandateId: string;
  readonly assigneeLabel: string | null;
  readonly conflictRestricted: boolean;
};

/** Case detail carries content, so it is the most constrained type here. */
export type CaseDetail = CaseSummary & {
  readonly summaryText: string;
  readonly provenance: string;
  readonly version: string;
};

/** Position workflow states. A local draft is never public truth. */
export const POSITION_STATES = Object.freeze([
  "draft",
  "submitted_internal",
  "proposed_for_publication",
  "public_approved_rendition",
  "superseded",
] as const);

export type PositionState = (typeof POSITION_STATES)[number];

export type PositionRecord = {
  readonly positionId: string;
  readonly title: string;
  readonly state: PositionState;
  readonly version: string;
  readonly mandateId: string;
  readonly updatedAt: string;
  readonly publicationState: PublicationState | null;
};

/**
 * A deviation record: a representative's stated divergence from a governed
 * democratic decision, with provenance. It is a record, not a state transition —
 * the referenced decision is unaffected by it.
 */
export type DeviationRecord = {
  readonly deviationId: string;
  readonly issue: string;
  readonly representativePosition: string;
  readonly referencedDecision: string | null;
  readonly explanation: string;
  readonly recordedAt: string;
  readonly version: string;
  readonly supersedes: string | null;
  readonly publicationState: PublicationState | null;
};

export const DECLARATION_KINDS = Object.freeze([
  "meeting",
  "declaration",
  "disclosure",
] as const);

export type DeclarationKind = (typeof DECLARATION_KINDS)[number];

export type DeclarationRecord = {
  readonly declarationId: string;
  readonly kind: DeclarationKind;
  readonly subject: string;
  readonly occurredAt: string;
  readonly submittedAt: string | null;
  readonly state: "draft" | "submitted" | "accepted" | "returned";
};

export type PublicationProposal = {
  readonly proposalId: string;
  readonly sourceKind: "position" | "deviation" | "declaration";
  readonly sourceId: string;
  readonly state: PublicationState;
  readonly decidedBy: string | null;
  readonly publicRenditionRef: string | null;
};

export type ConflictRestriction = {
  readonly restrictionId: string;
  readonly scopeLabel: string;
  readonly active: boolean;
  readonly recordedAt: string;
  /** Deliberately coarse: the reason is not exposed in protected detail. */
  readonly safeReason: string;
  readonly mayBeClearedBySubject: false;
};

/** An action descriptor the interface uses to decide what it may offer. */
export type ActionDescriptor = {
  readonly actionId: string;
  readonly label: string;
  readonly required: AuthorityRequirement;
  readonly impact: ActionImpact;
  readonly capability: string;
};
