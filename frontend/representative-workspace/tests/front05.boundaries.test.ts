import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

import {
  ELIGIBILITY_DECISIONS,
  NON_AUTHORITATIVE_IN_CLIENT,
  PROTECTED_REGISTRIES,
  PUBLICATION_STATES,
  REGISTRY_ACTIONS_FORBIDDEN,
  STATES_ONLY_PUBLICATION_AUTHORITY_MAY_SET,
  STATES_WS04_MAY_ORIGINATE,
  VOTING_DOMAIN_PROHIBITIONS,
  clientMayDecide,
  isPublicApproved,
  mayDecideEligibility,
  mayMutateRegistry,
  proposalEqualsPublicApproved,
  votingDomainAccessAvailableFor,
  ws04MayApprovePublication,
  ws04MayOriginate,
} from "../policies/boundaries";
import {
  FORBIDDEN_UNIVERSAL_ROLES,
  WS04_ROLES,
  crossMandateAccessAvailableFor,
  isForbiddenUniversalRole,
  mayOfferAction,
  maySelfClearConflict,
} from "../policies/authority";
import {
  actionRegisterClean,
  FORBIDDEN_PUBLICATION_ACTION_IDS,
  PUBLICATION_ACTIONS,
  proposedPublicationState,
  ws04MayReachApproved,
} from "../domain/publication";
import {
  CONFLICT_ACTIONS,
  FORBIDDEN_CONFLICT_ACTION_IDS,
  conflictRegisterClean,
  restrictedFor,
  anyRestrictionActive,
} from "../domain/conflict";
import { deviationAltersDecision } from "../domain/deviation";
import { clientMayCommitCaseTransition } from "../domain/caseWorkflow";

const HERE = resolve(import.meta.dirname, "..");

/* ---------------------------------------------------------------- prohibition 1 */

test("WS-04 may originate only draft and proposal states", () => {
  assert.deepEqual(
    [...STATES_WS04_MAY_ORIGINATE],
    ["draft", "proposal_submitted"],
  );
  for (const state of PUBLICATION_STATES) {
    const originable = ws04MayOriginate(state);
    const reserved = (
      STATES_ONLY_PUBLICATION_AUTHORITY_MAY_SET as readonly string[]
    ).includes(state);
    assert.equal(
      originable,
      !reserved,
      `${state} must be originable exactly when it is not reserved`,
    );
  }
});

test("no publication event reaches the approved state from any state", () => {
  for (const state of PUBLICATION_STATES) {
    for (const type of ["compose", "submit_proposal", "withdraw"] as const) {
      const next = proposedPublicationState(state, { type });
      assert.notEqual(
        next,
        "approved_by_publication_authority",
        `${state} + ${type} reached approval`,
      );
    }
    assert.equal(ws04MayReachApproved(state), false);
  }
});

test("approval is a total refusal and a proposal is never an approval", () => {
  assert.equal(ws04MayApprovePublication(), false);
  assert.equal(proposalEqualsPublicApproved(), false);
  assert.equal(isPublicApproved("proposal_submitted"), false);
  assert.equal(isPublicApproved("approved_by_publication_authority"), true);
});

test("the publication action register contains no approval verb", () => {
  assert.equal(actionRegisterClean(), true);
  const ids = PUBLICATION_ACTIONS.map((a) => a.actionId);
  for (const forbidden of FORBIDDEN_PUBLICATION_ACTION_IDS) {
    assert.ok(!ids.includes(forbidden), `${forbidden} must not be offered`);
  }
});

/* ---------------------------------------------------------------- prohibition 2 */

test("no registry mutation is permitted, for any registry or action", () => {
  for (const registry of PROTECTED_REGISTRIES) {
    for (const action of REGISTRY_ACTIONS_FORBIDDEN) {
      assert.equal(
        mayMutateRegistry(registry, action),
        false,
        `${action} on ${registry}`,
      );
    }
  }
});

/* ---------------------------------------------------------------- prohibition 3 */

test("no eligibility decision may be taken here", () => {
  for (const kind of ELIGIBILITY_DECISIONS) {
    assert.equal(mayDecideEligibility(kind), false, kind);
  }
  assert.equal(mayDecideEligibility("anything_at_all"), false);
});

