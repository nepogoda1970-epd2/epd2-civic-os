import assert from "node:assert/strict";
import test from "node:test";

import {
  CONFIRMATION_CODE_ALPHABET,
  RECEIPT_PERMITTED_FIELDS,
  RECEIPT_PROHIBITED_CONTENT,
  RECEIPT_RENDERINGS,
  acceptReceipt,
  confirmationCodeWellFormed,
  groupConfirmationCode,
} from "../domain/receipt";
import type { BallotStyle } from "../domain/types";

const VALID = {
  electionContextReference: "KONTEXT-0001",
  confirmationCode: "ABCDEFGH23456789",
  boardCheckpointReference: "CHECKPOINT-14",
  sealedBatchReference: "BATCH-2026-W36",
  publicationStatus: "ACCEPTED_PENDING_BATCH_COMMITMENT",
  verificationInstructions:
    "Prüfen Sie den Code auf der gesonderten Prüfseite.",
  receiptSchemaVersion: "1",
  countingStatus: "COUNTED_IF_PUBLISHED",
};

const STYLE: BallotStyle = {
  ballotStyleId: "s",
  schemaVersion: "1",
  contests: [
    {
      contestId: "c",
      title: "T",
      instruction: "i",
      selectionLimit: 1,
      options: [
        { optionId: "a", label: "Antwortmöglichkeit A" },
        { optionId: "b", label: "Antwortmöglichkeit B" },
      ],
    },
  ],
};

test("the permitted field list is exactly the specified eight", () => {
  assert.equal(RECEIPT_PERMITTED_FIELDS.length, 8);
  assert.deepEqual([...RECEIPT_PERMITTED_FIELDS].sort(), [
    "boardCheckpointReference",
    "confirmationCode",
    "countingStatus",
    "electionContextReference",
    "publicationStatus",
    "receiptSchemaVersion",
    "sealedBatchReference",
    "verificationInstructions",
  ]);
});

test("a well-formed receipt is accepted", () => {
  const result = acceptReceipt(VALID, STYLE);
  assert.equal(result.ok, true);
});

test("any field beyond the permitted set is refused", () => {
  for (const extra of [
    "ballotPlaintext",
    "choice",
    "boardSequence",
    "leafIndex",
    "retryToken",
    "acceptedAt",
    "voterHint",
  ]) {
    const result = acceptReceipt({ ...VALID, [extra]: "x" });
    assert.equal(result.ok, false, extra);
    if (result.ok) continue;
    assert.equal(result.rejection.reasonCode, "RECEIPT_FIELD_NOT_PERMITTED");
    assert.deepEqual(result.rejection.detail, [extra]);
  }
});

test("a receipt carrying persistent identity is refused", () => {
  const result = acceptReceipt({ ...VALID, member_id: "x" });
  assert.equal(result.ok, false);
  if (result.ok) return;
  // The field is not permitted at all, which is caught first and is stricter.
  assert.equal(result.rejection.reasonCode, "RECEIPT_FIELD_NOT_PERMITTED");
});

test("a receipt whose value spells out the choice is refused", () => {
  const result = acceptReceipt(
    { ...VALID, verificationInstructions: "Sie wählten Antwortmöglichkeit A." },
    STYLE,
  );
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.rejection.reasonCode, "RECEIPT_CARRIES_CHOICE");
  assert.deepEqual(result.rejection.detail, ["Antwortmöglichkeit A"]);
});

test("a receipt carrying an exact timestamp is refused", () => {
  for (const value of [
    "2026-09-01T12:34:56Z",
    "angenommen am 2026-09-01 12:34",
  ]) {
    const result = acceptReceipt({ ...VALID, sealedBatchReference: value });
    assert.equal(result.ok, false, value);
    if (result.ok) continue;
    assert.equal(
      result.rejection.reasonCode,
      "RECEIPT_CARRIES_EXACT_TIMESTAMP",
    );
  }
});

test("a malformed receipt is refused", () => {
  for (const value of [
    null,
    undefined,
    [],
    "text",
    3,
    { ...VALID, confirmationCode: 4 },
  ]) {
    const result = acceptReceipt(value);
    assert.equal(result.ok, false);
    if (result.ok) continue;
    assert.match(
      result.rejection.reasonCode,
      /RECEIPT_(MALFORMED|FIELD_NOT_PERMITTED)/,
    );
  }
});

test("a public challenge receipt states that it is not counted", () => {
  const result = acceptReceipt(
    { ...VALID, countingStatus: "NOT_COUNTED" },
    STYLE,
  );
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.equal(result.receipt.countingStatus, "NOT_COUNTED");
});

test("the prohibited content list names every item the specification names", () => {
  for (const item of [
    "ballot_plaintext",
    "human_readable_choice",
    "credential_reference",
    "continuation_reference",
    "board_sequence",
    "leaf_index",
    "retry_token",
    "remaining_cast_entitlement",
    "remaining_challenge_entitlement",
    "link_to_challenge_artefact",
    "link_to_cast_artefact",
    "exact_acceptance_timestamp",
  ]) {
    assert.ok(
      (RECEIPT_PROHIBITED_CONTENT as readonly string[]).includes(item),
      item,
    );
  }
});

test("the confirmation code is grouped and transcribable", () => {
  assert.equal(
    groupConfirmationCode("ABCDEFGH23456789"),
    "ABCD-EFGH-2345-6789",
  );
  assert.equal(groupConfirmationCode("abcd efgh"), "ABCD-EFGH");
  for (const confusable of ["I", "O", "0", "1"]) {
    assert.ok(!CONFIRMATION_CODE_ALPHABET.includes(confusable), confusable);
  }
});

test("code validation accepts the alphabet and refuses the rest", () => {
  assert.equal(confirmationCodeWellFormed("ABCD-EFGH-2345-6789"), true);
  assert.equal(confirmationCodeWellFormed("abcdefgh"), true);
  assert.equal(confirmationCodeWellFormed("ABC"), false);
  assert.equal(confirmationCodeWellFormed("ABCDEFG0"), false);
  assert.equal(confirmationCodeWellFormed("ABCDEFGI"), false);
  assert.equal(confirmationCodeWellFormed(""), false);
});

test("no rendering path requires a camera, a print or a machine-readable form", () => {
  assert.equal(RECEIPT_RENDERINGS.humanReadable, "mandatory");
  assert.equal(RECEIPT_RENDERINGS.audioReadable, "mandatory");
  assert.equal(RECEIPT_RENDERINGS.machineReadable, "optional_never_only");
  assert.equal(RECEIPT_RENDERINGS.printing, "never_required");
  assert.equal(RECEIPT_RENDERINGS.cameraRequired, false);
});
