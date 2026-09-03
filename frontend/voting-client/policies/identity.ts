/**
 * The hard voting freeze, expressed as code.
 *
 * No persistent member/person identifier may exist inside the voting domain.
 * The list below is the union of PACK-14's `HANDOFF_FORBIDDEN_FIELDS`, the
 * eligibility-service refusal list, and the identifiers the FRONT-04
 * assignment names.  `assertNoIdentity` is used by the domain layer on every
 * value that crosses into WS-03, so a new identifier cannot arrive silently.
 */

export const FORBIDDEN_IDENTITY_FIELDS = Object.freeze([
  "person_id",
  "person_record_id",
  "member_id",
  "member_number",
  "account_id",
  "account_reference",
  "user_id",
  "profile_id",
  "membership_id",
  "session_id",
  "session_reference",
  "credential_reference",
  "communication_persona_id",
  "device_id",
  "email",
  "phone",
  "correlation_id",
  "trace_id",
  "tracking_id",
] as const);

export type ForbiddenIdentityField = (typeof FORBIDDEN_IDENTITY_FIELDS)[number];

export function isForbiddenIdentityField(name: string): boolean {
  return (FORBIDDEN_IDENTITY_FIELDS as readonly string[]).includes(name);
}

/**
 * Returns the forbidden field names present anywhere in a value, walking plain
 * objects and arrays.  Returns an empty array for a clean value.  This is a
 * detector, not a sanitiser: the callers refuse, they do not strip and
 * continue, because stripping would hide the fact that a boundary leaked.
 */
export function findForbiddenIdentityFields(value: unknown): string[] {
  const found = new Set<string>();
  const seen = new Set<unknown>();
  const walk = (node: unknown): void => {
    if (node === null || typeof node !== "object") return;
    if (seen.has(node)) return;
    seen.add(node);
    if (Array.isArray(node)) {
      for (const item of node) walk(item);
      return;
    }
    for (const [key, child] of Object.entries(
      node as Record<string, unknown>,
    )) {
      if (isForbiddenIdentityField(key)) found.add(key);
      walk(child);
    }
  };
  walk(value);
  return [...found].sort();
}

export class ForbiddenIdentityError extends Error {
  readonly fields: readonly string[];
  constructor(fields: readonly string[]) {
    super("voting domain refused a value carrying persistent identity");
    this.name = "ForbiddenIdentityError";
    this.fields = fields;
  }
}

export function assertNoIdentity<T>(value: T): T {
  const found = findForbiddenIdentityFields(value);
  if (found.length > 0) throw new ForbiddenIdentityError(found);
  return value;
}
