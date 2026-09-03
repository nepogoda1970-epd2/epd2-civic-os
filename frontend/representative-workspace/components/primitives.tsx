import type { ReactNode } from "react";

import type { CapabilityStatus, SafeRefusal } from "../domain/types";
import { WS04_CONTENT } from "../content/de";

/**
 * The presentation primitives, reproduced from the immutable FRONT-00/FRONT-01
 * component language. Same markup shape, same class names, same tone. None of
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
  SUPPORTED_REAL_PATH: "neutral",
  SUPPORTED_WITH_DECLARED_LIMITATION: "limited",
  BLOCKED_BY_DEPENDENCY: "blocked",
  UNSUPPORTED: "blocked",
};

const CAPABILITY_LABEL: Record<CapabilityStatus, string> = {
  SUPPORTED_REAL_PATH: "verfügbar",
  SUPPORTED_WITH_DECLARED_LIMITATION: "eingeschränkt",
  BLOCKED_BY_DEPENDENCY: "nicht verfügbar",
  UNSUPPORTED: "nicht vorgesehen",
};

/**
 * A capability is never described as active unless the register says it is a
 * real path. The label comes from the status, not from the caller.
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
 * The refusal panel. For every failure the operator is told what happened,
 * whether anything was committed, and what can safely be done next. The three
 * are structural, not optional, because a refusal that omits one of them is
 * the kind that invents certainty.
 *
 * `data-refusal` carries the reason code and never the resource identifier, so
 * a non-disclosing refusal stays non-disclosing in the DOM as well as on screen.
 */
export function RefusalPanel({
  title,
  refusal,
}: {
  title: string;
  refusal: SafeRefusal;
}) {
  const committed =
    refusal.committed === "committed"
      ? WS04_CONTENT.states.committedYes
      : refusal.committed === "not_committed"
        ? WS04_CONTENT.states.committedNo
        : WS04_CONTENT.states.committedUnknown;
  return (
    <section
      className="state-panel"
      role="alert"
      data-refusal={refusal.reasonCode}
      data-non-disclosing={refusal.nonDisclosing ? "true" : "false"}
    >
      <h2>{title}</h2>
      <p>{refusal.safeMessage}</p>
      <dl className="metadata-list">
        <div>
          <dt>{WS04_CONTENT.states.commitStatus}</dt>
          <dd>{committed}</dd>
        </div>
        <div>
          <dt>{WS04_CONTENT.states.nextStep}</dt>
          <dd>{refusal.nextSafeAction}</dd>
        </div>
      </dl>
    </section>
  );
}

/**
 * A blocked capability, rendered with the exact missing dependency. Naming the
 * dependency is the difference between "this is broken" and "this is waiting on
 * a named, governed thing" — and only the second is actionable for the operator
 * and honest for the reviewer.
 */
export function DependencyPanel({
  title,
  dependency,
  behaviour,
}: {
  title: string;
  dependency: string;
  behaviour: string;
}) {
  return (
    <section className="state-panel" data-dependency-panel>
      <h2>{title}</h2>
      <dl className="metadata-list">
        <div>
          <dt>{WS04_CONTENT.states.dependency}</dt>
          <dd>{dependency}</dd>
        </div>
        <div>
          <dt>{WS04_CONTENT.states.nextStep}</dt>
          <dd>{behaviour}</dd>
        </div>
      </dl>
    </section>
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
    <Notice kind="information" title={WS04_CONTENT.fallback.title}>
      <p>{WS04_CONTENT.fallback.body}</p>
    </Notice>
  );
}

/**
 * The statement that a visible control is not an authorization. It is rendered
 * beside every consequential action, because "the button was enabled" is the
 * most common way a client-side check gets mistaken for a decision.
 */
export function RevalidationNotice() {
  return (
    <p className="informational" data-revalidation-notice>
      {WS04_CONTENT.auth.revalidationNotice}
    </p>
  );
}

export function PageHeader({ title, lead }: { title: string; lead?: string }) {
  return (
    <div className="page-header">
      <h1>{title}</h1>
      {lead ? <p>{lead}</p> : null}
    </div>
  );
}
