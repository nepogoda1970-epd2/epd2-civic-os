/**
 * The WS-04 capability register.
 *
 * Every capability the Representative Workspace could exercise is listed with
 * exactly one controlled status, the owning programme unit, the concrete
 * missing dependency, and the behaviour the interface implements instead.
 * Nothing in the interface may treat a capability as executable unless its
 * status here is `SUPPORTED_REAL_PATH`, and the static validator cross-checks
 * this table against `docs/frontend/FRONT-05-CAPABILITY-STATUS-MATRIX.csv`.
 *
 * The statuses are the honest answer at the FRONT-05 entering baseline. The
 * relevant findings, each re-established directly against the repository:
 *
 *  - No accepted executable HTTP runtime ships anywhere in the programme. Every
 *    `contracts/openapi/pack-*.yaml` carries the statement that no production
 *    HTTP server ships in that pack.
 *  - No representative or mandate service source exists in the accepted tree at
 *    all. `representative-desk-service` (PACK-29) and `office-mandate-service`
 *    (PACK-20) exist only inside unaccepted candidate archives.
 *  - The representative-facing functional requirements FIR-REP-001..004 are
 *    recorded in the requirements register with state `captured`, which is the
 *    pre-specification state; none is `accepted`.
 *  - `compliance-service` does define a `RepresentationMandate`, but PACK-09
 *    scopes it to legal power of attorney. It is not an elected political
 *    mandate and must not be used as one. Conflating them would be a
 *    correctness defect, not a shortcut.
 *  - `transparency-service` has no proposal/approval model: publication has the
 *    single state `PUBLISHED` and authorisation is a caller-supplied
 *    `actor_is_authorized` boolean. There is therefore nothing for a WS-04
 *    publication *proposal* to be submitted to.
 *  - CTRL (the governed control plane) is `NOT_STARTED`; no code is on disk.
 *
 * Consequence: every network capability below is `BLOCKED_BY_DEPENDENCY`. The
 * capabilities that are `SUPPORTED_REAL_PATH` are exactly those the workspace
 * performs itself, locally and authoritatively-for-presentation-only — refusal
 * rendering, scope binding, safe-state display, and the local composition of
 * a draft that has never been asserted to exist anywhere else.
 */

import type { CapabilityStatus } from "./types";

export type CapabilityId =
  | "mandate_session_establishment"
  | "mandate_scope_resolution"
  | "authority_revalidation"
  | "step_up_authentication"
  | "case_intake_list"
  | "case_detail_read"
  | "case_assignment"
  | "case_triage_transition"
  | "case_response_record"
  | "case_scoped_search"
  | "position_draft_read"
  | "position_draft_write"
  | "position_internal_submission"
  | "deviation_record_read"
  | "deviation_record_write"
  | "deviation_decision_reference"
  | "declaration_read"
  | "declaration_submission"
  | "publication_proposal_submission"
  | "publication_state_observation"
  | "conflict_restriction_read"
  | "conflict_restriction_change"
  | "registry_read_reference"
  | "eligibility_status_display"
  | "audit_trail_read"
  | "telemetry_emission"
  | "local_refusal_rendering"
  | "local_scope_binding"
  | "governed_fallback";

/**
 * How a missing dependency should be read by a reviewer.
 *
 * `ABSENT` means the thing simply does not exist yet: unremarkable, and it will
 * become a real path when it is built.
 *
 * `SECURITY_SENSITIVE_BOUNDARY` means something worse: a dependency *appears*
 * to exist, and taking it at face value would create a privileged path resting
 * on an authorization that was never actually established. Such a dependency is
 * not a candidate for becoming a real path when someone gets around to wiring
 * it up — it is a defect that must be corrected on the server side first.
 *
 * `PROHIBITED` means the capability is forbidden to this workspace outright, so
 * no dependency could ever unblock it.
 */
export const DEPENDENCY_CLASSES = Object.freeze([
  "ABSENT",
  "SECURITY_SENSITIVE_BOUNDARY",
  "PROHIBITED",
] as const);

export type DependencyClass = (typeof DEPENDENCY_CLASSES)[number];

export type CapabilityRecord = {
  readonly id: CapabilityId;
  readonly status: CapabilityStatus;
  /** The programme unit that owns the missing or present dependency. */
  readonly owner: string;
  /** The exact dependency that is missing. Empty only when nothing is missing. */
  readonly missingDependency: string;
  readonly dependencyClass: DependencyClass;
  readonly reason: string;
  readonly frontendBehaviour: string;
  /**
   * Set only on a `SECURITY_SENSITIVE_BOUNDARY`. States the defect in the
   * dependency itself, so it reaches the accepting authority as a finding
   * rather than as a line in a gap list.
   */
  readonly securityFinding?: string;
};

