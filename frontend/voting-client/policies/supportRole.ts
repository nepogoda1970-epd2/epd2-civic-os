/**
 * Accessibility Support Operator.
 *
 * The role exists so that a voter who needs help can be helped.  It is not a
 * second voter and it is not a privileged console.  Everything the operator
 * may do is listed; everything else is refused by a total function rather than
 * by the absence of a feature.
 */

export const VOTING_ROLES = Object.freeze([
  "eligible_voter",
  "accessibility_support_operator",
] as const);

export type VotingRole = (typeof VOTING_ROLES)[number];

/**
 * Capabilities the support operator may exercise.  All of them are about the
 * presentation of the page and none of them touch the ballot.
 */
export const SUPPORT_OPERATOR_PERMITTED_CAPABILITIES = Object.freeze([
  "explain_page_structure",
  "explain_keyboard_operation",
  "explain_current_step",
  "read_public_help_text",
  "offer_restart_path",
  "offer_alternative_channel_information",
] as const);

/**
 * Capabilities the support operator is technically prevented from exercising.
 * These are the ones that would turn assistance into participation.
 */
export const SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES = Object.freeze([
  "read_voter_selections",
  "set_voter_selections",
  "clear_voter_selections",
  "export_ballot_content",
  "obtain_ballot_identifier",
  "obtain_confirmation_code",
  "correlate_voter_and_ballot",
  "confirm_cast_on_behalf_of_voter",
  "bypass_cast_confirmation",
  "obtain_tally_information",
  "open_privileged_console",
] as const);

export type SupportOperatorCapability =
  | (typeof SUPPORT_OPERATOR_PERMITTED_CAPABILITIES)[number]
  | (typeof SUPPORT_OPERATOR_FORBIDDEN_CAPABILITIES)[number];

export function supportOperatorMay(capability: string): boolean {
  return (
    SUPPORT_OPERATOR_PERMITTED_CAPABILITIES as readonly string[]
  ).includes(capability);
}

/**
 * Only the voter's own session may render selections.  The check is on the
 * role, not on a permission that a deployment could grant.
 */
export function mayViewBallotSelections(role: VotingRole): boolean {
  return role === "eligible_voter";
}

export function mayChangeBallotSelections(role: VotingRole): boolean {
  return role === "eligible_voter";
}

export function mayConfirmConsequentialAction(role: VotingRole): boolean {
  return role === "eligible_voter";
}
