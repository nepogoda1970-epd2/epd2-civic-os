/**
 * Receipt minimisation.
 *
 * The receipt type in `types.ts` is already closed to the seven permitted
 * fields plus the counting marker.  This module is the second line: it refuses
 * a receipt whose *values* carry something prohibited, so a backend that one
 * day returns a confirmation code with the choice encoded into it is caught
 * here rather than rendered.
 */

import { findForbiddenIdentityFields } from "../policies/identity";
import { findProhibitedTallyQuantities } from "../policies/tally";
import type { BallotStyle, Receipt } from "./types";

export const RECEIPT_PERMITTED_FIELDS = Object.freeze([
  "electionContextReference",
  "confirmationCode",
  "boardCheckpointReference",
  "sealedBatchReference",
  "publicationStatus",
  "verificationInstructions",
  "receiptSchemaVersion",
  "countingStatus",
] as const);

export const RECEIPT_PROHIBITED_CONTENT = Object.freeze([
  "ballot_plaintext",
  "human_readable_choice",
  "nonce",
  "opening",
  "challenge_secret",
  "credential_reference",
  "continuation_reference",
  "identity",
  "exact_submission_timestamp",
  "exact_acceptance_timestamp",
  "exact_consumption_timestamp",
  "board_sequence",
  "leaf_index",
  "internal_object_id",
  "retry_token",
  "ip_address",
  "device_fingerprint",
  "build_fingerprint",
  "batch_occupancy",
  "position_among_ballots",
  "remaining_cast_entitlement",
  "remaining_challenge_entitlement",
  "link_to_challenge_artefact",
  "link_to_cast_artefact",
] as const);

export type ReceiptRejection = {
  readonly reasonCode:
    | "RECEIPT_FIELD_NOT_PERMITTED"
    | "RECEIPT_CARRIES_IDENTITY"
    | "RECEIPT_CARRIES_TALLY"
    | "RECEIPT_CARRIES_CHOICE"
    | "RECEIPT_CARRIES_EXACT_TIMESTAMP"
    | "RECEIPT_MALFORMED";
  readonly detail: readonly string[];
};

const ISO_INSTANT = /\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?/;

/**
 * Accept a receipt only if every field is permitted and no value discloses.
 * `style` is optional; when given, the option labels of the ballot are checked
 * against the receipt's text so a receipt that spells out the voter's choice is
 * refused even if it uses no prohibited field name.
 */
export function acceptReceipt(
  candidate: unknown,
  style?: BallotStyle,
):
  | { readonly ok: true; readonly receipt: Receipt }
  | {
      readonly ok: false;
      readonly rejection: ReceiptRejection;
    } {
  if (
    candidate === null ||
    typeof candidate !== "object" ||
    Array.isArray(candidate)
  ) {
    return {
      ok: false,
      rejection: { reasonCode: "RECEIPT_MALFORMED", detail: [] },
    };
  }
  const record = candidate as Record<string, unknown>;
  const permitted = RECEIPT_PERMITTED_FIELDS as readonly string[];
  const extra = Object.keys(record).filter((key) => !permitted.includes(key));
  if (extra.length > 0) {
    return {
      ok: false,
      rejection: {
        reasonCode: "RECEIPT_FIELD_NOT_PERMITTED",
        detail: extra.sort(),
      },
    };
  }
  for (const key of permitted) {
    if (typeof record[key] !== "string") {
      return {
        ok: false,
        rejection: { reasonCode: "RECEIPT_MALFORMED", detail: [key] },
      };
    }
  }
  const identity = findForbiddenIdentityFields(record);
  if (identity.length > 0) {
    return {
      ok: false,
      rejection: { reasonCode: "RECEIPT_CARRIES_IDENTITY", detail: identity },
    };
  }
  const tally = findProhibitedTallyQuantities(record);
  if (tally.length > 0) {
    return {
      ok: false,
      rejection: { reasonCode: "RECEIPT_CARRIES_TALLY", detail: tally },
    };
  }
  const joined = permitted.map((key) => String(record[key])).join("\n");
  if (ISO_INSTANT.test(joined)) {
    return {
      ok: false,
      rejection: { reasonCode: "RECEIPT_CARRIES_EXACT_TIMESTAMP", detail: [] },
    };
  }
  if (style) {
    const labels = style.contests.flatMap((contest) =>
      contest.options.map((option) => option.label),
    );
    const spelled = labels.filter(
      (label) => label.length > 2 && joined.includes(label),
    );
    if (spelled.length > 0) {
      return {
        ok: false,
        rejection: { reasonCode: "RECEIPT_CARRIES_CHOICE", detail: spelled },
      };
    }
  }
  return { ok: true, receipt: record as unknown as Receipt };
}

/**
 * The confirmation code is shown grouped, in an unambiguous alphabet, and is
 * always available as text.  A machine-readable form may exist beside it but
 * never instead of it.
 */
export const CONFIRMATION_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
export const CONFIRMATION_CODE_GROUP_SIZE = 4;

export function groupConfirmationCode(code: string): string {
  const cleaned = code.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
  const groups: string[] = [];
  for (let i = 0; i < cleaned.length; i += CONFIRMATION_CODE_GROUP_SIZE) {
    groups.push(cleaned.slice(i, i + CONFIRMATION_CODE_GROUP_SIZE));
  }
  return groups.join("-");
}

export function confirmationCodeWellFormed(code: string): boolean {
  const cleaned = code.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
  if (cleaned.length < 8 || cleaned.length > 32) return false;
  return [...cleaned].every((character) =>
    CONFIRMATION_CODE_ALPHABET.includes(character),
  );
}

/** A machine-readable rendering is never the only rendering. */
export const RECEIPT_RENDERINGS = Object.freeze({
  humanReadable: "mandatory",
  audioReadable: "mandatory",
  machineReadable: "optional_never_only",
  printing: "never_required",
  cameraRequired: false,
} as const);
