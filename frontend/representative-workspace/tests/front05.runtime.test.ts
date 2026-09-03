import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

import {
  DEPENDENCY_CLASSES,
  NETWORK_CAPABILITIES,
  WS04_CAPABILITIES,
  anyNetworkCapabilityExecutable,
  blockedCapabilities,
  capabilityExecutable,
  capabilityRecord,
  capabilityStatus,
  securityFindingsComplete,
  securitySensitiveBoundariesRespected,
  securitySensitiveDependencies,
} from "../domain/capabilities";
import {
  PUBLICATION_MODEL_GAP,
  callerAssertedAuthorizationSufficient,
} from "../domain/publication";
import {
  ACCEPTED_LINEAGE,
  BROWSER_AUTHORITY,
  PREDECESSOR_STATE,
  SPECIFICATION_ONLY_OPERATIONS,
  createProductionRuntime,
  productionCapabilitySummary,
} from "../runtime/productionRuntime";
import {
  PRODUCTION_REFUSALS,
  productionRefusal,
  type ProductionRefusalKey,
} from "../runtime/unavailable";
import {
  createGovernedTestRuntime,
  FIXTURE_MARKER,
} from "../runtime/governedTestRuntime";
import { createGovernedTestRuntime as absentFixture } from "../runtime/fixtureAbsent";
import { bindScope } from "../domain/scope";
import { CAPABILITY_STATUSES } from "../domain/types";
import type { MandateSession } from "../domain/types";

const HERE = resolve(import.meta.dirname, "..");

const SESSION: MandateSession = Object.freeze({
  state: "authenticated",
  role: "representative",
  assurance: "standard",
  scope: {
    mandateId: "MANDAT-A",
    organizationId: "ORG-A",
    label: "Mandat A",
    level: "test",
    authorityActive: true,
  },
  displayName: "Test",
  conflictRestricted: false,
});

function bound<T>(value: T) {
  const result = bindScope(SESSION, null, value);
  assert.equal(result.ok, true);
  if (!result.ok) throw new Error("unreachable");
  return result.value;
}

/* --------------------------------------------------------- capability register */

test("every capability carries a status from the closed vocabulary", () => {
  for (const record of WS04_CAPABILITIES) {
    assert.ok(
      (CAPABILITY_STATUSES as readonly string[]).includes(record.status),
      `${record.id}: ${record.status}`,
    );
    assert.ok(record.owner.length > 0, record.id);
    assert.ok(record.reason.length > 0, record.id);
    assert.ok(record.frontendBehaviour.length > 0, record.id);
  }
});

test("every blocked capability names its exact missing dependency", () => {
  for (const record of blockedCapabilities()) {
    assert.ok(
      record.missingDependency.length > 20,
      `${record.id} has no substantive dependency statement`,
    );
  }
});

test("only local capabilities are executable, and they name no dependency", () => {
  const executable = WS04_CAPABILITIES.filter(
    (r) => r.status === "SUPPORTED_REAL_PATH",
  );
  assert.deepEqual(executable.map((r) => r.id).sort(), [
    "governed_fallback",
    "local_refusal_rendering",
    "local_scope_binding",
  ]);
  for (const record of executable) {
    assert.equal(record.missingDependency, "", record.id);
  }
});

test("no network capability is executable at this baseline", () => {
  assert.equal(anyNetworkCapabilityExecutable(), false);
  for (const id of NETWORK_CAPABILITIES) {
    assert.equal(capabilityExecutable(id), false, id);
  }
});

test("the conflict self-clear capability is unsupported, not merely blocked", () => {
  assert.equal(capabilityStatus("conflict_restriction_change"), "UNSUPPORTED");
});

test("an unknown capability identifier throws rather than defaulting", () => {
  assert.throws(
    // @ts-expect-error deliberately outside the union
    () => capabilityRecord("not_a_capability"),
    /no entry/,
  );
});

test("the capability summary matches the register", () => {
  const summary = productionCapabilitySummary();
  assert.equal(summary.total, WS04_CAPABILITIES.length);
  assert.equal(summary.blocked, blockedCapabilities().length);
  assert.equal(summary.executable, 3);
});

/* ---------------------------------------------------------- production adapter */

