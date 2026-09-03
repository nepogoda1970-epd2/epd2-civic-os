import type { ReactNode } from "react";

import type {
  CapabilityStatus,
  JourneyState,
  SafeRefusal,
} from "../domain/types";
import { commitKnowledge } from "../domain/types";
import { WS03_CONTENT } from "../content/de";

/**
 * The presentation primitives, reproduced from the immutable FRONT-00/FRONT-01
 * component language.  Same markup shape, same class names, same tone.  None of
 * them is imported from the Member Workspace, because importing it would create
 * the shared runtime boundary the isolation rule forbids.
 */

export function Notice({
  kind = "information",
  title,
  children,
  role,
}: {
  kind?: "information" | "warning" | "legal" | "danger";
  title: string;
  children: ReactNode;
  role?: "status" | "alert";
}) {
  return (
    <section
      className={`notice notice--${kind}`}
      role={role}
      aria-label={role ? undefined : title}
    >
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function StatusBadge({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: "neutral" | "blocked" | "limited" | "failed" | "uncertain";
}) {
  return (
    <span className={`status-badge status-badge--${tone}`}>
      <span className="status-badge__marker" aria-hidden="true" />
      {label}
    </span>
  );
}

const CAPABILITY_TONE: Record<
  CapabilityStatus,
  "neutral" | "blocked" | "limited"
> = {
  AVAILABLE_ACCEPTED_RUNTIME: "neutral",
  AVAILABLE_REFERENCE_ONLY: "limited",
  LIMITED: "limited",
  BLOCKED_RUNTIME_CONTRACT: "blocked",
  BLOCKED_CRYPTO: "blocked",
  BLOCKED_INFRA: "blocked",
  BLOCKED_LEGAL: "blocked",
  BLOCKED_SECURITY_REVIEW: "blocked",
  PLANNED: "limited",
};

const CAPABILITY_LABEL: Record<CapabilityStatus, string> = {
  AVAILABLE_ACCEPTED_RUNTIME: "verfügbar",
  AVAILABLE_REFERENCE_ONLY: "nur Referenz",
  LIMITED: "eingeschränkt",
  BLOCKED_RUNTIME_CONTRACT: "nicht verfügbar",
  BLOCKED_CRYPTO: "nicht verfügbar",
  BLOCKED_INFRA: "nicht verfügbar",
  BLOCKED_LEGAL: "nicht verfügbar",
  BLOCKED_SECURITY_REVIEW: "nicht verfügbar",
  PLANNED: "geplant",
};

/**
 * A capability is never described as active unless it is an accepted runtime.
 * The label comes from the status, not from the caller.
 */
export function CapabilityBadge({ status }: { status: CapabilityStatus }) {
  return (
    <StatusBadge
      label={CAPABILITY_LABEL[status]}
      tone={CAPABILITY_TONE[status]}
    />
  );
}

/**
 * The refusal panel.  For every failure the voter is told what happened,
 * whether anything was committed, whether the entitlement is known to remain
 * usable, and what can safely be done next.  The four are structural, not
 * optional, because a refusal that omits one of them is the kind that invents
 * certainty.
 */
export function RefusalPanel({
  title,
  refusal,
}: {
  title: string;
  refusal: SafeRefusal;
}) {
  const committed =
    refusal.commitKnowledge === "committed"
      ? WS03_CONTENT.states.committedYes
      : refusal.commitKnowledge === "not_committed"
        ? WS03_CONTENT.states.committedNo
        : WS03_CONTENT.states.committedUnknown;
  return (
    <section
      className="state-panel"
      role="alert"
      data-refusal={refusal.reasonCode}
    >
      <h2>{title}</h2>
      <p>{refusal.safeMessage}</p>
      <dl className="metadata-list">
        <div>
          <dt>Stand der Abgabe</dt>
          <dd>{committed}</dd>
        </div>
        <div>
          <dt>Stimmberechtigung</dt>
          <dd>
            {refusal.entitlementKnownIntact
              ? WS03_CONTENT.states.entitlementIntact
              : WS03_CONTENT.states.entitlementUnknown}
          </dd>
        </div>
        <div>
          <dt>{WS03_CONTENT.states.nextStep}</dt>
          <dd>{refusal.nextSafeAction}</dd>
        </div>
      </dl>
    </section>
  );
}

/**
 * The journey position, announced politely so a screen-reader user hears the
 * state change without losing their place.
 */
export function JourneyStatus({ state }: { state: JourneyState }) {
  const knowledge = commitKnowledge(state);
  return (
    <p
      role="status"
      aria-live="polite"
      className="informational"
      data-journey-state={state}
      data-commit-knowledge={knowledge}
    >
      {knowledge === "committed"
        ? WS03_CONTENT.states.committedYes
        : knowledge === "not_committed"
          ? WS03_CONTENT.states.committedNo
          : WS03_CONTENT.states.committedUnknown}
    </p>
  );
}

export function ErrorSummary({
  title,
  items,
}: {
  title: string;
  items: readonly { readonly id: string; readonly message: string }[];
}) {
  if (items.length === 0) return null;
  return (
    <div
      className="error-summary"
      role="alert"
      tabIndex={-1}
      id="error-summary"
    >
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <a href={`#${item.id}`}>{item.message}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function GovernedFallback() {
  return (
    <Notice kind="information" title={WS03_CONTENT.fallback.title}>
      <p>{WS03_CONTENT.fallback.body}</p>
    </Notice>
  );
}
