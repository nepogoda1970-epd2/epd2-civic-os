"use client";

import { useEffect, useState } from "react";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import { publicationLabel } from "../domain/publication";
import type { PositionRecord, SafeRefusal } from "../domain/types";
import { formatGovernedInstant } from "../policies/dateTime";
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
 * Positions.
 *
 * The composition field is real and usable: an operator can type, and what they
 * typed stays on screen. What the surface never does is imply the text went
 * anywhere. The save attempt returns the production refusal, the draft is
 * labelled unsaved, and no browser store receives it — which is the honest
 * behaviour when no accepted route persists a draft.
 */
export function PositionSurface() {
  const { runtime, bind, guarded, ready } = useWorkspace();
  const [positions, setPositions] = useState<readonly PositionRecord[] | null>(
    null,
  );
  const [refusal, setRefusal] = useState<SafeRefusal | null>(null);
  const [saveRefusal, setSaveRefusal] = useState<SafeRefusal | null>(null);
  const [body, setBody] = useState("");

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
      const result = await api.positions.list(bound.value);
      if (cancelled) return;
      if (result.ok) setPositions(result.value);
      else setRefusal(result.error);
    })();
    return () => {
      cancelled = true;
    };
  }, [runtime, bind, ready]);

  async function attemptSave() {
    await guarded(async () => {
      const api = await runtime();
      const bound = bind({ positionId: null, body });
      if (!bound.ok) {
        setSaveRefusal(bound.error);
        return;
      }
      const result = await api.positions.save(bound.value);
      if (!result.ok) setSaveRefusal(result.error);
    });
  }

  const record = capabilityRecord("position_draft_read");

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.positions.title}
        lead={WS04_CONTENT.positions.lead}
      />
      <ScopeBanner />

      {refusal ? (
        <RefusalPanel
          title={WS04_CONTENT.positions.unavailableTitle}
          refusal={refusal}
        />
      ) : null}

      {positions === null ? (
        <DependencyPanel
          title={WS04_CONTENT.positions.unavailableTitle}
          dependency={record.missingDependency}
          behaviour={record.frontendBehaviour}
        />
      ) : (
        <ul className="record-list" data-position-list>
          {positions.map((position) => (
            <li key={position.positionId} data-position={position.positionId}>
              <h3>{position.title}</h3>
              <dl className="metadata-list">
                <div>
                  <dt>Stand</dt>
                  <dd data-position-state={position.state}>
                    {WS04_CONTENT.positions.states[position.state]}
                  </dd>
                </div>
                <div>
                  <dt>Veröffentlichung</dt>
                  <dd
                    data-publication-state={
                      position.publicationState ?? "unknown"
                    }
                  >
                    {position.publicationState === null
                      ? WS04_CONTENT.publication.stateUnknown
                      : publicationLabel(position.publicationState)}
                  </dd>
                </div>
                <div>
                  <dt>{WS04_CONTENT.desk.versionLabel}</dt>
                  <dd>{position.version}</dd>
                </div>
                <div>
                  <dt>Geändert</dt>
                  <dd>{formatGovernedInstant(position.updatedAt)}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}

      <section className="consequential-block" aria-labelledby="position-draft">
        <h2 id="position-draft">Entwurf</h2>
        <Notice kind="warning" title="Entwurf nicht gespeichert">
          <p>{WS04_CONTENT.positions.draftNotSaved}</p>
        </Notice>
        <div className="form-field">
          <label htmlFor="position-body">Text der Position</label>
          <textarea
            id="position-body"
            name="position-body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
        </div>
        <RevalidationNotice />
        <div className="action-row">
          <button
            type="button"
            className="button button--primary"
            onClick={() => void attemptSave()}
          >
            Entwurf speichern
          </button>
        </div>
        {saveRefusal ? (
          <RefusalPanel
            title={WS04_CONTENT.positions.saveBlocked}
            refusal={saveRefusal}
          />
        ) : null}
      </section>

      <GovernedFallback />
    </>
  );
}
