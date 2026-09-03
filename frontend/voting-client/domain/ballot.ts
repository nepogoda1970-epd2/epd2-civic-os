/**
 * Ballot preparation.
 *
 * Selections live in memory for the life of a page and nowhere else.  This
 * module contains the selection algebra; the React layer holds it in state and
 * the runtime layer never sees it, because there is no accepted contract that
 * could receive it.
 */

import { findForbiddenIdentityFields } from "../policies/identity";
import { findProhibitedTallyQuantities } from "../policies/tally";
import type {
  BallotContest,
  BallotDraft,
  BallotSelection,
  BallotStyle,
} from "./types";

export const BALLOT_STATE_PERSISTENCE = Object.freeze({
  localStorage: false,
  sessionStorage: false,
  indexedDB: false,
  cookie: false,
  cacheStorage: false,
  serviceWorker: false,
  url: false,
  history: false,
  pageTitle: false,
  telemetry: false,
  errorReport: false,
} as const);

export function emptyDraft(style: BallotStyle): BallotDraft {
  return {
    ballotStyleId: style.ballotStyleId,
    selections: style.contests.map((contest) => ({
      contestId: contest.contestId,
      optionIds: [],
    })),
  };
}

function contestById(
  style: BallotStyle,
  contestId: string,
): BallotContest | undefined {
  return style.contests.find((contest) => contest.contestId === contestId);
}

/**
 * Toggle one option.  A selection beyond the contest's limit is refused rather
 * than silently displacing an earlier one, because silently changing a voter's
 * ballot is exactly the behaviour the review step exists to catch.
 */
export function toggleOption(
  style: BallotStyle,
  draft: BallotDraft,
  contestId: string,
  optionId: string,
): BallotDraft {
  const contest = contestById(style, contestId);
  if (!contest) return draft;
  if (!contest.options.some((option) => option.optionId === optionId)) {
    return draft;
  }
  return {
    ballotStyleId: draft.ballotStyleId,
    selections: draft.selections.map((selection) => {
      if (selection.contestId !== contestId) return selection;
      const selected = selection.optionIds.includes(optionId);
      if (selected) {
        return {
          contestId,
          optionIds: selection.optionIds.filter((id) => id !== optionId),
        };
      }
      if (selection.optionIds.length >= contest.selectionLimit) {
        return contest.selectionLimit === 1
          ? { contestId, optionIds: [optionId] }
          : selection;
      }
      return { contestId, optionIds: [...selection.optionIds, optionId] };
    }),
  };
}

export function clearContest(
  draft: BallotDraft,
  contestId: string,
): BallotDraft {
  return {
    ballotStyleId: draft.ballotStyleId,
    selections: draft.selections.map((selection) =>
      selection.contestId === contestId
        ? { contestId, optionIds: [] }
        : selection,
    ),
  };
}

export function selectionFor(
  draft: BallotDraft,
  contestId: string,
): BallotSelection {
  return (
    draft.selections.find((selection) => selection.contestId === contestId) ?? {
      contestId,
      optionIds: [],
    }
  );
}

export type ContestValidity =
  | { readonly kind: "empty" }
  | { readonly kind: "within_limit" }
  | { readonly kind: "over_limit"; readonly limit: number };

export function contestValidity(
  style: BallotStyle,
  draft: BallotDraft,
  contestId: string,
): ContestValidity {
  const contest = contestById(style, contestId);
  const selection = selectionFor(draft, contestId);
  if (!contest) return { kind: "empty" };
  if (selection.optionIds.length === 0) return { kind: "empty" };
  if (selection.optionIds.length > contest.selectionLimit) {
    return { kind: "over_limit", limit: contest.selectionLimit };
  }
  return { kind: "within_limit" };
}

/**
 * A draft may be reviewed even when a contest is left blank — abstention is a
 * choice.  It may not be reviewed when a contest exceeds its limit, because
 * that ballot could not be encoded.
 */
export function readyForReview(
  style: BallotStyle,
  draft: BallotDraft,
): boolean {
  return style.contests.every(
    (contest) =>
      contestValidity(style, draft, contest.contestId).kind !== "over_limit",
  );
}

export function blankContestIds(
  style: BallotStyle,
  draft: BallotDraft,
): string[] {
  return style.contests
    .filter(
      (contest) =>
        contestValidity(style, draft, contest.contestId).kind === "empty",
    )
    .map((contest) => contest.contestId);
}

/**
 * A ballot style that arrives carrying identity or tally material is refused
 * outright.  A style is public data; anything else in it is a leak.
 */
export function ballotStyleAcceptable(style: unknown): boolean {
  return (
    findForbiddenIdentityFields(style).length === 0 &&
    findProhibitedTallyQuantities(style).length === 0
  );
}
