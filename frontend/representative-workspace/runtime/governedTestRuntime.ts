/**
 * Governed test profile.
 *
 * This module exists so the complete operator journey — the desk, a case
 * detail, a position draft, a deviation composition, a declaration form, a
 * publication proposal, the conflict-restricted state and every refusal
 * surface — can be exercised by real browser and accessibility tests. It is
 * not a backend and it never pretends to be one.
 *
 * What it supplies is presentation material only, and every item is marked as
 * prototype material in its own visible text. What it deliberately does NOT
 * supply is any successful mutation: no transition commits, no submission
 * succeeds, no proposal is accepted, no restriction is cleared. Those stay
 * blocked in this profile exactly as in production, because the dependency
 * blocking them is the absence of an accepted runtime, and a fixture cannot
 * substitute for one without becoming the fake the stage contract forbids.
 *
 * The fixture data contains no real person, no real case, and nothing that
 * could be mistaken for constituent correspondence.
 *
 * `FIXTURE_MARKER` is a unique string. The production build is scanned for it
 * and must not contain it.
 */

import type {
  CaseDetail,
  CaseSummary,
  ConflictRestriction,
  DeclarationRecord,
  DeviationRecord,
  MandateScope,
  MandateSession,
  PositionRecord,
  PublicationProposal,
  Result,
} from "../domain/types";
import { productionUnavailable } from "./unavailable";
import type { RepresentativeRuntime } from "./ports";

export const FIXTURE_MARKER = "EPD2_FRONT05_GOVERNED_TEST_FIXTURE_MARKER";

/** Every fixture string carries this prefix so it cannot be mistaken for real. */
export const FIXTURE_PREFIX = "PROTOTYP" as const;

export const FIXTURE_SCOPE: MandateScope = Object.freeze({
  mandateId: "PROTOTYP-MANDAT-0001",
  organizationId: "PROTOTYP-ORG-0001",
  label: "Prototyp-Mandat (nicht aktiviert)",
  level: "prototype",
  authorityActive: true,
  authorityExpiresAt: "2099-12-31T23:59:59Z",
});

export const FIXTURE_SESSION: MandateSession = Object.freeze({
  state: "authenticated",
  role: "representative",
  assurance: "standard",
  scope: FIXTURE_SCOPE,
  displayName: "Prototyp-Mandatsträgerin",
  conflictRestricted: false,
});

export const FIXTURE_CASES: readonly CaseSummary[] = Object.freeze([
  {
    caseId: "PROTOTYP-VORGANG-0001",
    reference: "PROTOTYP/2026/0001",
    subject: "Prototyp-Anliegen: Beispieltext ohne realen Bezug",
    state: "new",
    receivedAt: "2026-08-01T09:00:00Z",
    mandateId: FIXTURE_SCOPE.mandateId,
    assigneeLabel: null,
    conflictRestricted: false,
  },
  {
    caseId: "PROTOTYP-VORGANG-0002",
    reference: "PROTOTYP/2026/0002",
    subject: "Prototyp-Anliegen: zweiter Beispieltext",
    state: "triaged",
    receivedAt: "2026-08-03T11:30:00Z",
    mandateId: FIXTURE_SCOPE.mandateId,
    assigneeLabel: "Prototyp-Büro",
    conflictRestricted: false,
  },
  {
    caseId: "PROTOTYP-VORGANG-0003",
    reference: "PROTOTYP/2026/0003",
    subject: "Zugriff eingeschränkt",
    state: "assigned",
    receivedAt: "2026-08-05T08:15:00Z",
    mandateId: FIXTURE_SCOPE.mandateId,
    assigneeLabel: null,
    conflictRestricted: true,
  },
]);

export const FIXTURE_CASE_DETAIL: CaseDetail = Object.freeze({
  ...FIXTURE_CASES[0],
  summaryText:
    "Prototyp-Inhalt. Dieser Text stammt aus dem geprüften Testprofil und ist kein reales Bürgeranliegen.",
  provenance: "PROTOTYP-QUELLE",
  version: "PROTOTYP-VERSION-1",
});

export const FIXTURE_POSITIONS: readonly PositionRecord[] = Object.freeze([
  {
    positionId: "PROTOTYP-POSITION-0001",
    title: "Prototyp-Position",
    state: "draft",
    version: "PROTOTYP-VERSION-1",
    mandateId: FIXTURE_SCOPE.mandateId,
    updatedAt: "2026-08-10T10:00:00Z",
    publicationState: "draft",
  },
]);

