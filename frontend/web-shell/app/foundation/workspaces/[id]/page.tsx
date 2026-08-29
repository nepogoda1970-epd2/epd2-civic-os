import { notFound } from "next/navigation";

import { WorkspaceAcceptancePage } from "../../../../components/front02-acceptance";
import type { WorkspaceId } from "../../../../foundation/types";

const IDS = [
  "WS-01",
  "WS-02",
  "WS-03",
  "WS-04",
  "WS-05",
  "WS-06",
  "WS-07",
  "WS-08",
  "WS-09",
  "WS-10",
] as const;

export function generateStaticParams() {
  return IDS.map((id) => ({ id: id.toLowerCase() }));
}

export default async function WorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const normalized = id.toUpperCase() as WorkspaceId;
  if (!IDS.includes(normalized as (typeof IDS)[number])) notFound();
  return <WorkspaceAcceptancePage workspaceId={normalized} />;
}
