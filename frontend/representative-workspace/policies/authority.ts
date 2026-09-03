/**
 * Authority, mandate scope and the prohibition on a universal mode.
 *
 * The governing rule is that a frontend role guard is UX and nothing more.
 * `FRONT-02-SPECIFICATION.md` §4 excludes office/mandate authority from
 * frontend scope entirely, and PACK-09's schema note states the principle this
 * module encodes: "a mandate is an ENUMERATED SET OF AUTHORITIES, not a role
 * name … a role name is not proof of authority."
 *
 * So nothing here decides anything. These functions decide what the interface
 * may *offer*; the server decides what happens, and its refusal is authority.
 */

export const WS04_ROLES = Object.freeze([
  "representative",
  "mandate_staff",
  "publication_reviewer",
  "conflict_officer",
] as const);

export type Ws04Role = (typeof WS04_ROLES)[number];

export const PRIMARY_ROLES = Object.freeze([
  "representative",
  "mandate_staff",
] as const);

export const SECONDARY_ROLES = Object.freeze([
  "publication_reviewer",
  "conflict_officer",
] as const);

/**
 * Role names that must never exist. A build that introduces one of these has
 * created the universal mode the stage contract forbids, and a gate reads this
 * list.
 */
export const FORBIDDEN_UNIVERSAL_ROLES = Object.freeze([
  "super_admin",
  "superadmin",
  "representative_all",
  "all_mandates",
  "cross_mandate",
  "global_admin",
  "system_admin",
  "root",
  "impersonate",
  "debug_bypass",
] as const);

export function isForbiddenUniversalRole(value: string): boolean {
  return (FORBIDDEN_UNIVERSAL_ROLES as readonly string[]).includes(
    value.toLowerCase(),
  );
}

/** No role, flag or build mode grants authority across mandates. */
export function crossMandateAccessAvailableFor(role: string): false {
  void role;
  return false;
}

/** The authority a consequential action requires, as a value the server checks. */
export const AUTHORITY_REQUIREMENTS = Object.freeze([
  "none",
  "mandate_member",
  "mandate_representative",
  "mandate_staff_assigned",
  "publication_reviewer",
  "conflict_officer",
] as const);

export type AuthorityRequirement = (typeof AUTHORITY_REQUIREMENTS)[number];

/** Assurance the session must carry. Step-up is required for high impact. */
export const ASSURANCE_LEVELS = Object.freeze([
  "none",
  "standard",
  "stepped_up",
] as const);

export type AssuranceLevel = (typeof ASSURANCE_LEVELS)[number];

/**
 * The impact classes. `high` requires step-up; `consequential` additionally
 * requires commit-time revalidation, because authority can change between
 * opening a form and submitting it.
 */
export const ACTION_IMPACTS = Object.freeze([
  "read",
  "low",
  "high",
  "consequential",
] as const);

export type ActionImpact = (typeof ACTION_IMPACTS)[number];

export function stepUpRequired(impact: ActionImpact): boolean {
  return impact === "high" || impact === "consequential";
}

export function commitTimeRevalidationRequired(impact: ActionImpact): boolean {
  return impact === "consequential";
}

/**
 * Whether the interface may *offer* an action. This is presentation only: a
 * true answer means the control is shown enabled, never that the action will
 * succeed. Hiding a control is not authorization and this function is not a
 * security boundary; `runtime/` refuses everything regardless.
 */
export function mayOfferAction(input: {
  readonly role: Ws04Role | null;
  readonly required: AuthorityRequirement;
  readonly assurance: AssuranceLevel;
  readonly impact: ActionImpact;
  readonly inScope: boolean;
  readonly conflictRestricted: boolean;
  readonly authorityActive: boolean;
}): boolean {
  if (!input.authorityActive) return false;
  if (!input.inScope) return false;
  if (input.conflictRestricted) return false;
  if (input.role === null) return false;
  if (stepUpRequired(input.impact) && input.assurance !== "stepped_up") {
    return false;
  }
  switch (input.required) {
    case "none":
      return true;
    case "mandate_member":
      return true;
    case "mandate_representative":
      return input.role === "representative";
    case "mandate_staff_assigned":
      return input.role === "representative" || input.role === "mandate_staff";
    case "publication_reviewer":
      return input.role === "publication_reviewer";
    case "conflict_officer":
      return input.role === "conflict_officer";
    default:
      return false;
  }
}

/**
 * The conflict officer is a secondary role, not a representative admin. It may
 * act on conflict records and may not browse case content.
 */
export const CONFLICT_OFFICER_PERMITTED = Object.freeze([
  "view_conflict_register_entry",
  "record_conflict_assessment_proposal",
  "request_recusal_review",
] as const);

export const CONFLICT_OFFICER_FORBIDDEN = Object.freeze([
  "browse_case_content",
  "read_case_body",
  "read_correspondence",
  "reassign_case",
  "triage_case",
  "submit_position",
  "submit_declaration",
  "propose_publication",
  "approve_publication",
  "remove_own_conflict_flag",
  "cross_mandate_search",
] as const);

export function conflictOfficerMay(capability: string): boolean {
  return (CONFLICT_OFFICER_PERMITTED as readonly string[]).includes(capability);
}

/** A subject may never clear their own conflict restriction. */
export function maySelfClearConflict(role: Ws04Role): false {
  void role;
  return false;
}
