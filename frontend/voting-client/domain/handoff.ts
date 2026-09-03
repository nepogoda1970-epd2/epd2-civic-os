/**
 * The WS-02 → WS-03 handoff, verified on the WS-03 side.
 *
 * The check order mirrors the accepted identity-service and eligibility-service
 * implementations exactly: origin and audience are checked before anything else
 * is read, so a misdirected artifact is refused without its contents being
 * processed.  An unknown artifact and a bad value produce the same refusal, so
 * a caller cannot use the refusal as an existence oracle.
 *
 * This module verifies.  It does not fetch: no accepted runtime route exists
 * for redemption from a browser, and inventing one is forbidden.
 */

import {
  assertNoIdentity,
  findForbiddenIdentityFields,
} from "../policies/identity";
import { WS03_ORIGIN } from "../policies/isolation";
import type { SafeRefusal, VotingContext } from "./types";

export const VOTING_ENTRY_PURPOSE = "voting_entry" as const;
export const VOTING_AUDIENCE_ORIGIN = WS03_ORIGIN;

/** The artifact as it is presented to WS-03.  Six fields, none of them a person. */
export type HandoffArtifact = {
  readonly artifact: string;
  readonly audienceOrigin: string;
  readonly purpose: string;
  readonly votingContextId: string;
  readonly expiresAt: string;
};

export const HANDOFF_REFUSAL_CODES = Object.freeze([
  "VOTING_HANDOFF_INVALID",
  "VOTING_HANDOFF_EXPIRED",
  "VOTING_HANDOFF_ALREADY_USED",
  "VOTING_HANDOFF_AUDIENCE_MISMATCH",
  "VOTING_HANDOFF_ORIGIN_MISMATCH",
  "VOTING_HANDOFF_PURPOSE_MISMATCH",
  "VOTING_HANDOFF_CONTEXT_MISMATCH",
  "VOTING_HANDOFF_IDENTITY_PRESENT",
  "VOTING_HANDOFF_CHANNEL_FORBIDDEN",
] as const);

export type HandoffRefusalCode = (typeof HANDOFF_REFUSAL_CODES)[number];

export type HandoffVerification =
  | { readonly ok: true; readonly context: VotingContext }
  | { readonly ok: false; readonly refusal: SafeRefusal };

export type HandoffBinding = {
  readonly expectedAudience: string;
  readonly allowedOrigins: readonly string[];
  readonly expectedVotingContextId: string;
  readonly now: Date;
  /** Digests of artifacts this origin has already consumed in this page life. */
  readonly consumedDigests: ReadonlySet<string>;
};

/**
 * Every refusal renders the same sentence to the voter.  The reason code is
 * kept for the governed screen-state matrix and for tests; it is not a message
 * the voter is asked to interpret and it never says whether a record exists.
 */
const SAFE_MESSAGE =
  "Der Zugang zum Abstimmungsbereich konnte nicht übernommen werden.";
const NEXT_ACTION =
  "Kehren Sie in den Mitgliederbereich zurück und starten Sie den Vorgang erneut.";

function refuse(reasonCode: HandoffRefusalCode): HandoffVerification {
  return {
    ok: false,
    refusal: {
      kind:
        reasonCode === "VOTING_HANDOFF_EXPIRED"
          ? "expired"
          : reasonCode === "VOTING_HANDOFF_ALREADY_USED"
            ? "conflict"
            : "refused",
      reasonCode,
      safeMessage: SAFE_MESSAGE,
      // Nothing was cast: a handoff refusal happens before any ballot exists.
      commitKnowledge: "not_committed",
      entitlementKnownIntact: reasonCode !== "VOTING_HANDOFF_ALREADY_USED",
      nextSafeAction: NEXT_ACTION,
    },
  };
}

/**
 * A stable, non-reversible page-local digest of an artifact value, used only to
 * detect replay within one page life.  It is never stored, never transmitted
 * and never rendered.
 */
export function pageLocalDigest(value: string): string {
  let h1 = 0x811c9dc5;
  let h2 = 0x01000193;
  for (let i = 0; i < value.length; i += 1) {
    const c = value.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 0x01000193) >>> 0;
    h2 = Math.imul(h2 + c + i, 0x85ebca6b) >>> 0;
  }
  return `${h1.toString(16).padStart(8, "0")}${h2.toString(16).padStart(8, "0")}`;
}

