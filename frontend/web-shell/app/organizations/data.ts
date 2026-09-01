/**
 * PACK-08 frontend vertical slice — static sample data only.
 *
 * There is no running organization-service HTTP API in this repository
 * (see contracts/openapi/pack-08.yaml's own "minimal reference APIs only"
 * scope note and services/organization-service/README.md). This module is
 * therefore NOT a client for any real backend: it is a small, hand-written,
 * internally-consistent sample dataset that mirrors the exact canon 19e /
 * ADR-032 through ADR-037 field names used by
 * services/organization-service/src/epd2_organization_service/domain.py,
 * so the pages under app/organizations/ have something realistic to render
 * without ever performing a fetch() call.
 *
 * Field names, enum values, and status-transition shapes below are taken
 * directly from that domain module. Nothing here invents new authority,
 * grants, or roles beyond what is explicitly listed — the sample data is
 * deliberately sparse rather than exhaustive, per this slice's "no
 * authority inference" requirement: the UI only ever displays what is
 * explicitly present in this dataset, never a derived or assumed grant.
 */

export type OrganizationStatus = "draft" | "active" | "restricted" | "archived";

export interface SampleOrganization {
  organization_id: string;
  name: string;
  legal_operator: string;
  organization_type: string;
  status: OrganizationStatus;
  default_policy_version: string;
  organization_profile: string;
  effective_from: string;
  effective_until: string | null;
  dissolved_at: string | null;
  successor_reference: string | null;
  parent_reference: string | null;
  /** Not a canon field — sample-data-only history for the "as of" selector below. */
  status_history: Array<{ status: OrganizationStatus; effective_from: string }>;
}

export type RelationType =
  | "parent_of"
  | "subordinate_to"
  | "affiliated_with"
  | "successor_of"
  | "merged_into"
  | "split_from"
  | "temporary_supervision_by"
  | "operates_within"
  | "participates_in";

export type RelationCategory = "hierarchy" | "continuity" | "cooperation";

export const RELATION_CATEGORY_BY_TYPE: Record<RelationType, RelationCategory> =
  {
    parent_of: "hierarchy",
    subordinate_to: "hierarchy",
    successor_of: "continuity",
    merged_into: "continuity",
    split_from: "continuity",
    affiliated_with: "cooperation",
    temporary_supervision_by: "cooperation",
    operates_within: "cooperation",
    participates_in: "cooperation",
  };

export type RelationStatus = "draft" | "active" | "superseded" | "ended";

export interface SampleRelation {
  relation_id: string;
  relation_version: number;
  relation_type: RelationType;
  source_organization_id: string;
  target_organization_id: string;
  status: RelationStatus;
  valid_from: string;
  valid_until: string | null;
}

export type InstitutionalRole =
  | "dpo"
  | "election_board_member"
  | "election_officer"
  | "independent_auditor"
  | "finance_auditor"
  | "party_arbitrator"
  | "organizational_administrator";

export type AuthorityStatus = "proposed" | "active" | "revoked" | "expired";

export type ScopeType =
  | "organization_scope"
  | "jurisdiction_scope"
  | "civic_space_scope"
  | "process_scope";

export interface SampleAuthority {
  authority_id: string;
  authority_version: number;
  role_code: InstitutionalRole | string;
  scope_type: ScopeType;
  scope_reference: string;
  assigned_subject_reference: string;
  valid_from: string;
  valid_until: string | null;
  status: AuthorityStatus;
  grants_procedural_authority: boolean;
  grants_data_access: boolean;
}

export type AccessMode =
  | "exact_scope"
  | "ancestor_scope"
  | "descendant_scope"
  | "delegated_cross_scope"
  | "temporary_supervision"
  | "institutional_oversight_without_data_access";

/**
 * A single, explicit, sample regional-scope access grant. Mirrors
 * `RegionalScopeAccessDecision` / `check_regional_scope_access`'s default-deny
 * shape (canon 19e.12): if no grant below matches, access is denied — the
 * dev console never infers a grant that is not listed here.
 */
export interface SampleAccessGrant {
  grant_id: string;
  subject_reference: string;
  mode: AccessMode;
  scope_type: ScopeType;
  scope_reference: string;
  action_code: string;
  valid_from: string;
  valid_until: string | null;
}

