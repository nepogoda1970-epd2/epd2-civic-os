export type CapabilityStatus =
  "AVAILABLE" | "LIMITED" | "PLANNED" | "BLOCKED" | "UNAVAILABLE";
export type ActorMode = "applicant" | "member" | "anonymous";
export type Locale = "de" | "en";
export type Scope = {
  ref: string;
  label: string;
  level: "Bund" | "Land" | "Kreis" | "Ort";
  authorized: boolean;
};
export type Principal = {
  actor: ActorMode;
  displayName: string;
  scopeRef?: string;
  assurance: "standard" | "step-up-required" | "expired" | "revoked";
};
export type PortFailure = {
  kind: "forbidden" | "unavailable" | "stale" | "conflict" | "unknown";
  safeMessage: string;
};
export type Result<T> =
  { ok: true; value: T } | { ok: false; error: PortFailure };
export type ApplicantCase = {
  reference: string;
  submittedAt: string;
  status: string;
  unit: string;
  stage: string;
  deadline: string;
  documents: string[];
  timeline: { at: string; label: string }[];
  notice: string;
  reasonCode?: string;
};
export type MemberSummary = {
  status: string;
  organization: string;
  tasks: string[];
  deadlines: string[];
  messages: string[];
  capabilities: {
    initiatives: CapabilityStatus;
    deliberation: CapabilityStatus;
    delegation: CapabilityStatus;
  };
  voting: CapabilityStatus;
};
export type MembershipRecord = {
  status: string;
  affiliation: string;
  version: string;
  provenance: string;
  history: string[];
  correctionState: CapabilityStatus;
  decisionState: string;
  documentState: string;
};
export type Initiative = {
  ref: string;
  title: string;
  state: string;
  scopeRef: string;
};
export type InitiativeDraft = {
  title: string;
  summary: string;
  clientRequestRef: string;
  expectedVersion: string;
};
export type InitiativeReceipt = {
  receiptRef: string;
  committedAt: string;
  state: "committed";
};
export type DeliberationItem = {
  title: string;
  provenance: string;
  version: string;
};
export type DelegationStatus = { activation: CapabilityStatus; reason: string };
export type VotingContinuation = {
  continuation: string;
  purpose: "enter-voting-client";
  expiresAt: string;
  targetOrigin: "https://vote.epd.example";
};
export interface PrincipalPort {
  resolve(): Promise<Result<Principal>>;
}
export interface ApplicantCasePort {
  readOwnCase(): Promise<Result<ApplicantCase>>;
}
export interface MemberCorePort {
  read(scopeRef: string, signal?: AbortSignal): Promise<Result<MemberSummary>>;
}
export interface MembershipPort {
  read(
    scopeRef: string,
    signal?: AbortSignal,
  ): Promise<Result<MembershipRecord>>;
}
export interface InitiativesPort {
  list(scopeRef: string, signal?: AbortSignal): Promise<Result<Initiative[]>>;
  commit(
    scopeRef: string,
    draft: InitiativeDraft,
  ): Promise<Result<InitiativeReceipt>>;
}
export interface DeliberationPort {
  list(
    scopeRef: string,
    signal?: AbortSignal,
  ): Promise<Result<DeliberationItem[]>>;
}
export interface DelegationPort {
  status(
    scopeRef: string,
    signal?: AbortSignal,
  ): Promise<Result<DelegationStatus>>;
}
export interface OrganizationScopePort {
  listAuthorized(): Promise<Result<Scope[]>>;
  reauthorize(
    targetRef: string,
    signal?: AbortSignal,
  ): Promise<Result<{ scopeRef: string; contextVersion: string }>>;
}
export interface SessionAssurancePort {
  read(): Promise<
    Result<{
      assurance: string;
      sessions: string[];
      passkeys: string[];
      recovery: CapabilityStatus;
    }>
  >;
}
export interface VotingHandoffPort {
  create(): Promise<Result<VotingContinuation>>;
}
export interface SupportHelpPort {
  read(): Promise<Result<{ status: CapabilityStatus; offline: string }>>;
}
export type MemberRuntime = Readonly<{
  profile: "fixture" | "production";
  principal: PrincipalPort;
  applicantCase: ApplicantCasePort;
  memberCore: MemberCorePort;
  membership: MembershipPort;
  initiatives: InitiativesPort;
  deliberation: DeliberationPort;
  delegation: DelegationPort;
  organizationScope: OrganizationScopePort;
  sessionAssurance: SessionAssurancePort;
  votingHandoff: VotingHandoffPort;
  supportHelp: SupportHelpPort;
}>;
