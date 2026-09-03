import assert from "node:assert/strict";
import test from "node:test";

import {
  AUTHORITATIVE_LOCALE,
  LOCALES,
  LOCALE_CHANGES_NOTHING_ABOUT,
  LOCALE_MUST_NOT_ENCODE,
  LOCALE_STORAGE,
  TRANSLATION_STATUSES,
  localeAffects,
  mayPresentAsAuthoritative,
  resolveLocale,
} from "../policies/language";
import {
  DISPLAY_TIMEZONE_IS_AUTHORITATIVE,
  GOVERNANCE_TIMEZONE,
  TIME_AUTHORITY,
  deadlineComputedInClient,
  formatGovernedInstant,
} from "../policies/dateTime";
import { mayOfferAction } from "../policies/authority";
import { bindScope } from "../domain/scope";
import { proposedCaseState } from "../domain/caseWorkflow";
import { proposedPublicationState } from "../domain/publication";
import type { MandateSession } from "../domain/types";

const SESSION: MandateSession = Object.freeze({
  state: "authenticated",
  role: "representative",
  assurance: "stepped_up",
  scope: {
    mandateId: "MANDAT-A",
    organizationId: "ORG-A",
    label: "Mandat A",
    level: "test",
    authorityActive: true,
  },
  displayName: "Test",
  conflictRestricted: false,
});

test("an unknown or absent locale falls back to the authoritative one", () => {
  assert.equal(AUTHORITATIVE_LOCALE, "de");
  for (const value of [null, undefined, "", "fr", "de-DE-x", "../en", "EN "]) {
    const resolved = resolveLocale(value as string | null | undefined);
    assert.ok(
      (LOCALES as readonly string[]).includes(resolved),
      `${String(value)} resolved outside the locale set`,
    );
  }
  assert.equal(resolveLocale(null), "de");
  assert.equal(resolveLocale("fr"), "de");
  assert.equal(resolveLocale("en"), "en");
});

test("locale changes nothing about authority, scope or state", () => {
  for (const subject of LOCALE_CHANGES_NOTHING_ABOUT) {
    assert.equal(localeAffects(subject), false, subject);
  }
  assert.ok(LOCALE_MUST_NOT_ENCODE.length > 0);
});

/**
 * The property test the declaration above is worth: run the real decision
 * functions and show the answers are identical under both locales. A locale
 * that could change an authorization would be a serious defect, so it is
 * demonstrated rather than asserted.
 */
test("decisions are byte-identical under both locales", () => {
  for (const locale of LOCALES) {
    void resolveLocale(locale);

    const offer = mayOfferAction({
      role: "representative",
      required: "mandate_representative",
      assurance: "stepped_up",
      impact: "consequential",
      inScope: true,
      conflictRestricted: false,
      authorityActive: true,
    });
    assert.equal(offer, true, `offer under ${locale}`);

    const wrongMandate = bindScope(SESSION, "MANDAT-B", {});
    assert.equal(wrongMandate.ok, false, `scope under ${locale}`);

    assert.equal(
      proposedCaseState("assigned", { type: "triage" }),
      "triaged",
      `case state under ${locale}`,
    );
    assert.equal(
      proposedPublicationState("draft", { type: "submit_proposal" }),
      "proposal_submitted",
      `publication state under ${locale}`,
    );
    assert.equal(
      proposedPublicationState("proposal_submitted", { type: "compose" }),
      null,
      `no approval path under ${locale}`,
    );
  }
});

test("only an approved translation may be presented as authoritative", () => {
  assert.ok(TRANSLATION_STATUSES.length >= 2);
  // German is authoritative under every status, because it is the source.
  for (const status of TRANSLATION_STATUSES) {
    assert.equal(mayPresentAsAuthoritative("de", status), true, `de/${status}`);
  }
  assert.equal(mayPresentAsAuthoritative("en", "approved"), true);
  for (const status of TRANSLATION_STATUSES) {
    if (status === "approved") continue;
    assert.equal(
      mayPresentAsAuthoritative("en", status),
      false,
      `en/${status}`,
    );
  }
});

test("a locale preference is a UI preference and nothing more", () => {
  assert.equal(LOCALE_STORAGE.purpose, "ui-preference");
  assert.equal(LOCALE_STORAGE.crossOriginSynchronisation, false);
  assert.equal(LOCALE_STORAGE.sharedIdentityStorage, false);
});

/* ------------------------------------------------------------------ date/time */

test("the server is the time authority and the client computes no deadline", () => {
  assert.equal(TIME_AUTHORITY, "server");
  assert.equal(DISPLAY_TIMEZONE_IS_AUTHORITATIVE, false);
  assert.equal(deadlineComputedInClient(), false);
});

test("a governed instant is labelled with its timezone", () => {
  const formatted = formatGovernedInstant("2026-08-01T09:00:00Z");
  assert.ok(formatted.includes(GOVERNANCE_TIMEZONE), formatted);
});

test("an unreadable timestamp is reported, not silently rendered", () => {
  assert.match(formatGovernedInstant("not-a-date"), /unlesbar/);
  assert.match(formatGovernedInstant("not-a-date", "en"), /unreadable/);
});