function wellFormed(value: unknown): value is HandoffArtifact {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.artifact === "string" &&
    candidate.artifact.length > 0 &&
    typeof candidate.audienceOrigin === "string" &&
    typeof candidate.purpose === "string" &&
    typeof candidate.votingContextId === "string" &&
    candidate.votingContextId.length > 0 &&
    typeof candidate.expiresAt === "string"
  );
}

/**
 * Verify a presented handoff.  Order matters and is asserted by tests:
 *   1. shape
 *   2. no persistent identity anywhere in the value
 *   3. presenting origin
 *   4. audience
 *   5. purpose
 *   6. voting context
 *   7. replay
 *   8. expiry
 */
export function verifyHandoff(
  presented: unknown,
  binding: HandoffBinding,
  presentingOrigin: string,
): HandoffVerification {
  if (!wellFormed(presented)) return refuse("VOTING_HANDOFF_INVALID");
  if (findForbiddenIdentityFields(presented).length > 0) {
    return refuse("VOTING_HANDOFF_IDENTITY_PRESENT");
  }
  if (!binding.allowedOrigins.includes(presentingOrigin)) {
    return refuse("VOTING_HANDOFF_ORIGIN_MISMATCH");
  }
  if (presented.audienceOrigin !== binding.expectedAudience) {
    return refuse("VOTING_HANDOFF_AUDIENCE_MISMATCH");
  }
  if (presented.purpose !== VOTING_ENTRY_PURPOSE) {
    return refuse("VOTING_HANDOFF_PURPOSE_MISMATCH");
  }
  if (presented.votingContextId !== binding.expectedVotingContextId) {
    return refuse("VOTING_HANDOFF_CONTEXT_MISMATCH");
  }
  if (binding.consumedDigests.has(pageLocalDigest(presented.artifact))) {
    return refuse("VOTING_HANDOFF_ALREADY_USED");
  }
  const expiry = Date.parse(presented.expiresAt);
  if (Number.isNaN(expiry)) return refuse("VOTING_HANDOFF_INVALID");
  if (binding.now.getTime() >= expiry) return refuse("VOTING_HANDOFF_EXPIRED");

  return {
    ok: true,
    context: assertNoIdentity({
      votingContextId: presented.votingContextId,
      audienceOrigin: presented.audienceOrigin,
      purpose: VOTING_ENTRY_PURPOSE,
      expiresAt: presented.expiresAt,
      role: "eligible_voter",
    } satisfies VotingContext),
  };
}

/**
 * Channels through which a handoff may never be presented.  A value arriving
 * on one of these is refused as a channel violation and is not verified at
 * all: verifying it would mean processing a value the boundary has already
 * decided it will not accept.
 */
export const FORBIDDEN_HANDOFF_CHANNELS = Object.freeze([
  "query_string",
  "url_fragment",
  "path_segment",
  "local_storage",
  "session_storage",
  "indexed_db",
  "cookie",
  "cache_storage",
  "page_title",
  "referrer",
  "post_message_wildcard",
] as const);

export type HandoffChannel = (typeof FORBIDDEN_HANDOFF_CHANNELS)[number];

export function handoffChannelPermitted(channel: string): boolean {
  void channel;
  // No accepted runtime channel exists for presenting a handoff to a browser
  // in WS-03.  Until one does, every channel is refused, which is what keeps
  // the credential surface fail-closed rather than merely careful.
  return false;
}

/**
 * True when a URL carries something that looks like a handoff.  Used by the
 * credential surface to refuse loudly rather than ignore quietly, and by the
 * browser tests to prove the value never reaches storage, title or referrer.
 */
export const HANDOFF_BEARING_PARAMETER_NAMES = Object.freeze([
  "handoff",
  "artifact",
  "voting_handoff",
  "handoff_artifact",
  "continuation",
  "capability",
  "credential",
  "token",
  "assertion",
] as const);

export function urlCarriesHandoffChannelViolation(url: string): boolean {
  let parsed: URL;
  try {
    parsed = new URL(url, WS03_ORIGIN);
  } catch {
    return false;
  }
  const names = HANDOFF_BEARING_PARAMETER_NAMES as readonly string[];
  for (const name of parsed.searchParams.keys()) {
    if (names.includes(name.toLowerCase())) return true;
  }
  const fragment = parsed.hash.replace(/^#/, "");
  if (fragment.length === 0) return false;
  const fragmentParams = new URLSearchParams(fragment);
  for (const name of fragmentParams.keys()) {
    if (names.includes(name.toLowerCase())) return true;
  }
  return names.includes(fragment.toLowerCase());
}