export const SAMPLE_ORGANIZATIONS: SampleOrganization[] = [
  {
    organization_id: "00000000-0000-0000-0000-000000000001",
    name: "EPD² Bundesverband",
    legal_operator: "EPD² e.V.",
    organization_type: "party_federal",
    status: "active",
    default_policy_version: "1.0",
    organization_profile: "national umbrella organization",
    effective_from: "2024-01-01T00:00:00+00:00",
    effective_until: null,
    dissolved_at: null,
    successor_reference: null,
    parent_reference: null,
    status_history: [
      { status: "draft", effective_from: "2023-10-01T00:00:00+00:00" },
      { status: "active", effective_from: "2024-01-01T00:00:00+00:00" },
    ],
  },
  {
    organization_id: "00000000-0000-0000-0000-000000000002",
    name: "EPD² Landesverband Bayern",
    legal_operator: "EPD² e.V.",
    organization_type: "party_regional",
    status: "active",
    default_policy_version: "1.0",
    organization_profile: "regional chapter, Bavaria",
    effective_from: "2024-02-01T00:00:00+00:00",
    effective_until: null,
    dissolved_at: null,
    successor_reference: null,
    parent_reference: "00000000-0000-0000-0000-000000000001",
    status_history: [
      { status: "draft", effective_from: "2024-01-15T00:00:00+00:00" },
      { status: "active", effective_from: "2024-02-01T00:00:00+00:00" },
    ],
  },
  {
    organization_id: "00000000-0000-0000-0000-000000000003",
    name: "EPD² Kreisverband München",
    legal_operator: "EPD² e.V.",
    organization_type: "party_local",
    status: "restricted",
    default_policy_version: "1.0",
    organization_profile: "local chapter, Munich",
    effective_from: "2024-03-01T00:00:00+00:00",
    effective_until: null,
    dissolved_at: null,
    successor_reference: null,
    parent_reference: "00000000-0000-0000-0000-000000000002",
    status_history: [
      { status: "draft", effective_from: "2024-02-15T00:00:00+00:00" },
      { status: "active", effective_from: "2024-03-01T00:00:00+00:00" },
      { status: "restricted", effective_from: "2026-05-01T00:00:00+00:00" },
    ],
  },
  {
    organization_id: "00000000-0000-0000-0000-000000000004",
    name: "EPD² Kreisverband München (Vorgänger)",
    legal_operator: "EPD² e.V.",
    organization_type: "party_local",
    status: "archived",
    default_policy_version: "1.0",
    organization_profile:
      "predecessor local chapter, dissolved after reorganization",
    effective_from: "2023-06-01T00:00:00+00:00",
    effective_until: "2024-03-01T00:00:00+00:00",
    dissolved_at: "2024-03-01T00:00:00+00:00",
    successor_reference: "00000000-0000-0000-0000-000000000003",
    parent_reference: "00000000-0000-0000-0000-000000000002",
    status_history: [
      { status: "draft", effective_from: "2023-05-15T00:00:00+00:00" },
      { status: "active", effective_from: "2023-06-01T00:00:00+00:00" },
      { status: "archived", effective_from: "2024-03-01T00:00:00+00:00" },
    ],
  },
];

export const SAMPLE_RELATIONS: SampleRelation[] = [
  {
    relation_id: "10000000-0000-0000-0000-000000000001",
    relation_version: 1,
    relation_type: "parent_of",
    source_organization_id: "00000000-0000-0000-0000-000000000001",
    target_organization_id: "00000000-0000-0000-0000-000000000002",
    status: "active",
    valid_from: "2024-02-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    relation_id: "10000000-0000-0000-0000-000000000002",
    relation_version: 1,
    relation_type: "parent_of",
    source_organization_id: "00000000-0000-0000-0000-000000000002",
    target_organization_id: "00000000-0000-0000-0000-000000000003",
    status: "active",
    valid_from: "2024-03-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    relation_id: "10000000-0000-0000-0000-000000000003",
    relation_version: 1,
    relation_type: "successor_of",
    source_organization_id: "00000000-0000-0000-0000-000000000003",
    target_organization_id: "00000000-0000-0000-0000-000000000004",
    status: "active",
    valid_from: "2024-03-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    relation_id: "10000000-0000-0000-0000-000000000004",
    relation_version: 1,
    relation_type: "temporary_supervision_by",
    source_organization_id: "00000000-0000-0000-0000-000000000002",
    target_organization_id: "00000000-0000-0000-0000-000000000003",
    status: "active",
    valid_from: "2026-05-01T00:00:00+00:00",
    valid_until: "2026-07-29T00:00:00+00:00",
  },
];