export const FIXTURE_DEVIATIONS: readonly DeviationRecord[] = Object.freeze([
  {
    deviationId: "PROTOTYP-ABWEICHUNG-0001",
    issue: "Prototyp-Thema",
    representativePosition: "Prototyp-Standpunkt",
    referencedDecision: "PROTOTYP-ENTSCHEIDUNG-0001",
    explanation:
      "Prototyp-Begründung aus dem geprüften Testprofil. Kein realer Vorgang und keine reale Entscheidung.",
    recordedAt: "2026-08-12T12:00:00Z",
    version: "PROTOTYP-VERSION-1",
    supersedes: null,
    publicationState: "draft",
  },
]);

export const FIXTURE_DECLARATIONS: readonly DeclarationRecord[] = Object.freeze(
  [
    {
      declarationId: "PROTOTYP-ERKLAERUNG-0001",
      kind: "meeting",
      subject: "Prototyp-Termin",
      occurredAt: "2026-08-14",
      submittedAt: null,
      state: "draft",
    },
  ],
);

export const FIXTURE_PROPOSAL: PublicationProposal = Object.freeze({
  proposalId: "PROTOTYP-VORSCHLAG-0001",
  sourceKind: "position",
  sourceId: "PROTOTYP-POSITION-0001",
  state: "draft",
  decidedBy: null,
  publicRenditionRef: null,
});

export const FIXTURE_RESTRICTIONS: readonly ConflictRestriction[] =
  Object.freeze([
    {
      restrictionId: "PROTOTYP-BESCHRAENKUNG-0001",
      scopeLabel: "PROTOTYP-VORGANG-0003",
      active: true,
      recordedAt: "2026-08-05T09:00:00Z",
      safeReason: "Beschränkung durch die zuständige Stelle erfasst.",
      mayBeClearedBySubject: false,
    },
  ]);

function ok<T>(value: T): Result<T> {
  return { ok: true, value };
}

/**
 * Reads succeed with prototype material; every mutation returns exactly the
 * production refusal. The asymmetry is the point: the journey is walkable and
 * no consequential act ever appears to have happened.
 */
export function createGovernedTestRuntime(): RepresentativeRuntime {
  const runtime: RepresentativeRuntime = {
    profile: "governed_test",
    session: {
      current: async () => ok(FIXTURE_SESSION),
      observeStepUp: async () => productionUnavailable("stepUp"),
      signOut: async () => ok(null),
    },
    scope: {
      resolve: async () => ok(FIXTURE_SCOPE),
    },
    cases: {
      list: async () => ok(FIXTURE_CASES),
      read: async (bound) =>
        bound.value.caseId === FIXTURE_CASE_DETAIL.caseId
          ? ok(FIXTURE_CASE_DETAIL)
          : productionUnavailable("caseDetail"),
      search: async () => productionUnavailable("caseSearch"),
      transition: async () => productionUnavailable("caseMutation"),
      reread: async () => ok(FIXTURE_CASE_DETAIL),
    },
    positions: {
      list: async () => ok(FIXTURE_POSITIONS),
      save: async () => productionUnavailable("positionWrite"),
      submitInternal: async () => productionUnavailable("positionWrite"),
    },
    deviations: {
      list: async () => ok(FIXTURE_DEVIATIONS),
      record: async () => productionUnavailable("deviation"),
      resolveDecision: async () => productionUnavailable("decisionReference"),
    },
    declarations: {
      list: async () => ok(FIXTURE_DECLARATIONS),
      submit: async () => productionUnavailable("declaration"),
    },
    publication: {
      propose: async () => productionUnavailable("publicationProposal"),
      withdraw: async () => productionUnavailable("publicationProposal"),
      observe: async () => ok(FIXTURE_PROPOSAL),
    },
    conflict: {
      restrictions: async () => ok(FIXTURE_RESTRICTIONS),
      recordAssessmentProposal: async () => productionUnavailable("conflict"),
    },
    registry: {
      read: async () => productionUnavailable("registry"),
    },
    eligibility: {
      observe: async () => productionUnavailable("eligibility"),
    },
    audit: {
      read: async () => productionUnavailable("audit"),
    },
  };
  return Object.freeze(runtime);
}
