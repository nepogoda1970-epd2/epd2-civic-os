/**
 * Time.
 *
 * The server is authoritative for deadlines and timestamps. The browser's
 * timezone is a display preference and must never silently change the
 * governance meaning of a deadline — so every rendered instant carries an
 * explicit zone label, and a deadline is never computed in the client.
 */

export const TIME_AUTHORITY = "server" as const;

export const DISPLAY_TIMEZONE_IS_AUTHORITATIVE = false as const;

/** The zone a governed instant is stated in, alongside any local rendering. */
export const GOVERNANCE_TIMEZONE = "Europe/Berlin" as const;

export function deadlineComputedInClient(): false {
  return false;
}

/**
 * Render an instant with its zone made explicit. The label is part of the
 * string rather than a tooltip, because a deadline whose zone is only
 * discoverable on hover is a deadline that will be misread.
 */
export function formatGovernedInstant(
  isoInstant: string,
  locale: "de" | "en" = "de",
): string {
  const parsed = new Date(isoInstant);
  if (Number.isNaN(parsed.getTime())) {
    return locale === "de" ? "Zeitangabe unlesbar" : "unreadable timestamp";
  }
  const formatted = new Intl.DateTimeFormat(
    locale === "de" ? "de-DE" : "en-GB",
    {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: GOVERNANCE_TIMEZONE,
    },
  ).format(parsed);
  return `${formatted} (${GOVERNANCE_TIMEZONE})`;
}