test("every production port returns a controlled refusal", async () => {
  const api = createProductionRuntime();
  assert.equal(api.profile, "production");
  const calls: Promise<{ ok: boolean }>[] = [
    api.session.current(),
    api.session.observeStepUp(),
    api.session.signOut(),
    api.scope.resolve(),
    api.cases.list(bound({ state: null, page: 1 })),
    api.cases.read(bound({ caseId: "x" })),
    api.cases.search(bound({ query: "x" })),
    api.cases.transition(
      bound({ caseId: "x", event: "close", ifVersion: "1" }),
    ),
    api.cases.reread(bound({ caseId: "x" })),
    api.positions.list(bound({})),
    api.positions.save(bound({ positionId: null, body: "" })),
    api.positions.submitInternal(bound({ positionId: "x", ifVersion: "1" })),
    api.deviations.list(bound({})),
    api.deviations.record(
      bound({
        draft: {
          issue: "x",
          representativePosition: "x",
          referencedDecision: "d",
          explanation: "x".repeat(50),
          supersedes: null,
        },
      }),
    ),
    api.deviations.resolveDecision("d"),
    api.declarations.list(bound({})),
    api.declarations.submit(
      bound({
        draft: {
          kind: "meeting" as const,
          subject: "x",
          occurredAt: "2026-01-01",
          counterparty: "y",
          summary: "",
        },
      }),
    ),
    api.publication.propose(
      bound({ sourceKind: "position" as const, sourceId: "x" }),
    ),
    api.publication.withdraw(bound({ proposalId: "x" })),
    api.publication.observe(bound({ proposalId: "x" })),
    api.conflict.restrictions(bound({})),
    api.conflict.recordAssessmentProposal(
      bound({ restrictionId: "x", note: "" }),
    ),
    api.registry.read(bound({ registry: "membership_register", key: "x" })),
    api.eligibility.observe(bound({ subjectRef: "x" })),
    api.audit.read(bound({ since: "2026-01-01" })),
  ];
  const results = await Promise.all(calls);
  assert.equal(results.length, 25);
  for (const result of results) {
    assert.equal(result.ok, false);
  }
});

test("every production refusal names a capability the register records", () => {
  for (const [key, value] of Object.entries(PRODUCTION_REFUSALS)) {
    const record = capabilityRecord(
      value.capability as Parameters<typeof capabilityRecord>[0],
    );
    assert.equal(
      record.status,
      "BLOCKED_BY_DEPENDENCY",
      `${key} claims a capability that is not blocked`,
    );
  }
});

test("every refusal carries a message, a commit statement and a next step", () => {
  for (const key of Object.keys(
    PRODUCTION_REFUSALS,
  ) as ProductionRefusalKey[]) {
    const refusal = productionRefusal(key);
    assert.ok(refusal.safeMessage.length > 0, key);
    assert.ok(refusal.nextSafeAction.length > 0, key);
    assert.ok(
      ["committed", "not_committed", "unknown"].includes(refusal.committed),
      key,
    );
    assert.ok(refusal.reasonCode.startsWith("WS04_"), key);
  }
});

test("a refusal never claims a commit it cannot know about", () => {
  // Reads and blocked writes know nothing was committed; the two status
  // observations legitimately cannot know, and say so.
  assert.equal(productionRefusal("caseMutation").committed, "not_committed");
  assert.equal(productionRefusal("publicationState").committed, "unknown");
});

test("the case-detail refusal is non-disclosing", () => {
  assert.equal(productionRefusal("caseDetail").nonDisclosing, true);
});

