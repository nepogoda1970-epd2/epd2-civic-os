/**
 * The four hard prohibitions of WS-04, expressed so they can be tested.
 *
 * A representative workspace is dangerous precisely because it is plausible to
 * put these powers in it. Each one is therefore a named, closed list with a
 * total function that answers `false`, rather than an absent feature that a
 * later change could quietly add.
 */

/** 1. WS-04 may propose a rendition. It may never publish one. */
export const PUBLICATION_STATES = Object.freeze([
  "draft",
  "proposal_submitted",
  "returned_for_correction",
  "approved_by_publication_authority",
  "rejected",
  "superseded",
] as const);

export type PublicationState = (typeof PUBLICATION_STATES)[number];

/** States this workspace may itself reach. Approval is not among them. */
export const STATES_WS04_MAY_ORIGINATE = Object.freeze([
  "draft",
  "proposal_submitted",
] as const);

/** States that may only arrive from the publication source of truth. */
export const STATES_ONLY_PUBLICATION_AUTHORITY_MAY_SET = Object.freeze([
  "returned_for_correction",
  "approved_by_publication_authority",
  "rejected",
  "superseded",
] as const);

export function ws04MayOriginate(state: PublicationState): boolean {
  return (STATES_WS04_MAY_ORIGINATE as readonly string[]).includes(state);
}

export function ws04MayApprovePublication(): false {
  return false;
}

/** A proposal is never public-approved material. */
export function isPublicApproved(state: PublicationState): boolean {
  return state === "approved_by_publication_authority";
}

export function proposalEqualsPublicApproved(): false {
  return false;
}

/** 2. No registry custody. */
export const PROTECTED_REGISTRIES = Object.freeze([
  "membership_register",
  "voters_register",
  "candidate_register",
  "organization_register",
  "office_register",
  "mandate_register",
  "credential_register",
  "public_ledger",
  "transparency_ledger",
] as const);

export const REGISTRY_ACTIONS_FORBIDDEN = Object.freeze([
  "create_registry_entry",
  "update_registry_entry",
  "delete_registry_entry",
  "correct_registry_entry_in_place",
  "assume_registry_custody",
] as const);

export function mayMutateRegistry(registry: string, action: string): false {
  void registry;
  void action;
  return false;
}

/** Reading an authoritative read model, or submitting a request, is permitted. */
export const REGISTRY_INTERACTIONS_PERMITTED = Object.freeze([
  "read_authorized_projection",
  "submit_correction_request",
  "submit_proposal",
] as const);

export function registryInteractionPermitted(action: string): boolean {
  return (REGISTRY_INTERACTIONS_PERMITTED as readonly string[]).includes(
    action,
  );
}

/** 3. No eligibility decisions. */
export const ELIGIBILITY_DECISIONS = Object.freeze([
  "membership_eligibility",
  "voter_eligibility",
  "candidate_eligibility",
  "legal_competence",
  "credential_issuance",
  "mandate_validity",
] as const);

export function mayDecideEligibility(kind: string): false {
  void kind;
  return false;
}

/** Displaying an eligibility status read from an authoritative source is fine. */
export const ELIGIBILITY_DISPLAY = Object.freeze({
  permittedWhenReadFromAuthoritativeSource: true,
  permittedWhenDerivedInClient: false,
} as const);

/** 4. No voting-domain access. */
export const VOTING_DOMAIN_PROHIBITIONS = Object.freeze([
  "ballot_content",
  "ballot_style",
  "voter_identity_lookup",
  "voter_register_read",
  "intermediate_tally",
  "final_tally_before_publication",
  "voting_admin_function",
  "voting_session_reuse",
  "voting_token_reuse",
  "voting_handoff_consumption",
  "cross_domain_voter_correlation",
  "confirmation_code_lookup",
] as const);

export function votingDomainAccessAvailableFor(role: string): false {
  void role;
  return false;
}

/** The only permitted relationship to the voting domain is a governed handoff. */
export const VOTING_RELATIONSHIP = Object.freeze({
  governedHandoffOnly: true,
  directAccess: false,
  sessionSharing: false,
  identityBridge: false,
} as const);

/** 5. No client-side authoritative decision, on any of these subjects. */
export const NON_AUTHORITATIVE_IN_CLIENT = Object.freeze([
  "authority",
  "conflict_status",
  "publication_approval",
  "case_ownership",
  "mandate_status",
  "legal_effect",
  "voting_status",
  "eligibility",
] as const);

export function clientMayDecide(subject: string): false {
  void subject;
  return false;
}
