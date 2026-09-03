/**
 * DE/EN language model.
 *
 * `FRONT-02-LANGUAGE-AND-LOCALIZATION-MODEL.md` is binding: German is
 * authoritative for governed content; language is a rendition state of the same
 * route; an unknown locale fails safely to German; and the locale may never
 * change authorization, eligibility, scope, workflow state or legal effect.
 *
 * The failure conditions in §13 of that document are encoded here so a gate can
 * check them rather than a reviewer having to notice.
 */

export const LOCALES = Object.freeze(["de", "en"] as const);
export type Locale = (typeof LOCALES)[number];

export const AUTHORITATIVE_LOCALE: Locale = "de";

/** An unknown or unsupported locale fails safely to German. */
export function resolveLocale(value: string | null | undefined): Locale {
  return value === "en" ? "en" : "de";
}

/**
 * What a locale may never carry. A language preference that encoded any of
 * these would become a cross-workspace correlation handle.
 */
export const LOCALE_MUST_NOT_ENCODE = Object.freeze([
  "user_identity",
  "member_status",
  "political_interest",
  "organization_scope",
  "voting_eligibility",
  "voting_event_identity",
  "case_identifier",
  "cross_workspace_correlation_identifier",
] as const);

/** Changing language changes none of these. */
export const LOCALE_CHANGES_NOTHING_ABOUT = Object.freeze([
  "route_authority",
  "authorization",
  "eligibility",
  "organization_scope",
  "mandate_scope",
  "workflow_state",
  "legal_effect",
  "deadline",
  "publication_state",
  "conflict_status",
] as const);

export function localeAffects(subject: string): false {
  void subject;
  return false;
}

/** Translation status vocabulary for material governed content. */
export const TRANSLATION_STATUSES = Object.freeze([
  "draft",
  "under_review",
  "approved",
  "superseded",
] as const);

export type TranslationStatus = (typeof TRANSLATION_STATUSES)[number];

/**
 * A missing, stale or unapproved translation is never silently presented as
 * current authoritative content. The interface falls back to German and says so.
 */
export function mayPresentAsAuthoritative(
  locale: Locale,
  status: TranslationStatus,
): boolean {
  if (locale === AUTHORITATIVE_LOCALE) return true;
  return status === "approved";
}

/** The language preference is stored as a UI preference and nothing else. */
export const LOCALE_STORAGE = Object.freeze({
  purpose: "ui-preference",
  crossOriginSynchronisation: false,
  sharedIdentityStorage: false,
} as const);
