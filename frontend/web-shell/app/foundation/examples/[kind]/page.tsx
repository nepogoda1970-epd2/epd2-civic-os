import { notFound } from "next/navigation";
import type { ComponentType } from "react";

import {
  AbstimmungenFixture,
  CommunicationFixture,
  DashboardFixture,
  LoginFixture,
  PublicHomeFixture,
} from "../../../../components/migrated-fixtures";

const KINDS = ["public", "cockpit", "communication", "form", "table"] as const;
type Kind = (typeof KINDS)[number];
export function generateStaticParams() {
  return KINDS.map((kind) => ({ kind }));
}
function isKind(value: string): value is Kind {
  return KINDS.includes(value as Kind);
}

const fixtures: Record<Kind, ComponentType> = {
  public: PublicHomeFixture,
  cockpit: DashboardFixture,
  communication: CommunicationFixture,
  form: LoginFixture,
  table: AbstimmungenFixture,
};

export default async function ExamplePage({
  params,
}: {
  params: Promise<{ kind: string }>;
}) {
  const { kind } = await params;
  if (!isKind(kind)) notFound();
  const Fixture = fixtures[kind];
  return <Fixture />;
}
