from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION


def test_canon_version_is_semver_like_string() -> None:
    assert isinstance(CANON_VERSION, str)
    parts = CANON_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_repository_version_is_semver_like_string() -> None:
    assert isinstance(REPOSITORY_VERSION, str)
    parts = REPOSITORY_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_current_versions_match_expected_skeleton_version() -> None:
    # CANON_VERSION moved 0.1.0 -> 0.2.0 per ADR-010 (accepted with
    # amendment): Ballot.challenge_window_hours and
    # ResultPublication.challenge_deadline_at, a backward-compatible
    # (minor) canon addition per canon section 25. CANON_VERSION is
    # unchanged by CLAUDE-PACK-03 (no further canon edit was made).
    # CANON_VERSION moved 0.2.0 -> 0.3.0 per ADR-013 (accepted with
    # amendments): new canon section 19a (Transparency Context) defining
    # PublicLedgerEntry, AuditExportPackage, DisclosurePolicy,
    # LobbyLogEntry, a new section 20.14 event catalog, and four new
    # section 22 ownership-matrix rows - a backward-compatible (minor)
    # canon addition per canon section 25. That earlier round was a
    # canon-only change for CLAUDE-PACK-04 governance; no
    # transparency-service code existed yet, so REPOSITORY_VERSION stayed
    # unchanged at the time.
    # REPOSITORY_VERSION moved 0.2.0 -> 0.3.0 for CLAUDE-PACK-03
    # (Participation and Decision Kernel): six new services, no canon
    # change of its own.
    # REPOSITORY_VERSION moved 0.3.0 -> 0.4.0 for CLAUDE-PACK-04
    # (Transparency Context): implements transparency-service
    # (PublicLedgerEntry/AuditExportPackage/DisclosurePolicy/
    # LobbyLogEntry) against the already-accepted canon 0.3.0 text and
    # ADR-011 through ADR-015 - no further canon edit was made, so
    # CANON_VERSION is unchanged.
    # CANON_VERSION moved 0.3.0 -> 0.4.0 per ADR-018 and ADR-020
    # (both accepted with amendments): new canon section 19b (Governance
    # Context) defining GovernancePolicy, GovernanceDecision,
    # TechnicalChallenge, and integrating the already-existing
    # RoleAssignment (8.4); a new section 20.15 event catalog; three new
    # section 22 ownership-matrix rows; and the reworded/extended section
    # 23 forbidden-link entries (AdministratorRole generalized to any
    # RoleAssignment role_code) - a backward-compatible (minor) canon
    # addition per canon section 25. This round was a canon-only change
    # for CLAUDE-PACK-05 governance; no governance-service code existed
    # yet, so REPOSITORY_VERSION was unchanged at the time.
    # REPOSITORY_VERSION moved 0.4.0 -> 0.5.0 for CLAUDE-PACK-05
    # (Governance Context): implements governance-service
    # (RoleAssignment/GovernancePolicy/GovernanceDecision/
    # TechnicalChallenge) against the already-accepted canon 0.4.0 text
    # and ADR-016 through ADR-020 - no further canon edit was made, so
    # CANON_VERSION is unchanged at that point.
    # CANON_VERSION moved 0.4.0 -> 0.5.0 per ADR-023 and ADR-025 (both
    # accepted with amendments): new canon section 19c (AI Processing
    # Context, an extension of the already-existing section 17) adding
    # AIProcessingRecord.processing_status (six values, no stored
    # superseded), supersedes_ai_processing_record_id (a unified,
    # derived-at-read-time supersession mechanism covering both a
    # superseded processing run and a superseded review outcome), the
    # canonical embedded redaction_manifest value object (nine sub-fields),
    # the disclosure-lifecycle fields plus the derived DisclosureStatus
    # read model, and AIDisclosurePackage as a contract/value object (not
    # a canonical system-of-record entity); a corrected/expanded section
    # 20.12 AI event catalog (ai.output.corrected -> ai.output_corrected,
    # plus six new events); and new section 23 forbidden-link entries - a
    # backward-compatible (minor) canon addition per canon section 25.
    # This round is a canon-only change for CLAUDE-PACK-06 governance; no
    # ai-processing-service code exists yet, so REPOSITORY_VERSION is
    # unchanged at 0.5.0 (both versions now coincidentally match, as they
    # did transiently around PACK-04/PACK-05, but remain tracked
    # independently).
    # REPOSITORY_VERSION moved 0.5.0 -> 0.6.0 for CLAUDE-PACK-06 (AI
    # Processing Context): implements ai-processing-service
    # (AIProcessingRecord/RedactionManifest/AIDisclosurePackage) against
    # the already-accepted canon 0.5.0 text and ADR-021 through ADR-025 -
    # no further canon edit was made, so CANON_VERSION is unchanged at
    # 0.5.0.
    # CANON_VERSION moved 0.5.0 -> 0.6.0 per ADR-026 through ADR-031 (all
    # accepted, no further amendment): new canon section 19d
    # (Participation & Membership Context) adding ten new canonical
    # entities (ParticipantEligibilityPolicy, ProcessEligibilityPolicy,
    # StepUpAuthenticationRequirement, DigitalDecision, AssemblyDecision,
    # PartyMembershipEligibilityPolicy, AffiliationDeclaration,
    # ConflictAssessment, MembershipApplication, AuthenticationContext);
    # eight new IdentityRecord (7.3) fields; the four separated
    # electoral-eligibility claims replacing the generic
    # electoral_eligibility_met concept (never itself canonical); the
    # two-stage MembershipApplication lifecycle layered without
    # overloading Membership.membership_status (8.3, unchanged); the
    # widened seven-category human-control hard invariant; the
    # critical-policy four-gate activation/policy-freeze rule; the
    # enforcement-mechanism dichotomy (atomic capability check / scoped
    # capability token); and ParticipationRightsProfile's internal/
    # non-authoritative characterization - a backward-compatible (minor)
    # canon addition per canon section 25. That round was a canon-only
    # change for CLAUDE-PACK-07 governance; no membership-service or
    # eligibility-service extension code existed yet, so
    # REPOSITORY_VERSION stayed unchanged at 0.6.0 at the time (both
    # versions again coincidentally matched, as they did transiently
    # before, but remain tracked independently).
    # REPOSITORY_VERSION moved 0.6.0 -> 0.7.0 for CLAUDE-PACK-07 (business
    # workflows implementation): implements membership-service (a wholly
    # new service - PartyMembershipEligibilityPolicy, Membership,
    # MembershipApplication, AffiliationDeclaration, ConflictAssessment,
    # its own documented-duplicate Appeal) and extends
    # eligibility-service/identity-service in place
    # (ParticipantEligibilityPolicy, ProcessEligibilityPolicy,
    # StepUpAuthenticationRequirement, DigitalDecision, AssemblyDecision,
    # the four separated electoral-eligibility claims,
    # AuthenticationContext, canon 19d.2's eight IdentityRecord fields)
    # against the already-accepted canon 0.6.0 text and ADR-026 through
    # ADR-031 - no further canon edit was made, so CANON_VERSION was
    # unchanged at 0.6.0 at that point.
    # CANON_VERSION moved 0.6.0 -> 0.7.0 per ADR-032 through ADR-037 (all
    # accepted, ADR-032 through ADR-036 accepted in the PACK-08 spec-
    # correction round, ADR-037 accepted in this canon-amendment round):
    # new canon section 19e (Organization & Regional Scope Context)
    # extending Organization (8.1, six new additive fields) and confirming
    # CivicSpace (8.2, unchanged); four wholly new canonical entities
    # (OrganizationalUnit, OrganizationalRelation,
    # OrganizationalHierarchyOverlapPolicy, OrganizationalInheritancePolicy,
    # OrganizationalAuthority) plus the reusable OrganizationalScope value
    # shape; the multiple-typed-directed-graph relationship model with
    # relation-type-specific cycle/overlap rules; canonical effective
    # dating, reorganization, default-deny regional scope authorization
    # (six access modes), inheritance-policy ownership, the 90-day
    # temporary-supervision default, institutional authority assignments
    # and their minimum non-combinable-role baseline, role/authority
    # lifecycle rules, extended identity-minimization rules, and the
    # six-category RoleAssignment.scope_id classification requirement (8.4
    # itself unchanged in fields/status/owner); thirteen new section 20.5
    # events; five new section 22 ownership-matrix rows; new section 23
    # forbidden-link entries; ten new section 24 reason codes - a
    # backward-compatible (minor) canon addition per canon section 25.
    # This round is a canon-only change for CLAUDE-PACK-08 governance; no
    # organization-service code exists yet, so REPOSITORY_VERSION is
    # unchanged at 0.7.0 (both versions again coincidentally match, as
    # they have at several earlier points, but remain tracked
    # independently).
    # REPOSITORY_VERSION moved 0.7.0 -> 0.8.0 for the CLAUDE-PACK-08
    # IMPLEMENTATION ROUND: implements organization-service (a wholly new
    # service - Organization/OrganizationalUnit/CivicSpace/
    # OrganizationalRelation/OrganizationalHierarchyOverlapPolicy/
    # OrganizationalInheritancePolicy/OrganizationalAuthority, the
    # regional-scope-authorization engine, the role-incompatibility
    # baseline, temporary supervision, and the thirteen canon 20.5 events)
    # against the already-accepted canon 0.7.0 text and ADR-032 through
    # ADR-037 - no further canon edit was made (no canon-owned file was
    # touched this round), so CANON_VERSION is unchanged at 0.7.0.
    # REPOSITORY_VERSION moved 0.8.0 -> 0.9.0 for PACK-09 compliance-service; canon unchanged.
    # CANON_VERSION moved 0.7.0 -> 0.8.0 per ADR-054 (proposed, the
    # PACK-10 canon-amendment round): new canon section 19f (Party
    # Finance & Financial Accountability Context) with twenty-one new
    # canonical entities owned by Finance Service, a forty-five-rule
    # finance-invariant register (FIN-01..FIN-45), four new institutional
    # role codes (finance_administrator, payment_authorizer,
    # payment_executor, report_signatory) extending 19e.15's open list and
    # the 19e.16 incompatibility baseline, the purpose-scoped
    # FinancePartyHandle, the twelve-state Rechenschaftsbericht lifecycle
    # (submission != acknowledgement != acceptance != publication),
    # governed effective-dated finance policies and safe public financial
    # projections; a new section 20.17 with seventy-two finance events;
    # twenty-one new section 22 ownership-matrix rows; new section 23
    # forbidden-link entries; forty-five new section 24 reason codes - a
    # backward-compatible (minor) canon addition per canon section 25.
    # REPOSITORY_VERSION moved 0.9.0 -> 0.10.0 for the PACK-10
    # implementation round: services/finance-service ships the first
    # executable slice of section 19f (twelve modules - the authoritative
    # accounting register, accounting periods, contributions, sponsorship
    # and external financial benefit, expenses and payments, assets and
    # obligations, the reporting perimeter and frozen snapshot, the
    # twelve-state Rechenschaftsbericht lifecycle, the independent audit
    # engagement, all seventy-two canon 20.17 event builders, storage
    # ports with in-memory adapters, publication-safe projections and the
    # command layer), plus contracts/reason-codes/pack-10.yml. A new
    # bounded context is a minor bump per canon section 25. CANON_VERSION
    # is unchanged at 0.8.0: the implementation round amends no canon, and
    # docs/canonical/TZ-00-domain-event-canon.md is untouched.
    # canon-version.json now records
    # finance_context_implementation_status = "reference_implementation" -
    # not "implemented", because the production data plane (durable
    # storage, event bus, bank integration) is PACK-13's, not this
    # round's.
    # REPOSITORY_VERSION moved 0.10.0 -> 0.11.0 for the PACK-11
    # implementation round: services/document-service implements Governed
    # Documents & Evidence - organization-scoped document ownership,
    # immutable cryptographically linked document versions, typed document
    # and evidence references, controlled review and approval, the
    # publication lifecycle with restricted and public projections,
    # correction, supersession and revocation, legal hold, retention
    # metadata, evidence bundles, provenance, complete audit history and
    # scoped authorization with separation of duties - plus
    # contracts/reason-codes/pack-11.yml. A new bounded context is a minor
    # bump per canon section 25.
    # CANON_VERSION remains 0.8.0: PACK-11 made NO canon amendment. No
    # canon-owned file was touched by that round -
    # docs/canonical/TZ-00-domain-event-canon.md is byte-identical to its
    # 0.8.0 text, and canon-version.json changed only its non-canonical
    # bookkeeping fields (repository_compatibility widened to <0.12.0 and
    # the new document_context_implementation_status =
    # "reference_implementation", which is - like finance's - deliberately
    # not "implemented": the production data plane and the real content
    # store remain PACK-13's, not PACK-11's).
    # REPOSITORY_VERSION moved 0.11.0 -> 0.12.0 for the PACK-12
    # implementation round (services/privileged-access-service and
    # contracts/reason-codes/pack-12.yml), and 0.12.0 -> 0.13.0 for the
    # PACK-13 implementation candidate: services/data-plane-service
    # implements Production Data Plane & Contract Evolution in reference
    # form - transactional persistence contracts, optimistic concurrency,
    # scoped idempotency, the canonical schema registry with its
    # format-specific canonicalization and its digest/identity
    # separation, the deterministic compatibility checker, API and event
    # contract evolution, the migration framework and its five automated
    # gates, the backfill runner, the transactional outbox,
    # at-least-once delivery with effectively-once consumer effect,
    # projection governance, the search and export persistence
    # contracts, retention and legal-hold bindings, the PACK-12
    # privileged gates and the structural boundary guards - plus
    # contracts/reason-codes/pack-13.yml. A new bounded context is a
    # minor bump per canon section 25.
    # CANON_VERSION remains 0.8.0: PACK-13 made NO canon amendment, which
    # its own canon assessment records. canon-version.json changed only
    # its non-canonical bookkeeping fields (repository_compatibility
    # widened to <0.14.0 and the new
    # data_plane_context_implementation_status =
    # "reference_implementation" - deliberately not "implemented",
    # because every storage adapter in that service is in memory and the
    # production data plane it specifies is not deployed).
    assert CANON_VERSION == "0.8.0"
    assert REPOSITORY_VERSION == "0.13.0"