/* ---------------------------------------------------------------- prohibition 4 */

test("the voting domain is unreachable for every role", () => {
  for (const role of WS04_ROLES) {
    assert.equal(votingDomainAccessAvailableFor(role), false, role);
  }
  assert.ok(VOTING_DOMAIN_PROHIBITIONS.length >= 5);
});

/* ------------------------------------------------------- no universal admin mode */

test("no universal or cross-mandate role exists", () => {
  for (const role of FORBIDDEN_UNIVERSAL_ROLES) {
    assert.equal(isForbiddenUniversalRole(role), true, role);
    assert.ok(
      !(WS04_ROLES as readonly string[]).includes(role),
      `${role} must not be a WS-04 role`,
    );
  }
  for (const role of WS04_ROLES) {
    assert.equal(crossMandateAccessAvailableFor(role), false, role);
  }
});

test("the forbidden universal role names appear in no source file as a value", () => {
  const offenders: string[] = [];
  for (const file of sourceFiles()) {
    const text = readFileSync(file, "utf8");
    for (const role of FORBIDDEN_UNIVERSAL_ROLES) {
      // The names may appear inside the prohibition list itself and in tests.
      if (
        text.includes(`"${role}"`) &&
        !file.endsWith("policies/authority.ts") &&
        !file.includes("/tests/")
      ) {
        offenders.push(`${file}: ${role}`);
      }
    }
  }
  assert.deepEqual(offenders, []);
});

/* ------------------------------------------------ the client decides nothing */

test("no authoritative subject is decided in the client", () => {
  for (const subject of NON_AUTHORITATIVE_IN_CLIENT) {
    assert.equal(clientMayDecide(subject), false, subject);
  }
  assert.equal(clientMayCommitCaseTransition(), false);
  assert.equal(deviationAltersDecision(), false);
});

test("hiding a control is never treated as authorization", () => {
  // The offer function refuses on every guard, and each guard is independent.
  const base = {
    role: "representative" as const,
    required: "mandate_representative" as const,
    assurance: "stepped_up" as const,
    impact: "consequential" as const,
    inScope: true,
    conflictRestricted: false,
    authorityActive: true,
  };
  assert.equal(mayOfferAction(base), true);
  assert.equal(mayOfferAction({ ...base, authorityActive: false }), false);
  assert.equal(mayOfferAction({ ...base, inScope: false }), false);
  assert.equal(mayOfferAction({ ...base, conflictRestricted: true }), false);
  assert.equal(mayOfferAction({ ...base, role: null }), false);
  assert.equal(mayOfferAction({ ...base, assurance: "standard" }), false);
  assert.equal(
    mayOfferAction({ ...base, role: "mandate_staff" }),
    false,
    "staff may not take a representative-only action",
  );
});

/* ------------------------------------------------------------ conflict of interest */

test("a subject can never clear a restriction over themselves", () => {
  for (const role of WS04_ROLES) {
    assert.equal(maySelfClearConflict(role), false, role);
  }
  assert.equal(conflictRegisterClean(), true);
  const ids = CONFLICT_ACTIONS.map((a) => a.actionId);
  for (const forbidden of FORBIDDEN_CONFLICT_ACTION_IDS) {
    assert.ok(!ids.includes(forbidden), forbidden);
  }
});

test("an unreadable restriction register restricts rather than permits", () => {
  const unknown = { known: false as const, reason: "blocked" };
  assert.equal(restrictedFor(unknown, "anything"), true);
  assert.equal(anyRestrictionActive(unknown), true);
  const known = { known: true as const, restrictions: [] };
  assert.equal(restrictedFor(known, "anything"), false);
  assert.equal(anyRestrictionActive(known), false);
});

/* --------------------------------------------------------------------- helpers */

function sourceFiles(): string[] {
  const roots = [
    "app",
    "components",
    "content",
    "domain",
    "policies",
    "runtime",
  ];
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (/\.tsx?$/.test(entry)) out.push(full);
    }
  };
  for (const root of roots) walk(resolve(HERE, root));
  return out;
}
