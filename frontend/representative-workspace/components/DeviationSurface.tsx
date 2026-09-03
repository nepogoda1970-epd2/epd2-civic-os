"use client";

import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import {
  DEVIATION_LIMITS,
  validateDeviationDraft,
  type DeviationDraft,
} from "../domain/deviation";
import type { DeviationRecord, SafeRefusal } from "../domain/types";
import { formatGovernedInstant } from "../policies/dateTime";
import { ScopeBanner } from "./ScopeBanner";
import {
  DependencyPanel,
  ErrorSummary,
  GovernedFallback,
  Notice,
  PageHeader,
  RefusalPanel,
  RevalidationNotice,
} from "./primitives";
import { useWorkspace } from "./WorkspaceProvider";

const EMPTY: DeviationDraft = {
  issue: "",
  representativePosition: "",
  referencedDecision: null,
  explanation: "",
  supersedes: null,
};

/**
 * Deviations.
 *
 * Local validation runs and is useful — an unexplained deviation is not a
 * record — but a local pass is displayed as a local pass, never as acceptance.
 * The decision reference is carried as unverified text and labelled so, because
 * no accepted route resolves a decision identifier and claiming the reference
 * is valid would be the exact kind of invented certainty this stage forbids.
 */
export function DeviationSurface() {
  const { runtime, bind, guarded, ready } = useWorkspace();
  const [records, setRecords] = useState<readonly DeviationRecord[] | null>(
    null,
  );
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [recordRefusal, setRecordRefusal] = useState<SafeRefusal | null>(null);
  const [draft, setDraft] = useState<DeviationDraft>(EMPTY);
  const [errors, setErrors] = useState<
    readonly { readonly id: string; readonly message: string }[]
  >([]);

  useEffect(() => {
    // The provider resolves the session and the mandate scope asynchronously.
    // Reading before that finishes would bind against the anonymous session and
    // render a scope refusal that no later event clears — the surface would look
    // permanently refused to an operator who is, in fact, in scope.
    if (!ready) return;
    let cancelled = false;
    void (async () => {
      const api = await runtime();
      const bound = bind({});
      if (!bound.ok) {
        if (!cancelled) setRefusal(bound.error);
        return;
      }
      const result = await api.deviations.list(bound.value);
      if (cancelled) return;
      if (result.ok) setRecords(result.value);
      else setRefusal(result.error);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, ready]);

  async function attemptRecord() {
    const validated = validateDeviationDraft(draft);
    if (!validated.ok) {
      setErrors([
        { id: "deviation-explanation", message: validated.error.safeMessage },
      ]);
      return;
    }
    setErrors([]);
    await guarded(async () => {
      const api = await runtime();
      const bound = bind({ draft });
      if (!bound.ok) {
        setRecordRefusal(bound.error);
        return;
      }
      const result = await api.deviations.record(bound.value);
      if (!result.ok) setRecordRefusal(result.error);
    });
  }

  const record = capabilityRecord("deviation_record_read");

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.deviations.title}
        lead={WS04_CONTENT.deviations.lead}
      />
      <ScopeBanner />

      <Notice kind="legal" title="Wirkung einer Abweichung">
        <p>{WS04_CONTENT.deviations.doesNotAlter}</p>
      </Notice>

      {refusal ? (
        <RefusalPanel
          title={WS04_CONTENT.deviations.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {records === null ? (
        <DependencyPanel
          title={WS04_CONTENT.deviations.unavailableTitle}
          dependency={record.missingDependency}
          behaviour={record.frontendBehaviour}
        />
      ) : (
        <ul className="record-list" data-deviation-list>
          {records.map((item) => (
            <li key={item.deviationId} data-deviation={item.deviationId}>
              <h3>{item.issue}</h3>
              <dl className="metadata-list">
                <div>
                  <dt>{WS04_CONTENT.deviations.position}</dt>
                  <dd>{item.representativePosition}</dd>
                </div>
                <div>
                  <dt>{WS04_CONTENT.deviations.referencedDecision}</dt>
                  <dd data-reference-verified="false">
                    {item.referencedDecision ?? "—"}
                    <span className="informational">
                      {" "}
                      {WS04_CONTENT.deviations.referenceUnverified}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>{WS04_CONTENT.deviations.explanation}</dt>
                  <dd>{item.explanation}</dd>
                </div>
                <div>
                  <dt>{WS04_CONTENT.desk.versionLabel}</dt>
                  <dd>
                    {item.version}
                    {item.supersedes
                      ? ` — ${WS04_CONTENT.deviations.supersededBy} ${item.supersedes}`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt>Erfasst</dt>
                  <dd>{formatGovernedInstant(item.recordedAt)}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}

      <section className="consequential-block" aria-labelledby="deviation-new">
        <h2 id="deviation-new">Abweichung erfassen</h2>
        <ErrorSummary title="Bitte prüfen" items={errors} />
        <div className="form-field">
          <label htmlFor="deviation-issue">
            {WS04_CONTENT.deviations.issue}
          </label>
          <input
            id="deviation-issue"
            name="deviation-issue"
            maxLength={DEVIATION_LIMITS.issueMaxLength}
            value={draft.issue}
            onChange={(event) =>
              setDraft({ ...draft, issue: event.target.value })
            }
          />
        </div>
        <div className="form-field">
          <label htmlFor="deviation-decision">
            {WS04_CONTENT.deviations.referencedDecision}
          </label>
          <p>{WS04_CONTENT.deviations.referenceUnverified}</p>
          <input
            id="deviation-decision"
            name="deviation-decision"
            value={draft.referencedDecision ?? ""}
            onChange={(event) =>
              setDraft({
                ...draft,
                referencedDecision:
                  event.target.value.length === 0 ? null : event.target.value,
              })
            }
          />
        </div>
        <div className="form-field">
          <label htmlFor="deviation-explanation">
            {WS04_CONTENT.deviations.explanation}
          </label>
          <textarea
            id="deviation-explanation"
            name="deviation-explanation"
            maxLength={DEVIATION_LIMITS.explanationMaxLength}
            value={draft.explanation}
            onChange={(event) =>
              setDraft({ ...draft, explanation: event.target.value })
            }
          />
        </div>
        <RevalidationNotice />
        <div className="action-row">
          <button
            type="button"
            className="button button--primary"
            onClick={() => void attemptRecord()}
          >
            Abweichung erfassen
          </button>
        </div>
        {recordRefusal ? (
          <RefusalPanel
            title={WS04_CONTENT.deviations.recordBlocked}
            refusal={recordRefusal}
          />
        ) : null}
      </section>

      <GovernedFallback />
    </>
  );
}
