import type { WorkspaceId } from "./types";
import { workspaceById } from "./workspaces";

export type StorageKind =
  | "cookie"
  | "localStorage"
  | "sessionStorage"
  | "indexedDB"
  | "cacheStorage"
  | "serviceWorker";
export type StoragePurpose =
  | "preference"
  | "sensitive-data"
  | "ballot"
  | "identity"
  | "technical-cache";

export function storageAllowed(
  workspaceId: WorkspaceId,
  kind: StorageKind,
  purpose: StoragePurpose,
): boolean {
  const workspace = workspaceById(workspaceId);
  if (workspace.id === "WS-03") return false;
  if (
    purpose === "sensitive-data" ||
    purpose === "ballot" ||
    purpose === "identity"
  )
    return false;
  if (workspace.browserStorage === "none" || kind === "indexedDB") return false;
  return (
    purpose === "preference" && workspace.browserStorage === "preferences-only"
  );
}
