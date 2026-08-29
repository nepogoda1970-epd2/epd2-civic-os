import { notFound } from "next/navigation";

import {
  SystemStateAcceptancePage,
  type Front02SystemState,
} from "../../../../components/front02-acceptance";

const KINDS = ["denied", "error", "recovery", "translation-fallback"] as const;

export function generateStaticParams() {
  return KINDS.map((kind) => ({ kind }));
}

export default async function StatePage({
  params,
}: {
  params: Promise<{ kind: string }>;
}) {
  const { kind } = await params;
  if (!KINDS.includes(kind as (typeof KINDS)[number])) notFound();
  return <SystemStateAcceptancePage state={kind as Front02SystemState} />;
}
