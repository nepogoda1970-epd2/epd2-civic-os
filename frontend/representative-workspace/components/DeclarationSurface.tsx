"use client";

import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import {
  OBLIGATION_REMAINS_OPEN,
  validateDeclarationDraft,
  type DeclarationDraft,
} from "../domain/declaration";
import type { DeclarationRecord, SafeRefusal } from "../domain/types";
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

const EMPTY: DeclarationDraft = {
  kind: "meeting",
  subject: "",
  occurredAt: "",
  counterparty: "",
  summary: "",
};

/**
 * Declarations.
 *
 * The blunt sentence at the end of the blocked path is the point of this
 * surface. A representative who fills in a meeting declaration and sees a
 * neutral "could not send" may reasonably assume the system will retry. It will
 * not, and the obligation is theirs, so the interface says the obligation
 * remains open and names the governed route that still discharges it.
 */
export function DeclarationSurface() {
  const { runtime, bind, guarded, ready } = useWorkspace();
  const [records, setRecords] = useState<readonly DeclarationRecord[] | null>(
    null,
  );
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [submitRefusal, setSubmitRefusal] = useState<SafeRefusal | null>(null);
  const [draft, setDraft] = useState<DeclarationDraft>(EMPTY);
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
      const result = await api.declarations.list(bound.value);
      if (cancelled) return;
      if (result.ok) setRecords(result.value);
      else setRefusal(result.error);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, ready]);

  async function attemptSubmit() {
    const validated = validateDeclarationDraft(draft);
    if (!validated.ok) {
      setErrors([
        { id: "declaration-subject", message: validated.error.safeMessage },
      ]);
      return;
    }
    setErrors([]);
    await guarded(async () => {
      const api = await runtime();
      const bound = bind({ draft });
      if (!bound.ok) {
        setSubmitRefusal(bound.error);
        return;
      }
      const result = await api.declarations.submit(bound.value);
      if (!result.ok) setSubmitRefusal(result.error);
    });
  }

  const record = capabilityRecord("declaration_read");

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.declarations.title}
        lead={WS04_CONTENT.declarations.lead}
      />
      <ScopeBanner />

      {refusal ? (
        <RefusalPanel
          title={WS04_CONTENT.declarations.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {records === null ? (
        <DependencyPanel
          title={WS04_CONTENT.declarations.unavailableTitle}
          dependency={record.missingDependency}
          behaviour={record.frontendBehaviour}
        />
      ) : (
        <ul className="record-list" data-declaration-list>
          {records.map((item) => (
            <li key={item.declarationId} data-declaration={item.declarationId}>
              <h3>{item.subject}</h3>
              <dl className="metadata-list">
                <div>
                  <dt>Art</dt>
                  <dd>{WS04_CONTENT.declarations.kinds[item.kind]}</dd>
                </div>
                <div>
                  <dt>{WS04_CONTENT.declarations.occurredAt}</dt>
                  <dd>{item.occurredAt}</dd>
                </div>
                <div>
                  <dt>Stand</dt>
                  <dd data-declaration-state={item.state}>
                    {item.submittedAt === null
                      ? OBLIGATION_REMAINS_OPEN
                      : item.state}
                  </dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}

      <section
        className="consequential-block"
        aria-labelledby="declaration-new"
      >
        <h2 id="declaration-new">Erklärung erfassen</h2>
        <ErrorSummary title="Bitte prüfen" items={errors} />
        <div className="form-field">
          <label htmlFor="declaration-kind">Art</label>
          <select
            id="declaration-kind"
            name="declaration-kind"
            value={draft.kind}
            onChange={(event) =>
              setDraft({
                ...draft,
                kind: event.target.value as DeclarationDraft["kind"],
              })
            }
          >
            <option value="meeting">
              {WS04_CONTENT.declarations.kinds.meeting}
            </option>
            <option value="declaration">
              {WS04_CONTENT.declarations.kinds.declaration}
            </option>
            <option value="disclosure">
              {WS04_CONTENT.declarations.kinds.disclosure}
            </option>
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="declaration-subject">
            {WS04_CONTENT.declarations.subject}
          </label>
          <input
            id="declaration-subject"
            name="declaration-subject"
            value={draft.subject}
            onChange={(event) =>
              setDraft({ ...draft, subject: event.target.value })
            }
          />
        </div>
        <div className="form-field">
          <label htmlFor="declaration-date">
            {WS04_CONTENT.declarations.occurredAt}
          </label>
          <input
            id="declaration-date"
            name="declaration-date"
            type="date"
            value={draft.occurredAt}
            onChange={(event) =>
              setDraft({ ...draft, occurredAt: event.target.value })
            }
          />
        </div>
        <div className="form-field">
          <label htmlFor="declaration-counterparty">
            {WS04_CONTENT.declarations.counterparty}
          </label>
          <input
            id="declaration-counterparty"
            name="declaration-counterparty"
            value={draft.counterparty}
            onChange={(event) =>
              setDraft({ ...draft, counterparty: event.target.value })
            }
          />
        </div>
        <RevalidationNotice />
        <div className="action-row">
          <button
            type="button"
            className="button button--primary"
            onClick={() => void attemptSubmit()}
          >
            Erklärung übermitteln
          </button>
        </div>
        {submitRefusal ? (
          <>
            <RefusalPanel
              title={WS04_CONTENT.declarations.submitBlocked}
              refusal={submitRefusal}
            />
            <Notice
              kind="danger"
              title="Meldepflicht bleibt offen"
              role="alert"
            >
              <p data-obligation-open>
                {WS04_CONTENT.declarations.obligationOpen}
              </p>
            </Notice>
          </>
        ) : null}
      </section>

      <GovernedFallback />
    </>
  );
}
