"use client";
import { useMemo } from "react";
import { MemberWorkspace } from "./MemberWorkspace";
import { composeMemberRuntime } from "./runtime";
import type { ActorMode } from "./types";

export function MemberWorkspaceEntry({ path, runtimeProfile, actor }: { path: string; runtimeProfile: "fixture" | "production"; actor: ActorMode }) {
  const runtime = useMemo(() => composeMemberRuntime(runtimeProfile, actor === "applicant" ? "applicant" : "member"), [runtimeProfile, actor]);
  return <MemberWorkspace path={path} runtime={runtime} actor={actor} />;
}
