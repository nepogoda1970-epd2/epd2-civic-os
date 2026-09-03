"use client";

import { WS04_CONTENT } from "../content/de";
import { capabilityRecord } from "../domain/capabilities";
import {
  CONFLICT_ACTIONS,
  anyRestrictionActive,
  mayClearOwnRestriction,
  refusalFor,
  restrictionNotice,
} from "../domain/conflict";
import { formatGovernedInstant } from "../policies/dateTime";
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
 * Conflict restrictions.
 *
 * The behaviour worth reading closely is the unknown case. When the restriction
 * register cannot be read — which is the state at this baseline — the surface
 * reports "restricted", not "no restrictions found". Treating unknown as
 * cleared would hand a conflicted representative access to exactly the material
 * the restriction exists to withhold, and it would do so silently.
 *
 * There is no control to clear a restriction over oneself. No descriptor
 * exists, no port method exists, and `maySelfClearConflict` returns false for
 * every role.
 */
export function ConflictSurface() {
  const { restrictions, session } = useWorkspace();
  const record = capabilityRecord("conflict_restriction_read");
  const notice = restrictionNotice(session);
  /** Always false. Rendered so a policy change fails a browser assertion too. */
  const selfClear: boolean =
    session.role === null ? false : mayClearOwnRestriction(session.role);

  return (
    <>
      <PageHeader
        title={WS04_CONTENT.conflicts.title}
        lead={WS04_CONTENT.conflicts.lead}
      />
      <ScopeBanner />

      <Notice kind="legal" title="Zuständigkeit">
        <p data-no-self-clear={selfClear ? "true" : "false"}>
          {WS04_CONTENT.conflicts.noSelfClear}
        </p>
        <p>{WS04_CONTENT.conflicts.unknownIsRestricted}</p>
      </Notice>

      {notice ? (
        <p className="informational" data-restriction-notice>
          {notice}
        </p>
      ) : null}

      {restrictions.known ? (
        <ul className="record-list" data-restriction-list>
          {restrictions.restrictions.map((item) => (
            <li key={item.restrictionId} data-restriction={item.restrictionId}>
              <h3>{item.scopeLabel}</h3>
              <dl className="metadata-list">
                <div>
                  <dt>{WS04_CONTENT.conflicts.scopeLabel}</dt>
                  <dd>{item.scopeLabel}</dd>
                </div>
                <div>
                  <dt>Stand</dt>
                  <dd data-restriction-active={item.active ? "true" : "false"}>
                    {item.active ? WS04_CONTENT.conflicts.activeLabel : "—"}
                  </dd>
                </div>
                <div>
                  <dt>Erfasst</dt>
                  <dd>{formatGovernedInstant(item.recordedAt)}</dd>
                </div>
                <div>
                  <dt>Hinweis</dt>
                  <dd>{item.safeReason}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      ) : (
        <>
          <RefusalPanel
            title={WS04_CONTENT.conflicts.unavailableTitle}
            refusal={refusalFor(restrictions)}
          />
          <DependencyPanel
            title={WS04_CONTENT.conflicts.unavailableTitle}
            dependency={record.missingDependency}
            behaviour={record.frontendBehaviour}
          />
        </>
      )}

      <p
        className="informational"
        data-any-restriction-active={
          anyRestrictionActive(restrictions) ? "true" : "false"
        }
      >
        {WS04_CONTENT.conflicts.unknownIsRestricted}
      </p>

      <section
        className="consequential-block"
        aria-labelledby="conflict-actions"
      >
        <h2 id="conflict-actions">Handlungen der zuständigen Stelle</h2>
        <ul className="record-list">
          {CONFLICT_ACTIONS.map((action) => (
            <li key={action.actionId} data-action={action.actionId}>
              <h3>{action.label}</h3>
              <p className="informational">
                Vorbehalten der Stelle für Interessenkonflikte.
              </p>
            </li>
          ))}
        </ul>
      </section>

      <GovernedFallback />
    </>
  );
}
