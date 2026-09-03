"use client";

import Link from "next/link";

import { WS04_CONTENT } from "../content/de";
import {
  WS04_CAPABILITIES,
  capabilityRecord,
  type CapabilityId,
} from "../domain/capabilities";
import { WS04_ROUTE_PREFIX } from "../policies/workspace";
import { ScopeBanner } from "./ScopeBanner";
import {
  CapabilityBadge,
  DependencyPanel,
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
} from "./primitives";
import { useWorkspace } from "./WorkspaceProvider";

/**
 * The representative home.
 *
 * The design decision that matters here is what the home does when it cannot
 * count anything. The tempting answer is a tidy dashboard of zeros. That is a
 * lie: "0 offene Erklärungen" asserts a fact this workspace cannot establish,
 * and a representative who trusts it may miss a legal deadline. So each block
 * either shows a figure it can substantiate or says explicitly that the figure
 * is not obtainable and why.
 */

const HOME_BLOCKS: readonly {
  readonly id: CapabilityId;
  readonly label: string;
  readonly href: string;
}[] = [
  {
    id: "case_intake_list",
    label: WS04_CONTENT.home.queueSummary,
    href: `${WS04_ROUTE_PREFIX}/desk`,
  },
  {
    id: "declaration_read",
    label: WS04_CONTENT.home.pendingDeclarations,
    href: `${WS04_ROUTE_PREFIX}/declarations`,
  },
  {
    id: "position_draft_read",
    label: WS04_CONTENT.home.pendingWork,
    href: `${WS04_ROUTE_PREFIX}/positions`,
  },
  {
    id: "publication_state_observation",
    label: WS04_CONTENT.home.proposals,
    href: `${WS04_ROUTE_PREFIX}/publication`,
  },
  {
    id: "conflict_restriction_read",
    label: WS04_CONTENT.home.alerts,
    href: `${WS04_ROUTE_PREFIX}/conflicts`,
  },
];

function capabilitySummaryText(): string {
  const total = WS04_CAPABILITIES.length;
  const blocked = WS04_CAPABILITIES.filter(
    (c) => c.status === "BLOCKED_BY_DEPENDENCY",
  ).length;
  const executable = WS04_CAPABILITIES.filter(
    (c) => c.status === "SUPPORTED_REAL_PATH",
  ).length;
  return WS04_CONTENT.home.capabilitySummary
    .replace("{total}", String(total))
    .replace("{blocked}", String(blocked))
    .replace("{executable}", String(executable));
}

export function HomeSurface() {
  const { refusal, ready } = useWorkspace();

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.home.title}
        lead={WS04_CONTENT.home.lead}
      />
      <ScopeBanner />

      <Notice kind="warning" title="Zustand dieses Arbeitsbereichs">
        <p>{WS04_CONTENT.noRuntimeNotice}</p>
        <p className="informational" data-capability-summary>
          {capabilitySummaryText()}
        </p>
      </Notice>

      {refusal ? (
        <RefusalPanel title={WS04_CONTENT.auth.signedOut} refusal={refusal} />
      ) : null}

      <section aria-labelledby="home-blocks">
        <h2 id="home-blocks">{WS04_CONTENT.home.actionable}</h2>
        <p className="informational">{WS04_CONTENT.home.nothingActionable}</p>
        <ul className="record-list" data-home-blocks>
          {HOME_BLOCKS.map((block) => {
            const record = capabilityRecord(block.id);
            return (
              <li key={block.id} data-capability={block.id}>
                <h3>
                  <Link href={block.href}>{block.label}</Link>
                </h3>
                <p>
                  <CapabilityBadge status={record.status} />
                </p>
                <p className="informational">{record.frontendBehaviour}</p>
              </li>
            );
          })}
        </ul>
      </section>

      <DependencyPanel
        title="Warum keine Zahlen angezeigt werden"
        dependency={capabilityRecord("case_intake_list").missingDependency}
        behaviour="Eine Null wäre eine Behauptung. Solange die Dienste nicht abrufbar sind, wird keine Zahl angezeigt."
      />

      <Notice kind="legal" title={WS04_CONTENT.votingBoundary.title}>
        <p>{WS04_CONTENT.votingBoundary.body}</p>
      </Notice>

      <GovernedFallback />

      <p className="provenance" data-ready={ready ? "true" : "false"}>
        {WS04_CONTENT.states.notAudited}
      </p>
    </>
  );
}
