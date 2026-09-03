/**
 * Publication proposals.
 *
 * The one sentence this module exists to make unfalsifiable: a WS-04 proposal
 * is not a publication. The workspace composes a rendition, submits it as a
 * proposal, and stops. Approval belongs to the publication authority, and no
 * code path here can produce an approved state.
 *
 * There is a second, separate honesty problem recorded here rather than hidden:
 * the accepted transparency-service has a single publication state, PUBLISHED,
 * and authorises by a caller-supplied boolean. It has no proposal state. That
 * gap is an open governance item; this module does not close it by inventing a
 * state on the server's behalf.
 */

import {
  isPublicApproved,
  proposalEqualsPublicApproved,
  ws04MayApprovePublication,
  ws04MayOriginate,
  type PublicationState,
} from "../policies/boundaries";
import type {
  ActionDescriptor,
  PublicationProposal,
  SafeRefusal,
} from "./types";

/**
 * Not a gap: a defect.
 *
 * It would be comfortable to record the transparency service's shape as a
 * missing feature and move on. It is not one. A caller-supplied
 * `actor_is_authorized` boolean means the caller declares its own permission and
 * the service accepts the declaration — so the field that looks like an
 * authorization gate is an authorization *claim*, and a claim made by exactly
 * the party the gate exists to constrain.
 *
 * Two consequences bind this module:
 *
 *  1. FRONT-05 never sets, sends, or relies on such a flag. There is no field
 *     for it in any port signature, and no code path that could produce one.
 *  2. The capability stays blocked until a server-authoritative authorization
 *     contract exists. A proposal route appearing while the boolean stayed
 *     would not unblock it, because the route would inherit the same defect.
 *
 * `domain/capabilities.ts` classifies both publication capabilities as
 * `SECURITY_SENSITIVE_BOUNDARY` and asserts at module load that neither can be
 * marked a real path.
 */
export const PUBLICATION_MODEL_GAP = Object.freeze({
  classification: "SECURITY_SENSITIVE_BOUNDARY",
  observed:
    "transparency-service defines a single publication state PUBLISHED and authorises via a caller-supplied actor_is_authorized boolean.",
  securityFinding:
    "A caller-supplied authorization boolean is a self-asserted authorization. Accepting it as sufficient would let a rendition reach publication carrying nothing but the proposer's own claim of being allowed to publish, which is precisely the separation WS-04 exists to preserve.",
  required:
    "a server-authoritative proposal and authorization contract: a proposal state distinct from PUBLISHED, and an approval decided and recorded by an authority other than the proposer.",
  insufficientRemedies: Object.freeze([
    "adding a proposal route while authorization stays caller-supplied",
    "having WS-04 set actor_is_authorized itself",
    "treating a successful call as evidence that authorization occurred",
    "recording the capability as SUPPORTED_WITH_DECLARED_LIMITATION",
  ] as const),
  disposition:
    "OPEN_GOVERNANCE_ITEM / SECURITY-RELEVANT: recorded for the accepting authority. The capability remains BLOCKED_BY_DEPENDENCY, and approval remains UNSUPPORTED for this workspace under every dependency state. FRONT-05 does not define the missing server contract and does not build on the defective one.",
});

/**
 * Total function. No dependency state makes a caller-asserted authorization
 * sufficient, so this answers false unconditionally and is referenced by the
 * publication surface and by the mutation suite.
 */
export function callerAssertedAuthorizationSufficient(): false {
  return false;
}

export type ProposalEvent =
  | { readonly type: "compose" }
  | { readonly type: "submit_proposal" }
  | { readonly type: "withdraw" };

/**
 * The client-side transition table. It contains only the two states WS-04 may
 * originate. `approved_by_publication_authority` is unreachable from every
 * state under every event — a property the mutation suite attacks directly.
 */
const TRANSITIONS: Readonly<
  Record<
    PublicationState,
    Partial<Record<ProposalEvent["type"], PublicationState>>
  >
> = Object.freeze({
  draft: { submit_proposal: "proposal_submitted" },
  proposal_submitted: { withdraw: "draft" },
  returned_for_correction: { compose: "draft" },
  approved_by_publication_authority: {},
  rejected: {},
  superseded: {},
});

export function proposedPublicationState(
  state: PublicationState,
  event: ProposalEvent,
): PublicationState | null {
  const next = TRANSITIONS[state][event.type];
  if (next === undefined) return null;
  // Belt and braces: even if the table above were edited, WS-04 may not
  // originate a state outside its permitted set.
  if (!ws04MayOriginate(next)) return null;
  return next;
}

/** Total function. No argument makes this true. */
export function ws04MayReachApproved(state: PublicationState): false {
  void state;
  void ws04MayApprovePublication();
  void proposalEqualsPublicApproved();
  return false;
}

/**
 * Every proposal must be rendered with an explicit statement of what it is not.
 * The interface is required to display this string alongside any proposal.
 */
export const PROPOSAL_DISCLAIMER =
  "Vorschlag zur Veröffentlichung. Dies ist keine Veröffentlichung und keine Freigabe." as const;

export function publicationLabel(state: PublicationState): string {
  switch (state) {
    case "draft":
      return "Entwurf, nicht eingereicht";
    case "proposal_submitted":
      return "Vorschlag eingereicht, nicht freigegeben";
    case "returned_for_correction":
      return "Zur Überarbeitung zurückgegeben";
    case "approved_by_publication_authority":
      return "Von der Veröffentlichungsstelle freigegeben";
    case "rejected":
      return "Abgelehnt";
    case "superseded":
      return "Ersetzt";
    default:
      return "Unbekannt";
  }
}

/**
 * Whether the interface may present an item as public. Only the authority's
 * approved state qualifies, and only when it was observed rather than derived
 * from this workspace's own submission.
 */
export function mayPresentAsPublic(proposal: PublicationProposal): boolean {
  if (!isPublicApproved(proposal.state)) return false;
  // An approved state with no recorded deciding authority is not trustworthy.
  return proposal.decidedBy !== null && proposal.publicRenditionRef !== null;
}

export const PROPOSAL_BLOCKED: SafeRefusal = Object.freeze({
  kind: "blocked",
  reasonCode: "WS04-PUB-001",
  safeMessage:
    "Vorschläge zur Veröffentlichung können derzeit nicht eingereicht werden.",
  committed: "not_committed",
  nextSafeAction:
    "Der Text bleibt in diesem Fenster erhalten. Die Veröffentlichungsstelle nimmt Vorschläge weiterhin auf dem geregelten Weg entgegen.",
  nonDisclosing: false,
});

export const PUBLICATION_ACTIONS: readonly ActionDescriptor[] = Object.freeze([
  {
    actionId: "publication.propose",
    label: "Veröffentlichung vorschlagen",
    required: "mandate_representative",
    impact: "consequential",
    capability: "publication_proposal_submission",
  },
  {
    actionId: "publication.withdraw",
    label: "Vorschlag zurückziehen",
    required: "mandate_representative",
    impact: "high",
    capability: "publication_proposal_submission",
  },
]);

/**
 * There is deliberately no `publication.approve` descriptor. Its absence is
 * asserted by test: the action register must contain no identifier matching an
 * approval verb.
 */
export const FORBIDDEN_PUBLICATION_ACTION_IDS = Object.freeze([
  "publication.approve",
  "publication.publish",
  "publication.release",
  "publication.force_publish",
  "publication.self_approve",
] as const);

export function actionRegisterClean(): boolean {
  const ids = PUBLICATION_ACTIONS.map((a) => a.actionId);
  return !FORBIDDEN_PUBLICATION_ACTION_IDS.some((f) => ids.includes(f));
}