test("no source file in the production path issues a network request", () => {
  const offenders: string[] = [];
  const patterns = [
    /\bfetch\s*\(/,
    /XMLHttpRequest/,
    /new\s+WebSocket/,
    /EventSource/,
    /axios/,
    /https?:\/\/(?!represent\.epd\.example)/,
  ];
  for (const file of sourceFiles()) {
    if (file.includes("/tests/")) continue;
    const text = readFileSync(file, "utf8");
    for (const pattern of patterns) {
      if (pattern.test(text)) offenders.push(`${file}: ${pattern}`);
    }
  }
  assert.deepEqual(offenders, []);
});

test("the adapter carries no service-to-service authority", () => {
  for (const [name, value] of Object.entries(BROWSER_AUTHORITY)) {
    assert.equal(value, false, name);
  }
});

test("the pinned lineage matches the accepted FRONT-04 C2 record", () => {
  assert.equal(
    ACCEPTED_LINEAGE.front04C2Sha256,
    "1ac87914a30e589b4059e3b7c74e0a0fd940a78cecbe7f06de299421c8da55f8",
  );
  assert.equal(
    ACCEPTED_LINEAGE.front04C2SourceTreeDigest,
    "eee6bf1e80f9e5b5ce18618611513b871b195a163e98948d55d99f61276f2f2e",
  );
  assert.equal(ACCEPTED_LINEAGE.front04C2AuthoritativeRun, 33569268417);
  assert.equal(PREDECESSOR_STATE.CTRL, "NOT_STARTED");
  assert.equal(PREDECESSOR_STATE.INFRA, "NOT_STARTED");
});

test("the specification-only operations are recorded but never called", () => {
  assert.ok(SPECIFICATION_ONLY_OPERATIONS.length >= 15);
  const adapter = readFileSync(
    resolve(HERE, "runtime/productionRuntime.ts"),
    "utf8",
  );
  // Each appears exactly once, as a quoted literal inside the record.
  for (const operation of SPECIFICATION_ONLY_OPERATIONS) {
    const occurrences = adapter.split(`"${operation}"`).length - 1;
    assert.equal(occurrences, 1, `${operation} appears ${occurrences} times`);
  }
  assert.ok(adapter.includes("SPECIFICATION_ONLY_OPERATIONS"));

  // And no other source file mentions a representative path at all, so none of
  // them can be assembled into a request somewhere else.
  const offenders: string[] = [];
  for (const file of sourceFiles()) {
    if (file.includes("/tests/")) continue;
    if (file.endsWith("runtime/productionRuntime.ts")) continue;
    if (readFileSync(file, "utf8").includes("/representative/mandates/")) {
      offenders.push(file);
    }
  }
  assert.deepEqual(offenders, []);
});

/* ------------------------------------------------------------ governed profile */

test("the governed profile reads prototype material and commits nothing", async () => {
  const api = createGovernedTestRuntime();
  assert.equal(api.profile, "governed_test");

  const cases = await api.cases.list(bound({ state: null, page: 1 }));
  assert.equal(cases.ok, true);

  // Every mutation returns exactly the production refusal.
  const mutations = await Promise.all([
    api.cases.transition(
      bound({ caseId: "x", event: "close", ifVersion: "1" }),
    ),
    api.positions.save(bound({ positionId: null, body: "" })),
    api.positions.submitInternal(bound({ positionId: "x", ifVersion: "1" })),
    api.declarations.submit(
      bound({
        draft: {
          kind: "meeting" as const,
          subject: "x",
          occurredAt: "2026-01-01",
          counterparty: "y",
          summary: "",
        },
      }),
    ),
    api.publication.propose(
      bound({ sourceKind: "position" as const, sourceId: "x" }),
    ),
    api.conflict.recordAssessmentProposal(
      bound({ restrictionId: "x", note: "" }),
    ),
    api.cases.search(bound({ query: "x" })),
    api.deviations.record(
      bound({
        draft: {
          issue: "x",
          representativePosition: "x",
          referencedDecision: "d",
          explanation: "x".repeat(50),
          supersedes: null,
        },
      }),
    ),
  ]);
  for (const result of mutations) {
    assert.equal(result.ok, false);
  }
});

test("all fixture material is marked as prototype", async () => {
  const api = createGovernedTestRuntime();
  const cases = await api.cases.list(bound({ state: null, page: 1 }));
  assert.equal(cases.ok, true);
  if (!cases.ok) return;
  for (const item of cases.value) {
    assert.ok(item.caseId.startsWith("PROTOTYP"), item.caseId);
    assert.ok(item.reference.startsWith("PROTOTYP"), item.reference);
    assert.ok(item.mandateId.startsWith("PROTOTYP"), item.mandateId);
  }
  const detail = await api.cases.read(
    bound({ caseId: "PROTOTYP-VORGANG-0001" }),
  );
  assert.equal(detail.ok, true);
  if (!detail.ok) return;
  assert.match(detail.value.summaryText, /Prototyp/);
  assert.match(detail.value.summaryText, /kein reales/);
});

test("the fixture never reaches a proposal approval", async () => {
  const api = createGovernedTestRuntime();
  const proposal = await api.publication.observe(bound({ proposalId: "x" }));
  assert.equal(proposal.ok, true);
  if (!proposal.ok) return;
  assert.notEqual(proposal.value.state, "approved_by_publication_authority");
  assert.equal(proposal.value.decidedBy, null);
});

test("the fixture replacement refuses rather than degrading", () => {
  assert.throws(() => absentFixture(), /WS04_FIXTURE_ABSENT_IN_PRODUCTION/);
});

test("the fixture marker exists so a build can be scanned for it", () => {
  assert.equal(FIXTURE_MARKER, "EPD2_FRONT05_GOVERNED_TEST_FIXTURE_MARKER");
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

/* ------------------------------------------- security-sensitive dependencies */

/**
 * A missing dependency and a defective one are different findings, and the
 * difference is not cosmetic. `transparency-service` authorises publication by
 * a caller-supplied `actor_is_authorized` boolean — the caller declares its own
 * permission and the service accepts it. Reading that as "not built yet" would
 * invite a future change to wire up a route and call the capability supported,
 * inheriting the defect. The tests below make the distinction binding.
 */

test("the caller-asserted authorization boundary is classified, not merely noted", () => {
  const flagged = securitySensitiveDependencies()
    .map((r) => r.id)
    .sort();
  assert.deepEqual(flagged, [
    "publication_proposal_submission",
    "publication_state_observation",
  ]);
});

test("every capability carries a dependency class from the closed vocabulary", () => {
  for (const record of WS04_CAPABILITIES) {
    assert.ok(
      (DEPENDENCY_CLASSES as readonly string[]).includes(
        record.dependencyClass,
      ),
      `${record.id}: ${record.dependencyClass}`,
    );
  }
  // A prohibition is classified as one, never as an absence.
  assert.equal(
    capabilityRecord("conflict_restriction_change").dependencyClass,
    "PROHIBITED",
  );
});

test("a security-sensitive dependency can never be a supported real path", () => {
  assert.equal(securitySensitiveBoundariesRespected(), true);
  for (const record of securitySensitiveDependencies()) {
    assert.ok(
      record.status === "BLOCKED_BY_DEPENDENCY" ||
        record.status === "UNSUPPORTED",
      `${record.id} is ${record.status}`,
    );
    assert.notEqual(record.status, "SUPPORTED_REAL_PATH", record.id);
    // A declared limitation is the wrong vocabulary here: there is no bound
    // inside which a self-asserted authorization is safe.
    assert.notEqual(
      record.status,
      "SUPPORTED_WITH_DECLARED_LIMITATION",
      record.id,
    );
  }
});

test("every security-sensitive boundary states an actionable finding", () => {
  assert.equal(securityFindingsComplete(), true);
  for (const record of securitySensitiveDependencies()) {
    const finding = record.securityFinding ?? "";
    // Each finding must name the thing that is actually absent: either the
    // authorization itself, or the authority that should have decided.
    assert.match(finding, /authoriz\w*|authorit\w*/i, record.id);
    // And it must say what this workspace does about it, not merely diagnose.
    assert.match(finding, /must not|does not|treats|remains|stays/i, record.id);
  }
});

test("no capability outside the flagged set claims a security finding", () => {
  for (const record of WS04_CAPABILITIES) {
    if (record.dependencyClass === "SECURITY_SENSITIVE_BOUNDARY") continue;
    assert.equal(record.securityFinding, undefined, record.id);
  }
});

test("a caller-asserted authorization is never sufficient", () => {
  assert.equal(callerAssertedAuthorizationSufficient(), false);
  assert.equal(
    PUBLICATION_MODEL_GAP.classification,
    "SECURITY_SENSITIVE_BOUNDARY",
  );
  assert.match(PUBLICATION_MODEL_GAP.securityFinding, /self-asserted/);
  assert.match(PUBLICATION_MODEL_GAP.disposition, /SECURITY-RELEVANT/);
  assert.match(PUBLICATION_MODEL_GAP.disposition, /BLOCKED_BY_DEPENDENCY/);
});

test("the insufficient remedies are named, so none can be mistaken for a fix", () => {
  const remedies = PUBLICATION_MODEL_GAP.insufficientRemedies;
  assert.ok(remedies.length >= 4);
  // The specific trap: adding the route without fixing the authorization.
  assert.ok(
    remedies.some((r) => /proposal route while authorization stays/.test(r)),
  );
  // And the specific misclassification the status vocabulary invites.
  assert.ok(remedies.some((r) => /SUPPORTED_WITH_DECLARED_LIMITATION/.test(r)));
});

test("no port signature carries a caller-supplied authorization flag", () => {
  // The defect cannot be inherited if there is nowhere to put it.
  const forbidden = [
    "actor_is_authorized",
    "actorIsAuthorized",
    "isAuthorized",
    "authorized: true",
    "authorised: true",
  ];
  const offenders: string[] = [];
  for (const file of sourceFiles()) {
    const text = readFileSync(file, "utf8");
    for (const name of forbidden) {
      // The name may be discussed in prose; it may not appear as a code token.
      const asToken = new RegExp(
        `[^\\w"'\`]${name.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}\\\\s*[:,)=]`,
      );
      if (asToken.test(text)) offenders.push(`${file}: ${name}`);
    }
  }
  assert.deepEqual(offenders, []);
});
