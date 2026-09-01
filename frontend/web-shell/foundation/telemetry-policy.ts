import type { WorkspaceId } from "./types";
import { workspaceById } from "./workspaces";

export const TELEMETRY_PROHIBITED_FIELDS = [
  "userId",
  "globalUserId",
  "memberId",
  "ballot",
  "credential",
  "messageContent",
  "documentContent",
  "formContent",
] as const;

export function validateTelemetryEvent(
  workspaceId: WorkspaceId,
  event: Readonly<Record<string, unknown>>,
): boolean {
  if (workspaceById(workspaceId).analytics === "none") return false;
  return TELEMETRY_PROHIBITED_FIELDS.every((field) => !(field in event));
}
