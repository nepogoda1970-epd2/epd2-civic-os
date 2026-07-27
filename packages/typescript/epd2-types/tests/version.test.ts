import assert from "node:assert/strict";
import { test } from "node:test";

import { CANON_VERSION, REPOSITORY_VERSION } from "../src/version.js";

test("CANON_VERSION is a semver-like string", () => {
  assert.equal(typeof CANON_VERSION, "string");
  const parts = CANON_VERSION.split(".");
  assert.equal(parts.length, 3);
  for (const part of parts) {
    assert.ok(/^\d+$/.test(part), `expected numeric segment, got "${part}"`);
  }
});

test("REPOSITORY_VERSION is a semver-like string", () => {
  assert.equal(typeof REPOSITORY_VERSION, "string");
  const parts = REPOSITORY_VERSION.split(".");
  assert.equal(parts.length, 3);
  for (const part of parts) {
    assert.ok(/^\d+$/.test(part), `expected numeric segment, got "${part}"`);
  }
});

test("current versions match the expected skeleton version", () => {
  // CANON_VERSION moved 0.1.0 -> 0.2.0 per ADR-010 (accepted with
  // amendment): Ballot.challenge_window_hours and
  // ResultPublication.challenge_deadline_at, a backward-compatible
  // (minor) canon addition per canon section 25. CANON_VERSION is
  // unchanged by CLAUDE-PACK-03 (no further canon edit was made).
  // CANON_VERSION moved 0.2.0 -> 0.3.0 per ADR-013 (accepted with
  // amendments): new canon section 19a (Transparency Context) defining
  // PublicLedgerEntry, AuditExportPackage, DisclosurePolicy,
  // LobbyLogEntry, a new section 20.14 event catalog, and four new
  // section 22 ownership-matrix rows - a backward-compatible (minor)
  // canon addition per canon section 25. That earlier round was a
  // canon-only change for CLAUDE-PACK-04 governance; no
  // transparency-service code existed yet, so REPOSITORY_VERSION stayed
  // unchanged at the time.
  // REPOSITORY_VERSION moved 0.2.0 -> 0.3.0 for CLAUDE-PACK-03
  // (Participation and Decision Kernel): six new services, no canon
  // change of its own.
  // REPOSITORY_VERSION moved 0.3.0 -> 0.4.0 for CLAUDE-PACK-04
  // (Transparency Context): implements transparency-service
  // (PublicLedgerEntry/AuditExportPackage/DisclosurePolicy/
  // LobbyLogEntry) against the already-accepted canon 0.3.0 text and
  // ADR-011 through ADR-015 - no further canon edit was made, so
  // CANON_VERSION is unchanged.
  // CANON_VERSION moved 0.3.0 -> 0.4.0 per ADR-018 and ADR-020 (both
  // accepted with amendments): new canon section 19b (Governance
  // Context) defining GovernancePolicy, GovernanceDecision,
  // TechnicalChallenge, and integrating the already-existing
  // RoleAssignment (8.4); a new section 20.15 event catalog; three new
  // section 22 ownership-matrix rows; and the reworded/extended section
  // 23 forbidden-link entries (AdministratorRole generalized to any
  // RoleAssignment role_code) - a backward-compatible (minor) canon
  // addition per canon section 25. This round was a canon-only change
  // for CLAUDE-PACK-05 governance; no governance-service code existed
  // yet, so REPOSITORY_VERSION was unchanged at the time.
  // REPOSITORY_VERSION moved 0.4.0 -> 0.5.0 for CLAUDE-PACK-05
  // (Governance Context): implements governance-service
  // (RoleAssignment/GovernancePolicy/GovernanceDecision/
  // TechnicalChallenge) against the already-accepted canon 0.4.0 text
  // and ADR-016 through ADR-020 - no further canon edit was made, so
  // CANON_VERSION is unchanged.
  // CANON_VERSION moved 0.4.0 -> 0.5.0 per ADR-023 and ADR-025 (both
  // accepted with amendments): new canon section 19c (AI Processing
  // Context), extending the already-existing section 17
  // (AIProcessingRecord) with an independent processing_status field
  // kept structurally separate from human_review_status, a unified
  // supersedes_ai_processing_record_id field, a redaction_manifest
  // embedded value object, and disclosure-lifecycle fields - a
  // backward-compatible (minor) canon addition per canon section 25.
  // REPOSITORY_VERSION moved 0.5.0 -> 0.6.0 for CLAUDE-PACK-06 (AI
  // Processing Context): implements ai-processing-service
  // (AIProcessingRecord's processing_status/human_review_status split,
  // redaction_manifest, disclosure lifecycle) against the
  // already-accepted canon 0.5.0 text and ADR-021 through ADR-025 - no
  // further canon edit was made beyond ADR-023/ADR-025 above, so
  // CANON_VERSION is unchanged by this repository-side bump itself.
  // CANON_VERSION moved 0.5.0 -> 0.6.0 per ADR-026 through ADR-031 (all
  // accepted, no further amendment): new canon section 19d
  // (Participation & Membership Context) adding ten new canonical
  // entities (ParticipantEligibilityPolicy, ProcessEligibilityPolicy,
  // StepUpAuthenticationRequirement, DigitalDecision, AssemblyDecision,
  // PartyMembershipEligibilityPolicy, AffiliationDeclaration,
  // ConflictAssessment, MembershipApplication, AuthenticationContext),
  // eight new IdentityRecord fields, the four separated
  // electoral-eligibility claims, the two-stage MembershipApplication
  // lifecycle, the widened seven-category human-control hard invariant,
  // the critical-policy four-gate activation/policy-freeze rule, the
  // enforcement-mechanism dichotomy, and ParticipationRightsProfile's
  // internal/non-authoritative characterization - a backward-compatible
  // (minor) canon addition. That round was a canon-only change for
  // CLAUDE-PACK-07 governance; no membership-service or
  // eligibility-service extension code existed yet, so
  // REPOSITORY_VERSION stayed unchanged at 0.6.0 at the time.
  // REPOSITORY_VERSION moved 0.6.0 -> 0.7.0 for CLAUDE-PACK-07 (business
  // workflows implementation): implements membership-service (a wholly
  // new service - PartyMembershipEligibilityPolicy, Membership,
  // MembershipApplication, AffiliationDeclaration, ConflictAssessment,
  // its own Appeal) and extends eligibility-service/identity-service in
  // place (ParticipantEligibilityPolicy, ProcessEligibilityPolicy,
  // StepUpAuthenticationRequirement, DigitalDecision, AssemblyDecision,
  // the four separated electoral-eligibility claims,
  // AuthenticationContext, canon 19d.2's eight IdentityRecord fields)
  // against the already-accepted canon 0.6.0 text and ADR-026 through
  // ADR-031 - no further canon edit was made, so CANON_VERSION was
  // unchanged by this repository-side bump, at 0.6.0.
  // CANON_VERSION moved 0.6.0 -> 0.7.0 per ADR-032 through ADR-037 (all
  // accepted): new canon section 19e (Organization & Regional Scope
  // Context) extending Organization (8.1) and confirming CivicSpace
  // (8.2, unchanged); four new canonical entities (OrganizationalUnit,
  // OrganizationalRelation, OrganizationalHierarchyOverlapPolicy,
  // OrganizationalInheritancePolicy) plus OrganizationalAuthority and the
  // reusable OrganizationalScope value shape; multiple-typed-directed-
  // graph relationships; effective dating; reorganization rules;
  // default-deny regional scope authorization; inheritance-policy
  // ownership; the 90-day temporary-supervision default; institutional
  // authority assignments and their non-combinable-role baseline; role/
  // authority lifecycle rules; extended identity minimization; and the
  // RoleAssignment.scope_id six-category classification requirement
  // (8.4 itself unchanged) - a backward-compatible (minor) canon
  // addition. This round is a canon-only change for CLAUDE-PACK-08
  // governance; no organization-service code exists yet, so
  // REPOSITORY_VERSION is unchanged at 0.7.0.
  // REPOSITORY_VERSION moved 0.7.0 -> 0.8.0 for the CLAUDE-PACK-08
  // IMPLEMENTATION ROUND: implements organization-service (a wholly new
  // service - Organization/OrganizationalUnit/CivicSpace/
  // OrganizationalRelation/OrganizationalHierarchyOverlapPolicy/
  // OrganizationalInheritancePolicy/OrganizationalAuthority, the
  // regional-scope-authorization engine, the role-incompatibility
  // baseline, temporary supervision, and the thirteen canon 20.5 events)
  // against the already-accepted canon 0.7.0 text and ADR-032 through
  // ADR-037 - no further canon edit was made (no canon-owned file was
  // touched this round), so CANON_VERSION is unchanged at 0.7.0.
  // CANON_VERSION moved 0.7.0 -> 0.8.0 per ADR-054 (proposed, the
  // PACK-10 canon-amendment round): new canon section 19f (Party Finance
  // & Financial Accountability Context) with twenty-one new canonical
  // entities owned by Finance Service, a forty-five-rule finance-invariant
  // register, four new institutional role codes, the purpose-scoped
  // FinancePartyHandle, the twelve-state Rechenschaftsbericht lifecycle,
  // governed effective-dated finance policies and safe public financial
  // projections; a new section 20.17 with seventy-two finance events;
  // twenty-one new section 22 ownership-matrix rows; new section 23
  // forbidden-link entries; forty-five new section 24 reason codes - a
  // backward-compatible (minor) canon addition per canon section 25. No
  // finance-service code exists, so REPOSITORY_VERSION is unchanged at
  // 0.9.0.
  assert.equal(CANON_VERSION, "0.8.0");
  assert.equal(REPOSITORY_VERSION, "0.9.0");
});