export const SAMPLE_AUTHORITIES: SampleAuthority[] = [
  {
    authority_id: "20000000-0000-0000-0000-000000000001",
    authority_version: 1,
    role_code: "organizational_administrator",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000002",
    assigned_subject_reference: "30000000-0000-0000-0000-000000000001",
    valid_from: "2024-02-01T00:00:00+00:00",
    valid_until: null,
    status: "active",
    grants_procedural_authority: true,
    grants_data_access: false,
  },
  {
    authority_id: "20000000-0000-0000-0000-000000000002",
    authority_version: 1,
    role_code: "independent_auditor",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000001",
    assigned_subject_reference: "30000000-0000-0000-0000-000000000002",
    valid_from: "2024-01-01T00:00:00+00:00",
    valid_until: null,
    status: "active",
    grants_procedural_authority: false,
    grants_data_access: false,
  },
  {
    authority_id: "20000000-0000-0000-0000-000000000003",
    authority_version: 1,
    role_code: "dpo",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000001",
    assigned_subject_reference: "30000000-0000-0000-0000-000000000003",
    valid_from: "2024-01-01T00:00:00+00:00",
    valid_until: null,
    status: "active",
    grants_procedural_authority: false,
    grants_data_access: true,
  },
];

/**
 * Explicit, narrow sample grants for the development authorization console.
 * Deliberately small and default-deny: any (subject, scope, action) triple
 * not listed here is DENIED, never inferred from an unrelated grant.
 */
export const SAMPLE_ACCESS_GRANTS: SampleAccessGrant[] = [
  {
    grant_id: "40000000-0000-0000-0000-000000000001",
    subject_reference: "30000000-0000-0000-0000-000000000001",
    mode: "exact_scope",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000002",
    action_code: "view_organizational_relation",
    valid_from: "2024-02-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    grant_id: "40000000-0000-0000-0000-000000000002",
    subject_reference: "30000000-0000-0000-0000-000000000001",
    mode: "descendant_scope",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000002",
    action_code: "view_organizational_relation",
    valid_from: "2024-02-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    grant_id: "40000000-0000-0000-0000-000000000003",
    subject_reference: "30000000-0000-0000-0000-000000000002",
    mode: "institutional_oversight_without_data_access",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000001",
    action_code: "view_organizational_relation",
    valid_from: "2024-01-01T00:00:00+00:00",
    valid_until: null,
  },
  {
    grant_id: "40000000-0000-0000-0000-000000000004",
    subject_reference: "30000000-0000-0000-0000-000000000004",
    mode: "temporary_supervision",
    scope_type: "organization_scope",
    scope_reference: "00000000-0000-0000-0000-000000000003",
    action_code: "view_organizational_relation",
    valid_from: "2026-05-01T00:00:00+00:00",
    valid_until: "2026-07-29T00:00:00+00:00",
  },
];

export function findOrganization(id: string): SampleOrganization | undefined {
  return SAMPLE_ORGANIZATIONS.find(
    (organization) => organization.organization_id === id,
  );
}

export function relationsForOrganization(id: string): SampleRelation[] {
  return SAMPLE_RELATIONS.filter(
    (relation) =>
      relation.source_organization_id === id ||
      relation.target_organization_id === id,
  );
}

export function authoritiesForScope(organizationId: string): SampleAuthority[] {
  return SAMPLE_AUTHORITIES.filter(
    (authority) =>
      authority.scope_type === "organization_scope" &&
      authority.scope_reference === organizationId,
  );
}

/**
 * Sample-data-only helper for the "current / historical state" selector:
 * resolves which status was in effect at `asOf` from `status_history`,
 * mirroring the pattern of an `as_of` read (see contracts/openapi/pack-08.yaml's
 * `getOrganization`/`getCivicSpace` operations), without calling any API.
 */
export function statusAsOf(
  organization: Pick<SampleOrganization, "status_history">,
  asOf: string,
): OrganizationStatus {
  const asOfTime = new Date(asOf).getTime();
  let resolved = organization.status_history[0].status;
  for (const entry of organization.status_history) {
    if (new Date(entry.effective_from).getTime() <= asOfTime) {
      resolved = entry.status;
    }
  }
  return resolved;
}
