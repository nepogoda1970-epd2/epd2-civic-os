import type { RouteMetadata } from "./types";

// Representative FRONT-00 routes only. The full authoritative registry remains
// EPD2_Frontend_Route_Map_0.8.2.csv; no business route is activated here.
export const ROUTES: readonly RouteMetadata[] = [
  {
    id: "FRONT00-PUBLIC",
    workspaceId: "WS-01",
    path: "/foundation/examples/public",
    status: "prototype",
    authority: null,
    scope: null,
    visibility: "public",
    backendDependency: "FRONT-01 / approved publication rendition",
    clientChannels: ["responsive-web"],
  },
  {
    id: "FRONT00-COCKPIT",
    workspaceId: "WS-02",
    path: "/foundation/examples/cockpit",
    status: "not_production_connected",
    authority: "Member",
    scope: "organization scope",
    visibility: "private",
    backendDependency: "future member application block",
    clientChannels: ["responsive-web", "epd2-mobile-app"],
  },
  {
    id: "FRONT00-COMMUNICATION",
    workspaceId: "WS-02",
    path: "/foundation/examples/communication",
    status: "planned",
    authority: "Member",
    scope: "conversation scope",
    visibility: "private",
    backendDependency: "communications domain activation",
    clientChannels: ["responsive-web", "epd2-mobile-app"],
  },
  {
    id: "FRONT00-FORM",
    workspaceId: "WS-02",
    path: "/foundation/examples/form",
    status: "prototype",
    authority: "Member",
    scope: "own draft",
    visibility: "private",
    backendDependency: "future workflow endpoint",
    clientChannels: ["responsive-web", "epd2-mobile-app"],
  },
  {
    id: "FRONT00-TABLE",
    workspaceId: "WS-02",
    path: "/foundation/examples/table",
    status: "prototype",
    authority: "Member",
    scope: "organization scope",
    visibility: "private",
    backendDependency: "future list endpoint",
    clientChannels: ["responsive-web", "epd2-mobile-app"],
  },
] as const;

export const routeByPath = (path: string): RouteMetadata | undefined =>
  ROUTES.find((route) => route.path === path);
