/**
 * Case confidentiality, telemetry and the prohibited-boundary vocabulary.
 *
 * `CASE_CONFIDENTIAL` is the sharpest constraint in this workspace. The rules
 * below are expressed as data so a gate can read them and a mutation can be
 * caught, rather than as review guidance.
 */

/**
 * Field names that carry case or mandate content. A value carrying one of these
 * may not reach browser storage, a URL, a title, telemetry or an error report.
 */
export const CONFIDENTIAL_FIELD_NAMES = Object.freeze([
  "case_body",
  "caseBody",
  "case_content",
  "caseContent",
  "correspondence",
  "correspondence_body",
  "petitioner_name",
  "petitionerName",
  "petitioner_contact",
  "complainant",
  "declaration_body",
  "declarationBody",
  "disclosure_body",
  "position_text",
  "positionText",
  "deviation_text",
  "deviationText",
  "attachment_content",
  "attachment_url",
  "attachmentUrl",
  "storage_url",
  "storageUrl",
  "raw_document",
] as const);

/**
 * Identifiers that would create a correlation handle across workspaces or into
 * the voting domain. These are refused outright.
 */
export const FORBIDDEN_CORRELATION_IDENTIFIERS = Object.freeze([
  "person_id",
  "person_record_id",
  "member_id",
  "member_number",
  "account_id",
  "account_reference",
  "user_id",
  "profile_id",
  "membership_id",
  "citizen_id",
  "global_person_id",
  "cross_workspace_id",
  "correlation_id",
  "trace_id",
  "tracking_id",
  "voter_id",
  "voting_context_id",
  "ballot_id",
  "voting_handoff",
  "confirmation_code",
] as const);

function walk(value: unknown, names: readonly string[]): string[] {
  const found = new Set<string>();
  const seen = new Set<unknown>();
  const visit = (node: unknown): void => {
    if (node === null || typeof node !== "object") return;
    if (seen.has(node)) return;
    seen.add(node);
    if (Array.isArray(node)) {
      for (const item of node) visit(item);
      return;
    }
    for (const [key, child] of Object.entries(
      node as Record<string, unknown>,
    )) {
      if (names.includes(key)) found.add(key);
      visit(child);
    }
  };
  visit(value);
  return [...found].sort();
}

export function findConfidentialFields(value: unknown): string[] {
  return walk(value, CONFIDENTIAL_FIELD_NAMES as readonly string[]);
}

export function findForbiddenCorrelationIdentifiers(value: unknown): string[] {
  return walk(value, FORBIDDEN_CORRELATION_IDENTIFIERS as readonly string[]);
}

export class ConfidentialityError extends Error {
  readonly fields: readonly string[];
  constructor(fields: readonly string[], where: string) {
    super(`refused a value carrying protected content at ${where}`);
    this.name = "ConfidentialityError";
    this.fields = fields;
  }
}

/**
 * Refuse rather than strip. Stripping would let a boundary leak silently and
 * leave the interface believing the value was clean.
 */
export function assertNoConfidentialContent<T>(value: T, where: string): T {
  const confidential = findConfidentialFields(value);
  const correlation = findForbiddenCorrelationIdentifiers(value);
  const found = [...confidential, ...correlation];
  if (found.length > 0) throw new ConfidentialityError(found, where);
  return value;
}

/**
 * Telemetry. The accepted policy allows `workspace-operational` for WS-04, but
 * no analytics platform is connected and no content may be emitted. The
 * allowlist is closed: a field not on it cannot be emitted even in principle.
 */
export const TELEMETRY_ALLOWED_FIELDS = Object.freeze([
  "route_id",
  "capability_status",
  "safe_reason_code",
  "viewport_class",
  "locale",
] as const);

export const TELEMETRY_FORBIDDEN_CONTENT = Object.freeze([
  "case_body",
  "correspondence",
  "declaration_content",
  "position_text",
  "member_identifier",
  "citizen_identifier",
  "access_token",
  "auth_cookie",
  "secret",
  "voting_linked_identifier",
  "free_text",
] as const);

export const TELEMETRY_PLATFORM_CONNECTED = false as const;

export function telemetryFieldPermitted(field: string): boolean {
  return (TELEMETRY_ALLOWED_FIELDS as readonly string[]).includes(field);
}

/**
 * Fails closed. An event is permitted only when a platform is connected — it is
 * not — and only when every field is on the allowlist.
 */
export function validateTelemetryEvent(event: unknown): boolean {
  if (!TELEMETRY_PLATFORM_CONNECTED) return false;
  if (event === null || typeof event !== "object" || Array.isArray(event)) {
    return false;
  }
  return Object.keys(event as Record<string, unknown>).every(
    telemetryFieldPermitted,
  );
}

/** Error reports leave nothing behind either. */
export const ERROR_REPORTING = Object.freeze({
  enabled: false,
  carriesCaseContent: false,
  carriesIdentity: false,
  carriesCorrelationHandle: false,
  carriesStackTraceToUser: false,
} as const);

/**
 * Search. A broad cross-mandate or person search is prohibited; any search must
 * be explicitly scoped, server-authorized, minimised and bounded.
 */
export const SEARCH_POLICY = Object.freeze({
  crossMandateSearch: false,
  personSearch: false,
  enumerationPermitted: false,
  requiresExplicitScope: true,
  requiresServerAuthorization: true,
  maxPageSize: 25,
  clientSideFilteringOfConfidentialSet: false,
} as const);

export function searchScopePermitted(scope: string | null): boolean {
  if (!scope) return false;
  if (scope === "all" || scope === "*" || scope === "global") return false;
  return true;
}