const BLOCKED = "BLOCKED_BY_DEPENDENCY" as const;

export const WS04_CAPABILITIES: readonly CapabilityRecord[] = Object.freeze([
  {
    id: "mandate_session_establishment",
    status: BLOCKED,
    owner: "API-02 / identity boundary",
    missingDependency:
      "an accepted executable route issuing a mandate-scoped representative session",
    dependencyClass: "ABSENT",
    reason:
      "API-02 C13 accepts identity-side issuance operations, but none of them issues or validates a session bound to an elected mandate. No accepted route exists that a WS-04 browser could call to become authenticated as a mandate holder.",
    frontendBehaviour:
      "The workspace starts in the anonymous state, states that mandate sessions cannot be established against any accepted runtime, and offers no credential entry that would imply otherwise.",
  },
  {
    id: "mandate_scope_resolution",
    status: BLOCKED,
    owner: "PACK-20 office-mandate-service (unaccepted)",
    missingDependency:
      "an accepted mandate register exposing the mandate, its level, and its active authority window",
    dependencyClass: "ABSENT",
    reason:
      "The only mandate register source in the programme is office-mandate-service, which exists solely inside the unaccepted PACK-20 candidate archive. compliance-service.RepresentationMandate is legal power of attorney under PACK-09 and is not an elected mandate.",
    frontendBehaviour:
      "Scope is never resolved from the network. Every protected surface refuses with scope_mismatch or unavailable and names the missing register.",
  },
  {
    id: "authority_revalidation",
    status: BLOCKED,
    owner: "PACK-20 office-mandate-service (unaccepted)",
    missingDependency:
      "an accepted server-side authority check evaluated at commit time",
    dependencyClass: "ABSENT",
    reason:
      "Commit-time revalidation is a server obligation. With no accepted mandate service there is nothing to revalidate against, and the client is forbidden from deciding authority itself.",
    frontendBehaviour:
      "No action that would require commit-time revalidation is offered as executable. The requirement is displayed, not simulated.",
  },
  {
    id: "step_up_authentication",
    status: BLOCKED,
    owner: "API-02 / identity boundary",
    missingDependency:
      "an accepted executable step-up ceremony returning a raised assurance level",
    dependencyClass: "ABSENT",
    reason:
      "Assurance levels are declared in the accepted policy records, but no accepted route performs a step-up ceremony.",
    frontendBehaviour:
      "Surfaces that require step-up render the step_up_required state with the reason, and the trigger is inert by construction rather than disabled by styling.",
  },
  {
    id: "case_intake_list",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route listing mandate-scoped citizen cases",
    dependencyClass: "ABSENT",
    reason:
      "The desk service exists only inside the unaccepted PACK-29 candidate archive, and FIR-REP-001 is recorded as captured, not accepted.",
    frontendBehaviour:
      "The desk renders the unavailable state with the named dependency. No placeholder case list is shown, because a fabricated list is indistinguishable from a real one to the user.",
  },
  {
    id: "case_detail_read",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route returning a single case within mandate scope",
    dependencyClass: "ABSENT",
    reason:
      "Same dependency as the intake list. Case content is confidential and is the data class this workspace is most constrained around.",
    frontendBehaviour:
      "Detail routes refuse non-disclosingly: the refusal is identical whether the case does not exist or lies outside scope.",
  },
  {
    id: "case_assignment",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency: "an accepted executable case assignment operation",
    dependencyClass: "ABSENT",
    reason:
      "Assignment mutates server-held state; no accepted route accepts such a mutation.",
    frontendBehaviour:
      "The action is described in the action register with its authority requirement and reported as blocked. It is never offered as executable.",
  },
  {
    id: "case_triage_transition",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable state-transition operation with optimistic-concurrency semantics",
    dependencyClass: "ABSENT",
    reason:
      "Case state transitions are server-authoritative and require a version precondition. Neither the operation nor the version token has an accepted definition.",
    frontendBehaviour:
      "Transitions are not attempted. The state machine models the safe outcomes, including the uncertain outcome, and is exercised only under the governed test profile.",
  },
  {
    id: "case_response_record",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route recording an outbound response against a case",
    dependencyClass: "ABSENT",
    reason: "No accepted route accepts case correspondence.",
    frontendBehaviour:
      "Composition surfaces are not presented as a send path. Nothing composed is described as delivered.",
  },
  {
    id: "case_scoped_search",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable search operation that is server-side scope-bound",
    dependencyClass: "ABSENT",
    reason:
      "Search must be constrained on the server. A client-side filter over a client-held corpus is not a scoped search, and a cross-mandate search is prohibited outright.",
    frontendBehaviour:
      "Search is unavailable. The interface never offers an unscoped search field, so there is no surface on which a cross-mandate query could be typed.",
  },
  {
    id: "position_draft_read",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route returning stored position drafts",
    dependencyClass: "ABSENT",
    reason: "No accepted route stores or returns position drafts.",
    frontendBehaviour:
      "The position surface renders unavailable rather than an empty list, because an empty list asserts that nothing exists.",
  },
  {
    id: "position_draft_write",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency: "an accepted executable route persisting a draft",
    dependencyClass: "ABSENT",
    reason: "No accepted route persists a draft.",
    frontendBehaviour:
      "A draft composed in this workspace exists only in volatile memory for the life of the surface. It is labelled as unsaved, and no browser storage receives it.",
  },
  {
    id: "position_internal_submission",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route accepting an internal submission",
    dependencyClass: "ABSENT",
    reason: "No accepted route accepts a submission.",
    frontendBehaviour:
      "Submission is reported blocked with the named dependency. The workspace never reports a draft as submitted.",
  },
  {
    id: "deviation_record_read",
    status: BLOCKED,
    owner: "PACK-29 / transparency-service",
    missingDependency:
      "an accepted executable route returning deviation records with provenance",
    dependencyClass: "ABSENT",
    reason:
      "transparency-service publishes finished items; it holds no deviation record model, and the desk service that would hold one is unaccepted.",
    frontendBehaviour: "Unavailable state with the named dependency.",
  },
  {
    id: "deviation_record_write",
    status: BLOCKED,
    owner: "PACK-29 representative-desk-service (unaccepted)",
    missingDependency:
      "an accepted executable route recording a deviation against a governed decision",
    dependencyClass: "ABSENT",
    reason: "No accepted route accepts a deviation record.",
    frontendBehaviour:
      "The composition surface exists and enforces the record's shape locally, including the requirement that a deviation references a decision and cannot alter it. Nothing is transmitted.",
  },
  {
    id: "deviation_decision_reference",
    status: BLOCKED,
    owner: "PACK-16 / decision runtime",
    missingDependency:
      "an accepted executable route resolving a governed decision identifier to its published record",
    dependencyClass: "ABSENT",
    reason:
      "A deviation must reference a real decision. No accepted route resolves decision identifiers.",
    frontendBehaviour:
      "References are accepted as opaque text and explicitly marked unverified. The workspace does not claim a reference is valid.",
  },
  {
    id: "declaration_read",
    status: BLOCKED,
    owner: "PACK-09 compliance-service",
    missingDependency:
      "an accepted executable route returning a representative's own declarations",
    dependencyClass: "ABSENT",
    reason:
      "compliance-service models declarations at specification level only; no accepted executable route exists, and its RepresentationMandate is legal power of attorney rather than an elected mandate.",
    frontendBehaviour: "Unavailable state with the named dependency.",
  },
  {
    id: "declaration_submission",
    status: BLOCKED,
    owner: "PACK-09 compliance-service",
    missingDependency:
      "an accepted executable route accepting a declaration submission",
    dependencyClass: "ABSENT",
    reason: "No accepted route accepts a declaration.",
    frontendBehaviour:
      "The form validates locally and reports the submission blocked. It never reports acceptance, and it never asserts a compliance obligation has been met.",
  },
  {
    id: "publication_proposal_submission",
    status: BLOCKED,
    owner: "PACK-13 transparency-service",
    missingDependency:
      "a server-authoritative proposal and authorization contract: a proposal state distinct from PUBLISHED, and an authorization decided by the server rather than asserted by the caller",
    dependencyClass: "SECURITY_SENSITIVE_BOUNDARY",
    reason:
      "transparency-service has a single publication state, PUBLISHED, and it authorises by a caller-supplied actor_is_authorized boolean. There is no proposal state to submit into, and the authorization gate is not an authorization gate.",
    securityFinding:
      "A caller-supplied actor_is_authorized boolean is a self-asserted authorization: the caller declares its own permission and the service accepts the declaration. FRONT-05 must not treat it as evidence that any authorization occurred, and must not build a privileged path on it — doing so would let a proposal reach publication carrying nothing but the proposer's own claim of being allowed to publish. This is a defect in the dependency, not a gap in it: the capability stays blocked until a server-authoritative authorization contract exists, and would remain blocked even if a proposal route were added while the boolean stayed.",
    frontendBehaviour:
      "The workspace offers proposal composition only, states in the interface that a proposal is not an approval, and reports submission blocked. It never sets, sends or relies on an authorization flag of its own.",
  },
  {
    id: "publication_state_observation",
    status: BLOCKED,
    owner: "PACK-13 transparency-service",
    missingDependency:
      "a route returning a publication state whose approval was decided by an authority other than the proposer",
    dependencyClass: "SECURITY_SENSITIVE_BOUNDARY",
    reason:
      "No accepted executable transparency route ships, and the model behind it records no deciding authority — publication is authorised by the caller's own actor_is_authorized boolean.",
    securityFinding:
      "An observed publication state carries no independent evidence of who approved it, because the service records no deciding authority. A state read back from such a service cannot distinguish an approval by the publication authority from one the proposer asserted about itself, so this workspace treats an approved state with no recorded decider as not public — see mayPresentAsPublic in domain/publication.ts.",
    frontendBehaviour:
      "Publication state is shown as unknown rather than assumed, and an approved state is presented as public only when a deciding authority and a public rendition reference are both present.",
  },
  {
    id: "conflict_restriction_read",
    status: BLOCKED,
    owner: "PACK-09 compliance-service",
    missingDependency:
      "an accepted executable route returning active conflict restrictions for a mandate",
    dependencyClass: "ABSENT",
    reason: "No accepted route returns restrictions.",
    frontendBehaviour:
      "Restrictions cannot be read, so the workspace fails closed: it neither asserts that a restriction is absent nor treats an unknown restriction as cleared.",
  },
  {
    id: "conflict_restriction_change",
    status: "UNSUPPORTED",
    owner: "Conflict officer role, outside WS-04",
    missingDependency:
      "not applicable — the capability is prohibited for this workspace, not merely blocked",
    dependencyClass: "PROHIBITED",
    reason:
      "A subject may never clear a restriction over themselves. This is a prohibition, so it would remain unsupported even if an accepted route existed.",
    frontendBehaviour:
      "No surface, no action descriptor, and no port exists. The prohibition is enforced by absence and asserted by a total function returning false.",
  },
  {
    id: "registry_read_reference",
    status: BLOCKED,
    owner: "PACK-20 / PACK-09 registers (unaccepted or specification-level)",
    missingDependency:
      "an accepted executable read route over a protected register",
    dependencyClass: "ABSENT",
    reason:
      "WS-04 holds no registry custody and may only reference registry data by reading it. No accepted read route exists.",
    frontendBehaviour:
      "Registry-derived facts are shown as unavailable. No registry mutation surface exists at all.",
  },
  {
    id: "eligibility_status_display",
    status: BLOCKED,
    owner: "Eligibility authority, outside WS-04",
    missingDependency:
      "an accepted executable route returning a decided eligibility status",
    dependencyClass: "ABSENT",
    reason:
      "WS-04 may display an eligibility decision made elsewhere but may never make one. No accepted route supplies a decision to display.",
    frontendBehaviour:
      "Eligibility is displayed as undetermined-elsewhere, with the explicit statement that this workspace does not decide it.",
  },
  {
    id: "audit_trail_read",
    status: BLOCKED,
    owner: "CTRL / governed control plane (NOT_STARTED)",
    missingDependency: "any control-plane implementation whatsoever",
    dependencyClass: "ABSENT",
    reason:
      "CTRL is recorded NOT_STARTED and no code is on disk. There is no audit surface to read.",
    frontendBehaviour:
      "The workspace states that its own actions are not currently audited by an accepted control plane, which is a limitation the operator must know.",
  },
  {
    id: "telemetry_emission",
    status: BLOCKED,
    owner: "Platform telemetry (not connected)",
    missingDependency: "a connected accepted telemetry platform",
    dependencyClass: "ABSENT",
    reason:
      "No telemetry platform is connected. The allowlist and the content prohibitions are implemented and tested regardless, so that the constraint is already binding when a platform arrives.",
    frontendBehaviour:
      "No telemetry leaves the browser. The validator asserts the allowlist is enforced and that case content can never enter an event.",
  },
  {
    id: "local_refusal_rendering",
    status: "SUPPORTED_REAL_PATH",
    owner: "FRONT-05 / WS-04",
    missingDependency: "",
    dependencyClass: "ABSENT",
    reason:
      "Rendering a safe refusal is performed entirely by this workspace and depends on nothing external.",
    frontendBehaviour:
      "Every refusal kind renders a safe message, a committed/not-committed/unknown statement, and one safe next action, with non-disclosure preserved where required.",
  },
  {
    id: "local_scope_binding",
    status: "SUPPORTED_REAL_PATH",
    owner: "FRONT-05 / WS-04",
    missingDependency: "",
    dependencyClass: "ABSENT",
    reason:
      "Binding every route and action to exactly one mandate scope, and rejecting any request that carries none or more than one, is local structure. It is presentation-side only and never a substitute for the server decision.",
    frontendBehaviour:
      "There is no representation of an unbounded scope in the type system, so a cross-mandate request has no expressible form.",
  },
  {
    id: "governed_fallback",
    status: "SUPPORTED_REAL_PATH",
    owner: "FRONT-05 / WS-04",
    missingDependency: "",
    dependencyClass: "ABSENT",
    reason:
      "Directing the user to the governed non-digital path when a digital path is blocked is local and always available.",
    frontendBehaviour:
      "Each blocked surface names the offline route that remains valid, so no citizen matter is dropped because the software is unfinished.",
  },
]);

