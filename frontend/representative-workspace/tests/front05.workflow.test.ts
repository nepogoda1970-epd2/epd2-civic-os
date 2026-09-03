import assert from "node:assert/strict";
import test from "node:test";

import {
  CASE_ACTIONS,
  STALE_CASE,
  UNCERTAIN_CASE,
  listProjection,
  preconditionFor,
  proposedCaseState,
  retryOfferedFor,
} from "../domain/caseWorkflow";
import {
  DECISION_REFERENCE_UNVERIFIED,
  DEVIATION_LIMITS,
  referenceVerified,
  supersedes,
  validateDeviationDraft,
} from "../domain/deviation";
import {
  OBLIGATION_REMAINS_OPEN,
  obligationDischarged,
  submissionBlockedRefusal,
  validateDeclarationDraft,
} from "../domain/declaration";
import {
  PROPOSAL_DISCLAIMER,
  PUBLICATION_MODEL_GAP,
  mayPresentAsPublic,
  publicationLabel,
} from "../domain/publication";
import { CASE_STATES, POSITION_STATES } from "../domain/types";
import type { CaseSummary, DeviationRecord } from "../domain/types";
import {
  stepUpRequired,
  commitTimeRevalidationRequired,
} from "../policies/authority";

/* ------------------------------------------------------------------ case states */

test("the archived and unavailable states are terminal", () => {
  for (const state of ["archived", "unavailable"] as const) {
    for (const type of [
      "assign",
      "triage",
      "await_response",
      "record_response",
      "close",
      "archive",
      "reopen",
    ] as const) {
      assert.equal(
        proposedCaseState(state, { type }),
        null,
        `${state}+${type}`,
      );
    }
  }
});

test("no transition leads into the unavailable state", () => {
  for (const state of CASE_STATES) {
    for (const type of [
      "assign",
      "triage",
      "await_response",
      "record_response",
      "close",
      "archive",
      "reopen",
    ] as const) {
      assert.notEqual(
        proposedCaseState(state, { type }),
        "unavailable",
        `${state}+${type}`,
      );
    }
  }
});

test("a transition without a version precondition is inadmissible", () => {
  assert.equal(preconditionFor(null).admissible, false);
  assert.equal(preconditionFor("").admissible, false);
  assert.equal(preconditionFor("v1").admissible, true);
  assert.equal(preconditionFor("v1").requiresVersion, true);
});

test("the uncertain outcome offers no retry", () => {
  assert.equal(
    retryOfferedFor({ kind: "uncertain", refusal: UNCERTAIN_CASE }),
    false,
  );
  assert.equal(UNCERTAIN_CASE.committed, "unknown");
  assert.match(UNCERTAIN_CASE.nextSafeAction, /Nicht erneut absenden/);
});

test("a stale-version conflict offers no blind retry either", () => {
  assert.equal(
    retryOfferedFor({ kind: "refused", refusal: STALE_CASE }),
    false,
  );
  assert.equal(STALE_CASE.committed, "not_committed");
});

test("the case list projection carries no body text", () => {
  const summary: CaseSummary = {
    caseId: "c1",
    reference: "R/1",
    subject: "Betreff",
    state: "new",
    receivedAt: "2026-01-01T00:00:00Z",
    mandateId: "M",
    assigneeLabel: null,
    conflictRestricted: false,
  };
  const projected = listProjection([summary]);
  assert.deepEqual(
    Object.keys(projected[0]).sort(),
    Object.keys(summary).sort(),
  );
  assert.ok(!("summaryText" in projected[0]));
});

test("a restricted case's subject is replaced in the list", () => {
  const projected = listProjection([
    {
      caseId: "c1",
      reference: "R/1",
      subject: "Vertraulicher Betreff",
      state: "new",
      receivedAt: "2026-01-01T00:00:00Z",
      mandateId: "M",
      assigneeLabel: null,
      conflictRestricted: true,
    },
  ]);
  assert.equal(projected[0].subject, "Zugriff eingeschränkt");
});

test("consequential case actions demand step-up and commit revalidation", () => {
  const close = CASE_ACTIONS.find((a) => a.actionId === "case.close");
  assert.ok(close);
  assert.equal(close.impact, "consequential");
  assert.equal(stepUpRequired(close.impact), true);
  assert.equal(commitTimeRevalidationRequired(close.impact), true);
  // A read never demands step-up.
  assert.equal(stepUpRequired("read"), false);
  assert.equal(commitTimeRevalidationRequired("high"), false);
});

/* ------------------------------------------------------------------ deviations */

test("a deviation without a referenced decision is rejected", () => {
  const result = validateDeviationDraft({
    issue: "Thema",
    representativePosition: "Standpunkt",
    referencedDecision: null,
    explanation: "x".repeat(DEVIATION_LIMITS.explanationMinLength),
    supersedes: null,
  });
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.error.reasonCode, "WS04-DEV-003");
});

test("a deviation without a substantive explanation is rejected", () => {
  const result = validateDeviationDraft({
    issue: "Thema",
    representativePosition: "Standpunkt",
    referencedDecision: "D-1",
    explanation: "zu kurz",
    supersedes: null,
  });
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.error.reasonCode, "WS04-DEV-004");
});

test("a well-formed deviation passes locally without being accepted", () => {
  const draft = {
    issue: "Thema",
    representativePosition: "Standpunkt",
    referencedDecision: "D-1",
    explanation: "x".repeat(60),
    supersedes: null,
  };
  assert.equal(validateDeviationDraft(draft).ok, true);
});

