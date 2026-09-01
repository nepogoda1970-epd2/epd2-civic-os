"use client";

import { useId, useState } from "react";

import { Bilingual, formatDate } from "./Bilingual";
import type { Bilingual as BilingualPair } from "./labels";
import { LABELS } from "./labels";
import type { OrganizationStatus } from "./data";
import { statusAsOf } from "./data";

interface HistoryEntry {
  status: OrganizationStatus;
  effective_from: string;
}

/**
 * Current / historical state selector for an organization's status.
 * Resolves purely against the static `status_history` sample array in
 * data.ts (see `statusAsOf`) — no network request, no server action.
 */
export function AsOfSelector({
  history,
  statusLabels,
}: {
  history: HistoryEntry[];
  statusLabels: Record<string, BilingualPair>;
}) {
  const selectId = useId();
  const [asOf, setAsOf] = useState<string>(
    history[history.length - 1].effective_from,
  );

  const resolvedStatus = statusAsOf({ status_history: history }, asOf);

  return (
    <div role="group" aria-label={LABELS.asOfSelectorLabel.de}>
      <label htmlFor={selectId}>
        <Bilingual pair={LABELS.asOfSelectorLabel} />
      </label>
      <p className="hint">
        <Bilingual pair={LABELS.asOfSelectorHint} />
      </p>
      <select
        id={selectId}
        value={asOf}
        onChange={(event) => setAsOf(event.target.value)}
      >
        {history.map((entry) => (
          <option key={entry.effective_from} value={entry.effective_from}>
            {formatDate(entry.effective_from)} —{" "}
            {statusLabels[entry.status]?.de ?? entry.status}
          </option>
        ))}
      </select>
      <p aria-live="polite">
        <Bilingual pair={LABELS.currentStatusAsOf} />:{" "}
        <strong>
          <Bilingual
            pair={
              statusLabels[resolvedStatus] ?? {
                de: resolvedStatus,
                en: resolvedStatus,
              }
            }
          />
        </strong>
      </p>
    </div>
  );
}
