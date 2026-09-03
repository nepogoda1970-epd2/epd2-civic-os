"use client";

import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import {
  PROPOSAL_DISCLAIMER,
  PUBLICATION_ACTIONS,
  PUBLICATION_MODEL_GAP,
  callerAssertedAuthorizationSufficient,
  mayPresentAsPublic,
  publicationLabel,
} from "../domain/publication";
import type { PublicationProposal, SafeRefusal } from "../domain/types";
import { ws04MayApprovePublication } from "../policies/boundaries";
import { ScopeBanner } from "./ScopeBanner";
import {
  DependencyPanel,
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
  RevalidationNotice,
} from "./primitives";
import { useWorkspace } from "./WorkspaceProvider";

/**
 * Publication proposals.
 *
 * There is no approve control anywhere on this surface, and its absence is not
 * a styling choice: no action descriptor for approval exists, no port method
 * returns an approval, and `ws04MayApprovePublication()` is a total function
 * returning false. Three independent things would have to change together for
 * an approval to become reachable, and the mutation suite attacks each of them.
 *
 * The open governance item is displayed rather than hidden: the accepted
 * transparency service has no proposal state at all, and pretending otherwise
 * would be inventing a server contract from the frontend.
 */
export function PublicationSurface() {
  const { runtime, bind, guarded, ready } = useWorkspace();
  const [proposal, setProposal] = useState<PublicationProposal | null>(null);
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [proposeRefusal, setProposeRefusal] = useState<SafeRefusal | null>(
    null,
  );

  useEffect(() => {
    // The provider resolves the session and the mandate scope asynchronously.
    // Reading before that finishes would bind against the anonymous session and
    // render a scope refusal that no later event clears — the surface would look
    // permanently refused to an operator who is, in fact, in scope.
    if (!ready) return;
    let cancelled = false;
    void (async () => {
      const api = await runtime();
      const bound = bind({ proposalId: "current" });
      if (!bound.ok) {
        if (!cancelled) setRefusal(bound.error);
        return;
      }
      const result = await api.publication.observe(bound.value);
      if (cancelled) return;
      if (result.ok) setProposal(result.value);
      else setRefusal(result.error);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, ready]);

  async function attemptPropose() {
    await guarded(async () => {
      const api = await runtime();
      const bound = bind({
        sourceKind: "position" as const,
        sourceId: proposal?.sourceId ?? "",
      });
      if (!bound.ok) {
        setProposeRefusal(bound.error);
        return;
      }
      const result = await api.publication.propose(bound.value);
      if (!result.ok) setProposeRefusal(result.error);
    });
  }

  const record = capabilityRecord("publication_proposal_submission");
  /** Always false. Referenced so a change to the policy fails a test here too. */
  const approvalReachable: boolean = ws04MayApprovePublication();

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.publication.title}
        lead={WS04_CONTENT.publication.lead}
      />
      <ScopeBanner />

      <Notice kind="legal" title="Vorschlag ist keine Freigabe" role="status">
        <p data-proposal-disclaimer>{PROPOSAL_DISCLAIMER}</p>
        <p>{WS04_CONTENT.publication.separationNotice}</p>
      </Notice>

      {refusal ? (
        <RefusalPanel
          title={WS04_CONTENT.publication.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {proposal === null ? (
        <DependencyPanel
          title={WS04_CONTENT.publication.unavailableTitle}
          dependency={
            capabilityRecord("publication_state_observation").missingDependency
          }
          behaviour={WS04_CONTENT.publication.stateUnknown}
        />
      ) : (
        <section className="card" data-proposal={proposal.proposalId}>
          <h2 className="card-title">{publicationLabel(proposal.state)}</h2>
          <dl className="metadata-list">
            <div>
              <dt>Quelle</dt>
              <dd>
                {proposal.sourceKind} — {proposal.sourceId}
              </dd>
            </div>
            <div>
              <dt>{WS04_CONTENT.publication.decidedBy}</dt>
              <dd data-decided-by={proposal.decidedBy ?? "none"}>
                {proposal.decidedBy ?? WS04_CONTENT.publication.stateUnknown}
              </dd>
            </div>
            <div>
              <dt>Öffentlich sichtbar</dt>
              <dd data-public={mayPresentAsPublic(proposal) ? "true" : "false"}>
                {mayPresentAsPublic(proposal) ? "ja" : "nein"}
              </dd>
            </div>
          </dl>
        </section>
      )}

      <section
        className="consequential-block"
        aria-labelledby="proposal-actions"
      >
        <h2 id="proposal-actions">Mögliche Handlungen</h2>
        <RevalidationNotice />
        <ul className="record-list">
          {PUBLICATION_ACTIONS.map((action) => (
            <li key={action.actionId} data-action={action.actionId}>
              <h3>{action.label}</h3>
              <p className="informational">{record.missingDependency}</p>
            </li>
          ))}
        </ul>
        <div className="action-row">
          <button
            type="button"
            className="button button--primary"
            onClick={() => void attemptPropose()}
          >
            Veröffentlichung vorschlagen
          </button>
        </div>
        <p
          className="informational"
          data-approval-reachable={approvalReachable ? "true" : "false"}
        >
          {WS04_CONTENT.publication.separationNotice}
        </p>
        {proposeRefusal ? (
          <RefusalPanel
            title={WS04_CONTENT.publication.proposeBlocked}
            refusal={proposeRefusal}
          />
        ) : null}
      </section>

      <section
        className="provenance"
        data-governance-gap
        data-classification={PUBLICATION_MODEL_GAP.classification}
      >
        <h2>Offener Governance-Punkt (sicherheitsrelevant)</h2>
        <dl className="metadata-list">
          <div>
            <dt>Festgestellt</dt>
            <dd>{PUBLICATION_MODEL_GAP.observed}</dd>
          </div>
          <div>
            <dt>Sicherheitsbefund</dt>
            <dd data-security-finding>
              {PUBLICATION_MODEL_GAP.securityFinding}
            </dd>
          </div>
          <div>
            <dt>Erforderlich</dt>
            <dd>{PUBLICATION_MODEL_GAP.required}</dd>
          </div>
          <div>
            <dt>Nicht ausreichend</dt>
            <dd>
              <ul>
                {PUBLICATION_MODEL_GAP.insufficientRemedies.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </dd>
          </div>
          <div>
            <dt>Behandlung</dt>
            <dd
              data-caller-asserted-sufficient={
                callerAssertedAuthorizationSufficient() ? "true" : "false"
              }
            >
              {PUBLICATION_MODEL_GAP.disposition}
            </dd>
          </div>
        </dl>
      </section>

      <GovernedFallback />
    </>
  );
}