const BY_ID: ReadonlyMap<CapabilityId, CapabilityRecord> = new Map(
  WS04_CAPABILITIES.map((record) => [record.id, record]),
);

export function capabilityRecord(id: CapabilityId): CapabilityRecord {
  const record = BY_ID.get(id);
  if (record === undefined) {
    throw new Error(`WS-04 capability register has no entry for '${id}'`);
  }
  return record;
}

export function capabilityStatus(id: CapabilityId): CapabilityStatus {
  return capabilityRecord(id).status;
}

/**
 * The single question the interface is allowed to ask. Note that it is false
 * for every network capability at this baseline, by construction.
 */
export function capabilityExecutable(id: CapabilityId): boolean {
  return capabilityRecord(id).status === "SUPPORTED_REAL_PATH";
}

export function blockedCapabilities(): readonly CapabilityRecord[] {
  return WS04_CAPABILITIES.filter((r) => r.status === BLOCKED);
}

/**
 * Every capability that reaches the network. The validator asserts that this
 * set and the executable set are disjoint: no network capability may ever be
 * reported executable while no accepted runtime exists.
 */
export const NETWORK_CAPABILITIES: readonly CapabilityId[] = Object.freeze(
  WS04_CAPABILITIES.filter(
    (r) =>
      r.id !== "local_refusal_rendering" &&
      r.id !== "local_scope_binding" &&
      r.id !== "governed_fallback" &&
      r.id !== "conflict_restriction_change",
  ).map((r) => r.id),
);

