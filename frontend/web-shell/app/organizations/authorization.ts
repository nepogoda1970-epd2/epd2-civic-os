/**
 * PACK-08 frontend vertical slice — development authorization test console
 * logic.
 *
 * This is a narrow, client-side-only re-implementation of the SHAPE of
 * canon 19e.12's default-deny regional scope access check
 * (`check_regional_scope_access` /
 * services/organization-service/src/epd2_organization_service/application.py`),
 * for demonstration/testing of the six access modes against the static
 * sample grants in data.ts. It is not the real authorization engine, calls
 * no API, and makes no production authorization decision — see the console
 * page's own "development only" banner. It deliberately never infers a
 * grant beyond what is explicitly listed in SAMPLE_ACCESS_GRANTS: any
 * (subject, scope, action) combination with no matching grant is DENIED.
 */

import type { AccessMode, SampleAccessGrant, ScopeType } from "./data";
import { SAMPLE_ACCESS_GRANTS } from "./data";

export interface AuthorizationCheckInput {
  subjectReference: string;
  scopeType: ScopeType;
  scopeReference: string;
  actionCode: string;
  asOf: string;
}

export interface AuthorizationCheckResult {
  allowed: boolean;
  reasonCode: string;
  mode: AccessMode | null;
  matchedGrant: SampleAccessGrant | null;
}

function isGrantActiveAt(grant: SampleAccessGrant, asOf: string): boolean {
  const asOfTime = new Date(asOf).getTime();
  const from = new Date(grant.valid_from).getTime();
  const until = grant.valid_until
    ? new Date(grant.valid_until).getTime()
    : null;
  return asOfTime >= from && (until === null || asOfTime < until);
}

/**
 * Default-deny check: returns the first sample grant that matches subject,
 * scope, action, and validity window at `asOf`. If none match, the result
 * is an explicit DENY with reason code REGIONAL_SCOPE_ACCESS_DENIED_BY_DEFAULT
 * (this console's own sample-only reason code — the real service's
 * canon-fixed reason code for this case is `CROSS_SCOPE_ACCESS_DENIED`, see
 * contracts/reason-codes/pack-08.yml).
 */
export function checkSampleRegionalScopeAccess(
  input: AuthorizationCheckInput,
): AuthorizationCheckResult {
  const candidate = SAMPLE_ACCESS_GRANTS.find(
    (grant) =>
      grant.subject_reference === input.subjectReference &&
      grant.scope_type === input.scopeType &&
      grant.scope_reference === input.scopeReference &&
      grant.action_code === input.actionCode &&
      isGrantActiveAt(grant, input.asOf),
  );

  if (!candidate) {
    return {
      allowed: false,
      reasonCode: "CROSS_SCOPE_ACCESS_DENIED",
      mode: null,
      matchedGrant: null,
    };
  }

  return {
    allowed: true,
    reasonCode: "REGIONAL_SCOPE_ACCESS_GRANTED",
    mode: candidate.mode,
    matchedGrant: candidate,
  };
}
