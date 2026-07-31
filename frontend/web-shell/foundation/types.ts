export const PRESENTATION_STATES = [
  "loading",
  "empty",
  "ready",
  "partial",
  "stale",
  "error",
  "forbidden",
  "authority_missing",
  "scope_unresolved",
  "not_available",
  "planned",
  "prototype",
  "not_legally_activated",
  "not_production_connected",
  "requires_step_up",
  "requires_dual_control",
  "under_review",
  "superseded",
  "withdrawn",
] as const;

export type PresentationState = (typeof PRESENTATION_STATES)[number];
export type ClientChannel = "responsive-web" | "epd2-mobile-app";
export type WorkspaceId =
  | "WS-01"
  | "WS-02"
  | "WS-03"
  | "WS-04"
  | "WS-05"
  | "WS-06"
  | "WS-07"
  | "WS-08"
  | "WS-09"
  | "WS-10";

export type WorkspacePolicy = Readonly<{
  id: WorkspaceId;
  name: string;
  originPlaceholder: string;
  routePrefix: string;
  shell: "public" | "member" | "voting" | "institutional" | "publication";
  navigationSource: string;
  capabilities: readonly string[];
  sensitivity: string;
  analytics:
    | "aggregate-first-party"
    | "workspace-operational"
    | "security-only"
    | "none";
  browserStorage: "preferences-only" | "purpose-specific" | "none";
  sessionSharing: "forbidden";
  activation:
    | "design-baseline"
    | "wave-1-gated"
    | "planned"
    | "candidate-gated";
}>;

export type RouteMetadata = Readonly<{
  id: string;
  workspaceId: WorkspaceId;
  path: string;
  status: PresentationState;
  authority: string | null;
  scope: string | null;
  visibility: "public" | "private";
  backendDependency: string;
  clientChannels: readonly ClientChannel[];
}>;