export function anyNetworkCapabilityExecutable(): boolean {
  return NETWORK_CAPABILITIES.some((id) => capabilityExecutable(id));
}

/**
 * Dependencies that are not merely missing but defective.
 *
 * These are the ones a reviewer must not read as "will work once someone wires
 * it up". Each names a boundary where the dependency, as it currently stands,
 * would hand this workspace a privileged path resting on an authorization that
 * was never established.
 */
export function securitySensitiveDependencies(): readonly CapabilityRecord[] {
  return WS04_CAPABILITIES.filter(
    (r) => r.dependencyClass === "SECURITY_SENSITIVE_BOUNDARY",
  );
}

/**
 * The invariant that makes the classification binding rather than descriptive.
 *
 * A capability whose dependency is a security-sensitive boundary may never be
 * `SUPPORTED_REAL_PATH`. Unblocking it requires the *dependency* to be
 * corrected — a server-authoritative authorization contract — and not merely a
 * route to appear. Adding the route while the caller-asserted authorization
 * stayed would leave this capability blocked, and this function is what says so
 * to any future change.
 *
 * It also refuses `SUPPORTED_WITH_DECLARED_LIMITATION`. A declared limitation is
 * the right vocabulary for a capability that works within stated bounds; it is
 * the wrong vocabulary for one whose authorization is self-asserted, because
 * there is no bound inside which that is safe.
 */
export function securitySensitiveBoundariesRespected(): boolean {
  return securitySensitiveDependencies().every(
    (r) => r.status === "BLOCKED_BY_DEPENDENCY" || r.status === "UNSUPPORTED",
  );
}

/**
 * Every security-sensitive boundary must carry a stated finding. A boundary
 * flagged without a finding would reach the accepting authority as a label
 * rather than as something they can act on.
 */
export function securityFindingsComplete(): boolean {
  return securitySensitiveDependencies().every(
    (r) => (r.securityFinding ?? "").length > 100,
  );
}

/**
 * Asserted at module load. A change that marks one of these executable takes the
 * workspace down rather than shipping a privileged path built on a caller's own
 * claim about its permissions.
 */
if (!securitySensitiveBoundariesRespected()) {
  throw new Error(
    "WS-04 capability register: a capability with a security-sensitive dependency is not blocked.",
  );
}
