import { cookies } from "next/headers";
import { MemberWorkspaceEntry } from "../../../member/MemberWorkspaceEntry";
import type { ActorMode } from "../../../member/types";

export const dynamic = "force-dynamic";

export default async function MemberRoute({ params }: { params: Promise<{ memberPath?: string[] }> }) {
  const { memberPath = [] } = await params;
  const fixtureEnabled = process.env.NEXT_PUBLIC_FRONT03_FIXTURE === "1" && process.env.EPD2_FRONT03_GOVERNED_TEST_CONTEXT === "1";
  const cookieStore = await cookies();
  const fixtureActor = cookieStore.get("front03_fixture_principal")?.value;
  const actor: ActorMode = fixtureEnabled ? (fixtureActor === "applicant" || process.env.NEXT_PUBLIC_FRONT03_ACTOR === "applicant" ? "applicant" : "member") : "anonymous";
  return <MemberWorkspaceEntry path={`/member/${memberPath.join("/")}`.replace(/\/$/, "")} runtimeProfile={fixtureEnabled ? "fixture" : "production"} actor={actor} />;
}
