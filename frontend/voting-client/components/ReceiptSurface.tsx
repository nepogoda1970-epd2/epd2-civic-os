"use client";

import { useRef, useState } from "react";

import { WS03_CONTENT } from "../content/de";
import { capability } from "../domain/capabilities";
import {
  confirmationCodeWellFormed,
  groupConfirmationCode,
  RECEIPT_PERMITTED_FIELDS,
} from "../domain/receipt";
import type { Receipt, SafeRefusal } from "../domain/types";
import {
  CapabilityBadge,
  ErrorSummary,
  GovernedFallback,
  Notice,
  RefusalPanel,
} from "./primitives";
import { AssistancePanel } from "./assistance";
import { resolveVotingRuntime } from "../runtime/compose";

/**
 * PAGE-019 — Stimmabgabe verifizieren.
 *
 * The lookup is by confirmation code, by keyboard, on this origin.  No camera
 * is required and no machine-readable form is offered as the only path.  The
 * receipt renderer prints the permitted fields and nothing else; there is no
 * branch in this component that can render a choice, because the type it
 * accepts has no field that could hold one.
 */
export function ReceiptSurface() {
  const [code, setCode] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const inFlight = useRef(false);

  const record = capability("receipt_verification");
  const recordedAsCast = capability("recorded_as_cast_verification");

  async function check(event: React.FormEvent) {
    event.preventDefault();
    if (inFlight.current) return;
    if (!confirmationCodeWellFormed(code)) {
      setInvalid(true);
      setReceipt(null);
      setRefusal(null);
      return;
    }
    setInvalid(false);
    inFlight.current = true;
    setBusy(true);
    try {
      const runtime = await resolveVotingRuntime();
      const result = await runtime.receipt.readReceipt(code);
      if (result.ok) {
        setReceipt(result.value);
        setRefusal(null);
      } else {
        setReceipt(null);
        setRefusal(result.error);
      }
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>{WS03_CONTENT.receipt.title}</h1>
        <p>{WS03_CONTENT.receipt.lead}</p>
      </div>

      <p>
        <CapabilityBadge status={record.status} />{" "}
        <span className="informational">Nachweisprüfung</span>{" "}
        <CapabilityBadge status={recordedAsCast.status} />{" "}
        <span className="informational">Veröffentlichungsprüfung</span>
      </p>

      <ErrorSummary
        title="Bitte prüfen Sie Ihre Eingabe"
        items={
          invalid
            ? [
                {
                  id: "confirmation-code",
                  message: WS03_CONTENT.receipt.codeInvalid,
                },
              ]
            : []
        }
      />

      <form onSubmit={check} noValidate>
        <div className="form-field">
          <label htmlFor="confirmation-code">
            {WS03_CONTENT.receipt.codeLabel}
          </label>
          <p id="confirmation-code-hint">{WS03_CONTENT.receipt.codeHint}</p>
          <input
            id="confirmation-code"
            name="confirmation-code"
            type="text"
            inputMode="text"
            autoComplete="off"
            spellCheck={false}
            value={code}
            aria-describedby="confirmation-code-hint"
            aria-invalid={invalid || undefined}
            onChange={(event) => setCode(event.target.value)}
          />
          {invalid ? (
            <p className="validation-message">
              {WS03_CONTENT.receipt.codeInvalid}
            </p>
          ) : null}
        </div>
        <button
          type="submit"
          className="button button--primary"
          disabled={busy}
        >
          {WS03_CONTENT.receipt.check}
        </button>
      </form>

      {busy ? (
        <p role="status" aria-live="polite">
          {WS03_CONTENT.states.loading}
        </p>
      ) : null}

      {refusal ? (
        <RefusalPanel
          title={WS03_CONTENT.receipt.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {receipt ? <ReceiptView receipt={receipt} /> : null}

      <Notice kind="information" title={WS03_CONTENT.receipt.neverShows}>
        <p>{WS03_CONTENT.receipt.neverShowsBody}</p>
        <p>{WS03_CONTENT.receipt.doNotShare}</p>
      </Notice>

      <AssistancePanel />
      <GovernedFallback />
    </>
  );
}

const FIELD_LABELS: Record<(typeof RECEIPT_PERMITTED_FIELDS)[number], string> =
  {
    electionContextReference: "Abstimmungskontext",
    confirmationCode: "Nachweiscode",
    boardCheckpointReference: "Veröffentlichungsstand",
    sealedBatchReference: "Veröffentlichungsblock",
    publicationStatus: "Veröffentlichungsstatus",
    verificationInstructions: "Prüfhinweis",
    receiptSchemaVersion: "Nachweisversion",
    countingStatus: "Zählstatus",
  };

/**
 * The receipt renderer.  It iterates the permitted field list, so a field that
 * is not permitted cannot be displayed even if one somehow reached the object.
 */
export function ReceiptView({ receipt }: { receipt: Receipt }) {
  return (
    <section className="state-panel" data-receipt>
      <h2>Nachweis</h2>
      <p className="confirmation-code" aria-label="Nachweiscode in Gruppen">
        {groupConfirmationCode(receipt.confirmationCode)}
      </p>
      <dl className="metadata-list">
        {RECEIPT_PERMITTED_FIELDS.filter(
          (field) => field !== "confirmationCode",
        ).map((field) => (
          <div key={field}>
            <dt>{FIELD_LABELS[field]}</dt>
            <dd>{receipt[field]}</dd>
          </div>
        ))}
      </dl>
      <p>{WS03_CONTENT.receipt.doNotShare}</p>
    </section>
  );
}
