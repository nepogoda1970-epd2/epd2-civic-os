"use client";

import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import {
  CASE_ACTIONS,
  clientMayCommitCaseTransition,
  preconditionFor,
} from "../domain/caseWorkflow";
import type { CaseDetail, SafeRefusal } from "../domain/types";
import { mayOfferAction } from "../policies/authority";
import { formatGovernedInstant } from "../policies/dateTime";
import { ScopeBanner } from "./ScopeBanner";
import {
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
  RevalidationNotice,
} from "./primitives";
import { useWorkspace } from "./WorkspaceProvider";

/**
 * Case detail.
 *
 * The refusal path here is the security-relevant one. A case that does not
 * exist, a case belonging to another mandate, and a case the operator is
 * conflict-restricted from must all produce the same message, because a
 * distinguishable "not found" turns direct URL entry into a membership oracle
 * over another mandate's caseload.
 *
 * That is stronger than it sounds, and an earlier version of this file failed
 * it. Rendering a *different panel* for the restricted case — one naming the
 * conflict register as the missing dependency — was enough to distinguish it
 * from a case that simply does not exist, which is the oracle in a politer
 * font. So this surface renders exactly one refusal, `CASE_UNAVAILABLE`, for
 * every negative outcome, and the reviewer-facing dependency detail lives on
 * the desk list, which is not resource-specific and therefore discloses nothing.
 *
 * The loading state is part of the same property. A surface that showed one
 * thing while resolving and another afterwards would let an observer time the
 * difference, so nothing is rendered about the case until the outcome is known.
 *
 * Nothing on this surface writes the case body anywhere. It is not in the page
 * title, not in the URL, not in a data attribute and not in a stored value —
 * the identifier appears in the route because a route needs one, and the
 * content stays in the component tree only.
 */

/**
 * The single refusal every negative outcome renders. It names no resource, no
 * mandate and no reason, and it is identical for absent, out-of-scope,
 * restricted and unavailable.
 */
const CASE_UNAVAILABLE: SafeRefusal = Object.freeze({
  kind: "not_found",
  reasonCode: "WS04-CASE-UNAVAILABLE",
  safeMessage: "Dieser Vorgang ist nicht abrufbar.",
  committed: "not_committed",
  nextSafeAction: "Zur Vorgangsliste zurückkehren.",
  nonDisclosing: true,
});
export function CaseDetailSurface({ caseId }: { caseId: string }) {
  const { runtime, bind, session, scope, restrictedIn, ready } = useWorkspace();
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [resolved, setResolved] = useState(false);

  useEffect(() => {
    // The provider resolves the session and the mandate scope asynchronously.
    // Reading before that finishes would bind against the anonymous session and
    // render a scope refusal that no later event clears — the surface would look
    // permanently refused to an operator who is, in fact, in scope.
    if (!ready) return;
    let cancelled = false;
    void (async () => {
      const api = await runtime();
      const bound = bind({ caseId });
      if (!bound.ok) {
        // The scope refusal is discarded deliberately: surfacing which of the
        // negative outcomes occurred is the disclosure this surface prevents.
        if (!cancelled) setResolved(true);
        return;
      }
      const result = await api.cases.read(bound.value);
      if (cancelled) return;
      if (result.ok) setDetail(result.value);
      setResolved(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, caseId, ready]);

  const restricted = restrictedIn(caseId);
  const precondition = preconditionFor(detail?.version ?? null);

  return (
    <>
      <PageHeader title={WS04_CONTENT.desk.detailTitle} />
      <ScopeBanner />

      {!resolved ? (
        <p className="informational" role="status" data-case-resolving>
          {WS04_CONTENT.desk.resolving}
        </p>
      ) : restricted || detail === null ? (
        /*
         * One panel for every negative outcome. Restricted, out of scope,
         * absent and unavailable are indistinguishable here by construction,
         * not by matching wording that a later edit could drift apart.
         */
        <RefusalPanel
          title={WS04_CONTENT.desk.detailUnavailableTitle}
          refusal={CASE_UNAVAILABLE}
        />
      ) : (
        <section className="card" data-case-detail>
          <h2 className="card-title">{detail.subject}</h2>
          <dl className="metadata-list">
            <div>
              <dt>{WS04_CONTENT.desk.columnReference}</dt>
              <dd>{detail.reference}</dd>
            </div>
            <div>
              <dt>{WS04_CONTENT.desk.columnState}</dt>
              <dd data-case-state={detail.state}>
                {WS04_CONTENT.desk.states[detail.state]}
              </dd>
            </div>
            <div>
              <dt>{WS04_CONTENT.desk.columnReceived}</dt>
              <dd>{formatGovernedInstant(detail.receivedAt)}</dd>
            </div>
            <div>
              <dt>{WS04_CONTENT.desk.versionLabel}</dt>
              <dd>{detail.version}</dd>
            </div>
            <div>
              <dt>{WS04_CONTENT.desk.provenanceLabel}</dt>
              <dd>{detail.provenance}</dd>
            </div>
          </dl>
          <p>{detail.summaryText}</p>
        </section>
      )}

      <Notice kind="legal" title="Vertraulichkeit">
        <p>{WS04_CONTENT.desk.confidentialNotice}</p>
      </Notice>

      <section className="consequential-block" aria-labelledby="case-actions">
        <h2 id="case-actions">Mögliche Handlungen</h2>
        <p className="informational">{WS04_CONTENT.desk.transitionBlocked}</p>
        <RevalidationNotice />
        <ul className="record-list">
          {CASE_ACTIONS.map((action) => {
            const offered =
              mayOfferAction({
                role: session.role,
                required: action.required,
                assurance: session.assurance,
                impact: action.impact,
                inScope: scope !== null,
                conflictRestricted: session.conflictRestricted || restricted,
                authorityActive: scope?.authorityActive ?? false,
              }) &&
              precondition.admissible &&
              /* Always false: no client-side commit exists. */
              clientMayCommitCaseTransition();
            return (
              <li key={action.actionId} data-action={action.actionId}>
                <h3>{action.label}</h3>
                <p className="informational">
                  {
                    capabilityRecord(
                      action.capability as Parameters<
                        typeof capabilityRecord
                      >[0],
                    ).missingDependency
                  }
                </p>
                <button
                  type="button"
                  className="button button--secondary"
                  disabled={!offered}
                  aria-disabled={!offered}
                  data-offered={offered ? "true" : "false"}
                >
                  {action.label}
                </button>
              </li>
            );
          })}
        </ul>
      </section>

      <GovernedFallback />
    </>
  );
}
