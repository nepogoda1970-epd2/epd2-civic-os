/**
 * PACK-15 — rendition layer for the voting trust boundary.
 *
 * Server components only. Nothing here reads or writes browser storage,
 * performs a network call, or renders credential material. The isolated
 * voting shell deliberately shares no code path that carries identity
 * state: it does not use the member workspace shell and renders no
 * navigation, no profile and no account menu.
 *
 * NOT PRODUCTION READY. NOT LEGALLY ACTIVATED.
 */

import type { ReactNode } from "react";

import {
  Card,
  LinkButton,
  MetadataList,
  Notice,
  StatePanel,
} from "./foundation";
import type { PresentationState } from "../foundation/types";
import type {
  ParticipationMarkerKind,
  ParticipationStateId,
} from "../foundation/voting-trust-policy";
import { participationStateById } from "../foundation/voting-trust-policy";
import type { ParticipationStateText } from "../public/voting-content";
import { VOTING_CONTENT } from "../public/voting-content";

/**
 * Participation states map onto the shared presentation-state vocabulary so
 * that badge shape and structure stay consistent with the rest of the
 * system. No participation state maps onto a "success after casting"
 * meaning, because no such state exists.
 */
const PRESENTATION_STATE: Record<ParticipationStateId, PresentationState> = {
  eligibility_pending: "under_review",
  eligibility_confirmed: "ready",
  review_required: "under_review",
  eligibility_denied: "forbidden",
  access_queued: "partial",
  access_available: "ready",
  access_expired: "not_available",
  dispute_open: "under_review",
};

/** Shape-based markers. Colour is never the sole carrier of a state. */
const MARKER_GLYPH: Record<ParticipationMarkerKind, string> = {
  dot: "●",
  clock: "◔",
  check: "✓",
  crossed: "✕",
  key: "⚿",
  expired: "⌛",
};

function ParticipationMarker({
  kind,
  label,
}: {
  kind: ParticipationMarkerKind;
  label: string;
}) {
  return (
    <p className="participation-marker" data-marker={kind}>
      <span aria-hidden="true">{MARKER_GLYPH[kind]}</span>{" "}
      <strong>{label}</strong>
      <span className="visually-hidden">
        {" "}
        ({VOTING_CONTENT.markerLabels[kind]})
      </span>
    </p>
  );
}

const ACTION_LABELS: Readonly<Record<string, string>> =
  VOTING_CONTENT.actionLabels;

function ActionList({ actions }: { actions: readonly string[] }) {
  if (actions.length === 0) {
    return <p>{VOTING_CONTENT.noActionAvailable}</p>;
  }
  return (
    <>
      <p>{VOTING_CONTENT.actionsHeading}</p>
      <ul className="structured-list">
        {actions.map((action) => (
          <li key={action}>{ACTION_LABELS[action] ?? action}</li>
        ))}
      </ul>
    </>
  );
}

export function VotingContextCard({
  contextName,
  votingType,
  scope,
  windowLabel,
}: {
  contextName: string;
  votingType: string;
  scope: string;
  windowLabel: string;
}) {
  const { labels } = VOTING_CONTENT.contextSummary;
  return (
    <Card title={VOTING_CONTENT.contextSummary.cardTitle}>
      <MetadataList
        items={[
          { term: labels.contextName, description: contextName },
          { term: labels.votingType, description: votingType },
          { term: labels.scope, description: scope },
          { term: labels.window, description: windowLabel },
        ]}
      />
      <p>{VOTING_CONTENT.contextSummary.separationNote}</p>
    </Card>
  );
}

export function EligibilityStatePanel({
  state,
}: {
  state: ParticipationStateId;
}) {
  const definition = participationStateById(state);
  const text: ParticipationStateText = VOTING_CONTENT.states[state];
  return (
    <div className="participation-state" data-participation-state={state}>
      <StatePanel state={PRESENTATION_STATE[state]} title={text.title}>
        <ParticipationMarker
          kind={definition.markerKind}
          label={definition.labelDe}
        />
        <p>{text.body}</p>
        {text.note ? <p>{text.note}</p> : null}
        <p>{text.nextStep}</p>
        <ActionList actions={definition.actions} />
      </StatePanel>
    </div>
  );
}