test("a decision reference is never reported as verified", () => {
  const record: DeviationRecord = {
    deviationId: "d1",
    issue: "i",
    representativePosition: "p",
    referencedDecision: "D-1",
    explanation: "e",
    recordedAt: "2026-01-01T00:00:00Z",
    version: "v1",
    supersedes: null,
    publicationState: "draft",
  };
  assert.equal(referenceVerified(record), false);
  assert.match(DECISION_REFERENCE_UNVERIFIED, /ungeprüft/);
});

test("superseding is explicit and preserves the earlier record", () => {
  const earlier: DeviationRecord = {
    deviationId: "d1",
    issue: "i",
    representativePosition: "p",
    referencedDecision: "D-1",
    explanation: "e",
    recordedAt: "2026-01-01T00:00:00Z",
    version: "v1",
    supersedes: null,
    publicationState: "draft",
  };
  const later = { ...earlier, deviationId: "d2", supersedes: "d1" };
  assert.equal(supersedes(earlier, later), true);
  assert.equal(supersedes(later, earlier), false);
});

/* ---------------------------------------------------------------- declarations */

test("a meeting without a counterparty is not documentable", () => {
  const result = validateDeclarationDraft({
    kind: "meeting",
    subject: "Termin",
    occurredAt: "2026-01-01",
    counterparty: "  ",
    summary: "",
  });
  assert.equal(result.ok, false);
  if (result.ok) return;
  assert.equal(result.error.reasonCode, "WS04-DECL-004");
});

test("an incomplete date is rejected", () => {
  for (const occurredAt of ["", "2026", "2026-01", "01.01.2026"]) {
    const result = validateDeclarationDraft({
      kind: "declaration",
      subject: "Gegenstand",
      occurredAt,
      counterparty: "",
      summary: "",
    });
    assert.equal(result.ok, false, occurredAt);
  }
});

test("no obligation is discharged without an accepted, submitted record", () => {
  assert.equal(
    obligationDischarged({
      declarationId: "x",
      kind: "meeting",
      subject: "s",
      occurredAt: "2026-01-01",
      submittedAt: null,
      state: "draft",
    }),
    false,
  );
  assert.equal(
    obligationDischarged({
      declarationId: "x",
      kind: "meeting",
      subject: "s",
      occurredAt: "2026-01-01",
      submittedAt: "2026-01-02T00:00:00Z",
      state: "submitted",
    }),
    false,
  );
  assert.equal(
    obligationDischarged({
      declarationId: "x",
      kind: "meeting",
      subject: "s",
      occurredAt: "2026-01-01",
      submittedAt: "2026-01-02T00:00:00Z",
      state: "accepted",
    }),
    true,
  );
});

test("the blocked-submission refusal states that the obligation stays open", () => {
  const refusal = submissionBlockedRefusal();
  assert.equal(refusal.nextSafeAction, OBLIGATION_REMAINS_OPEN);
  assert.match(OBLIGATION_REMAINS_OPEN, /Meldepflicht bleibt offen/);
});

/* ----------------------------------------------------------------- publication */

test("every publication state has a label that never reads as published", () => {
  assert.match(publicationLabel("draft"), /nicht eingereicht/);
  assert.match(publicationLabel("proposal_submitted"), /nicht freigegeben/);
  assert.match(
    publicationLabel("approved_by_publication_authority"),
    /Veröffentlichungsstelle/,
  );
});

test("an approved state without a deciding authority is not presented as public", () => {
  assert.equal(
    mayPresentAsPublic({
      proposalId: "p",
      sourceKind: "position",
      sourceId: "s",
      state: "approved_by_publication_authority",
      decidedBy: null,
      publicRenditionRef: null,
    }),
    false,
  );
  assert.equal(
    mayPresentAsPublic({
      proposalId: "p",
      sourceKind: "position",
      sourceId: "s",
      state: "approved_by_publication_authority",
      decidedBy: "Veröffentlichungsstelle",
      publicRenditionRef: "ref",
    }),
    true,
  );
  assert.equal(
    mayPresentAsPublic({
      proposalId: "p",
      sourceKind: "position",
      sourceId: "s",
      state: "proposal_submitted",
      decidedBy: "x",
      publicRenditionRef: "ref",
    }),
    false,
  );
});

test("the proposal disclaimer is unambiguous", () => {
  assert.match(PROPOSAL_DISCLAIMER, /keine Veröffentlichung/);
  assert.match(PROPOSAL_DISCLAIMER, /keine Freigabe/);
});

test("the missing server proposal state is recorded as an open item", () => {
  assert.match(PUBLICATION_MODEL_GAP.disposition, /OPEN_GOVERNANCE_ITEM/);
  assert.match(PUBLICATION_MODEL_GAP.observed, /PUBLISHED/);
  assert.match(PUBLICATION_MODEL_GAP.observed, /actor_is_authorized/);
});

test("a local position draft is not a publication state", () => {
  assert.ok((POSITION_STATES as readonly string[]).includes("draft"));
  assert.ok(
    (POSITION_STATES as readonly string[]).includes(
      "public_approved_rendition",
    ),
  );
  // The two vocabularies are distinct; a position state is not a publication one.
  assert.ok(
    !(POSITION_STATES as readonly string[]).includes("proposal_submitted"),
  );
});
