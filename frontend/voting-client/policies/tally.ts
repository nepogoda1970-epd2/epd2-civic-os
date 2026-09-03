/**
 * No intermediate tally.
 *
 * The rule is not "hide the tally from this role" — the functionality must not
 * exist.  This module names the quantities the Voting Client may never hold or
 * render, so a component that acquires one fails a test rather than a review.
 */

export const PROHIBITED_TALLY_QUANTITIES = Object.freeze([
  "partial_result",
  "current_distribution",
  "option_ranking",
  "candidate_ranking",
  "accepted_ballot_count",
  "submitted_ballot_count",
  "turnout",
  "turnout_percentage",
  "remaining_voter_count",
  "board_occupancy",
  "batch_occupancy",
  "leaf_index",
  "board_sequence",
  "position_among_ballots",
  "remaining_cast_entitlement",
  "remaining_challenge_entitlement",
  "progress_from_accepted_ballots",
] as const);

export type ProhibitedTallyQuantity =
  (typeof PROHIBITED_TALLY_QUANTITIES)[number];

export function isProhibitedTallyQuantity(name: string): boolean {
  return (PROHIBITED_TALLY_QUANTITIES as readonly string[]).includes(name);
}

export function findProhibitedTallyQuantities(value: unknown): string[] {
  const found = new Set<string>();
  const seen = new Set<unknown>();
  const walk = (node: unknown): void => {
    if (node === null || typeof node !== "object") return;
    if (seen.has(node)) return;
    seen.add(node);
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    for (const [key, child] of Object.entries(
      node as Record<string, unknown>,
    )) {
      if (isProhibitedTallyQuantity(key)) found.add(key);
      walk(child);
    }
  };
  walk(value);
  return [...found].sort();
}

/** No role, permission or build flag makes an intermediate tally available. */
export function intermediateTallyAvailableFor(role: string): false {
  void role;
  return false;
}