/**
 * Availability of the one-time access. A queue position, an estimated
 * waiting time and a countdown are prohibited: they leak cohort structure
 * and apply pressure. The deadline is stated as a plain date.
 */
export function AccessAvailabilityPanel({
  state,
  expiresLabel,
}: {
  state: Extract<
    ParticipationStateId,
    "access_queued" | "access_available" | "access_expired"
  >;
  expiresLabel: string;
}) {
  const definition = participationStateById(state);
  const text: ParticipationStateText = VOTING_CONTENT.states[state];
  const { heading, windowLabel, noCountdownNote } =
    VOTING_CONTENT.accessAvailability;
  return (
    <Card title={heading}>
      <div className="access-availability" data-participation-state={state}>
        <h3>{text.title}</h3>
        <ParticipationMarker
          kind={definition.markerKind}
          label={definition.labelDe}
        />
        <p>{text.body}</p>
        {text.note ? <p>{text.note}</p> : null}
        <MetadataList
          items={[{ term: windowLabel, description: expiresLabel }]}
        />
        <p>{noCountdownNote}</p>
        <p>{text.nextStep}</p>
      </div>
    </Card>
  );
}

/**
 * Explicit departure from the member area. The crossing is never automatic
 * and never a form submission; both choices are ordinary links.
 */
export function HandoffDepartureNotice() {
  const departure = VOTING_CONTENT.departure;
  return (
    <Card title={departure.title}>
      <div className="handoff-departure" data-boundary="WS-02-to-WS-03">
        <p>{departure.body}</p>
        <p>{departure.deliveryNote}</p>
        <p>
          <strong>{departure.declarationLabel}:</strong> {departure.declaration}
        </p>
        <div className="page-actions">
          <LinkButton href={departure.continueHref} variant="primary">
            {departure.continueLabel}
          </LinkButton>
          <LinkButton href={departure.cancelHref} variant="secondary">
            {departure.cancelLabel}
          </LinkButton>
        </div>
      </div>
    </Card>
  );
}

/**
 * Minimal shell for the isolated voting origin (WS-03). No shared shell, no
 * navigation, no profile, no account menu, no link back into the member
 * area, no measurement of any kind.
 */
export function IsolatedVotingShell({ children }: { children: ReactNode }) {
  return (
    <div className="voting-shell" data-workspace="WS-03">
      <a className="skip-link" href="#main-content">
        Zum Inhalt springen
      </a>
      <main className="main" id="main-content" tabIndex={-1}>
        {children}
      </main>
      <footer className="footer">
        <span>Abstimmungsbereich</span>
        <span>
          Getrennter Bereich — keine Angaben zu Ihrer Person, keine
          Nutzungsdaten, keine Verbindung zu Ihrem Konto.
        </span>
      </footer>
    </div>
  );
}

/**
 * The waiting state while the one-time access is minted and immediately
 * redeemed inside the voting origin. Announced politely to assistive
 * technology; no numeric progress, no countdown, no queue position, and
 * nothing about the access itself is announced.
 */
export function CredentialExchangeWaitingPanel() {
  const waiting = VOTING_CONTENT.waiting;
  return (
    <section
      aria-atomic="true"
      aria-live="polite"
      className="state-panel"
      data-voting-step="access-exchange"
      role="status"
    >
      <ParticipationMarker kind="clock" label={waiting.title} />
      <h2>{waiting.title}</h2>
      <p>{waiting.body}</p>
      <p>{waiting.note}</p>
    </section>
  );
}

export function AccessRedeemedPanel() {
  const redeemed = VOTING_CONTENT.redeemed;
  return (
    <Card title={redeemed.title}>
      <ParticipationMarker kind="check" label={redeemed.title} />
      <p>{redeemed.body}</p>
      <Notice kind="information" title="Nächster Schritt">
        <p>{redeemed.transition}</p>
      </Notice>
    </Card>
  );
}
