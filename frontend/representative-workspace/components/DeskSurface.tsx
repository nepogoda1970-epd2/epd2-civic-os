"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import { listProjection } from "../domain/caseWorkflow";
import type { CaseSummary, SafeRefusal } from "../domain/types";
import { formatGovernedInstant } from "../policies/dateTime";
import { WS04_ROUTE_PREFIX } from "../policies/workspace";
import { ScopeBanner } from "./ScopeBanner";
import {
  DependencyPanel,
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
} from "./primitives";
import { useWorkspace } from "./WorkspaceProvider";

/**
 * The case queue.
 *
 * Two things are deliberately absent. There is no search field, because search
 * must be server-side scope-bound and is blocked — offering one would create a
 * surface on which a cross-mandate query could be typed. And there is no empty
 * state that reads as "no cases": when the list cannot be read, the surface
 * says the list is not obtainable, which is a different claim.
 */
export function DeskSurface() {
  const { runtime, bind, restrictedIn, ready } = useWorkspace();
  const [cases, setCases] = useState<readonly CaseSummary[] | null>(null);
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);

  useEffect(() => {
    // The provider resolves the session and the mandate scope asynchronously.
    // Reading before that finishes would bind against the anonymous session and
    // render a scope refusal that no later event clears — the surface would look
    // permanently refused to an operator who is, in fact, in scope.
    if (!ready) return;
    let cancelled = false;
    void (async () => {
      const api = await runtime();
      const bound = bind({ state: null, page: 1 });
      if (!bound.ok) {
        if (!cancelled) setRefusal(bound.error);
        return;
      }
      const result = await api.cases.list(bound.value);
      if (cancelled) return;
      if (result.ok) setCases(listProjection(result.value));
      else setRefusal(result.error);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, ready]);

  const record = capabilityRecord("case_intake_list");

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.desk.title}
        lead={WS04_CONTENT.desk.lead}
      />
      <ScopeBanner />

      <Notice kind="legal" title="Vertraulichkeit">
        <p>{WS04_CONTENT.desk.confidentialNotice}</p>
      </Notice>

      {/*
        No search input is rendered. The scope notice explains the boundary so
        the absence reads as a rule rather than an oversight.
      */}
      <p className="informational" data-search-policy>
        {WS04_CONTENT.search.scopeNotice} {WS04_CONTENT.search.unavailable}
      </p>

      {refusal ? (
        <RefusalPanel
          title={WS04_CONTENT.desk.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {cases === null ? (
        <DependencyPanel
          title={WS04_CONTENT.desk.unavailableTitle}
          dependency={record.missingDependency}
          behaviour={WS04_CONTENT.desk.empty}
        />
      ) : (
        <div className="queue-scroll">
          <table className="queue-table" data-case-queue>
            <caption>{WS04_CONTENT.desk.lead}</caption>
            <thead>
              <tr>
                <th scope="col">{WS04_CONTENT.desk.columnReference}</th>
                <th scope="col">{WS04_CONTENT.desk.columnSubject}</th>
                <th scope="col">{WS04_CONTENT.desk.columnState}</th>
                <th scope="col">{WS04_CONTENT.desk.columnReceived}</th>
                <th scope="col">{WS04_CONTENT.desk.columnAssignee}</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => {
                const restricted =
                  item.conflictRestricted || restrictedIn(item.caseId);
                return (
                  <tr key={item.caseId} data-case-row={item.caseId}>
                    <td>{item.reference}</td>
                    <td>
                      {restricted ? (
                        WS04_CONTENT.desk.restricted
                      ) : (
                        <Link
                          href={`${WS04_ROUTE_PREFIX}/desk/${encodeURIComponent(item.caseId)}`}
                        >
                          {item.subject}
                        </Link>
                      )}
                    </td>
                    <td data-case-state={item.state}>
                      {WS04_CONTENT.desk.states[item.state]}
                    </td>
                    <td>{formatGovernedInstant(item.receivedAt)}</td>
                    <td>
                      {item.assigneeLabel ?? WS04_CONTENT.desk.unassigned}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <Notice kind="information" title={WS04_CONTENT.degraded.title}>
        <p>{WS04_CONTENT.degraded.intakePaused}</p>
      </Notice>

      <GovernedFallback />
    </>
  );
}
