import assert from "node:assert/strict";
import test from "node:test";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { AUTHORITATIVE_DE_TITLES, WS03_CONTENT_EN } from "../content/en";
import { CONTENT_VERSION, WS03_CONTENT } from "../content/de";
import {
  FRONT04_DESIGN_CHANGE_DECISIONS,
  INHERITED_DESIGN_TOKENS,
} from "../policies/visualBaseline";

const HERE = resolve(import.meta.dirname, "..");
const GLOBALS = resolve(HERE, "../web-shell/app/globals.css");
const VOTING_CSS = resolve(HERE, "app/voting.css");

function tokensOf(css: string): Map<string, string> {
  const block = css.slice(
    css.indexOf(":root {"),
    css.indexOf("}", css.indexOf(":root {")),
  );
  const map = new Map<string, string>();
  for (const line of block.split("\n")) {
    const match = line.match(/^\s*(--[a-z0-9-]+):\s*(.+);\s*$/);
    if (match) map.set(match[1], match[2].trim());
  }
  return map;
}

test("the inherited design tokens are reproduced without modification", () => {
  assert.ok(existsSync(GLOBALS), "the FRONT-00/01 stylesheet must be present");
  const inherited = tokensOf(readFileSync(GLOBALS, "utf8"));
  const mine = tokensOf(readFileSync(VOTING_CSS, "utf8"));
  for (const [name, value] of Object.entries(INHERITED_DESIGN_TOKENS)) {
    assert.equal(inherited.get(name), value, `${name} in globals.css`);
    assert.equal(mine.get(name), value, `${name} in voting.css`);
  }
  // The Voting Client introduces no token of its own.
  for (const name of mine.keys()) {
    assert.ok(
      name in INHERITED_DESIGN_TOKENS,
      `voting.css introduces an unregistered token: ${name}`,
    );
  }
});

test("the shared primitive rules keep the inherited proportions", () => {
  const inherited = readFileSync(GLOBALS, "utf8");
  const mine = readFileSync(VOTING_CSS, "utf8");
  // A sample of load-bearing declarations, compared literally.
  for (const rule of [
    "padding: 1.75rem;\n  border: 1px solid var(--card-border);\n  border-radius: var(--radius-lg);\n  background: var(--white);",
    "padding: 0.75rem 1.375rem;\n  border: 1px solid transparent;\n  border-radius: var(--radius-sm);\n  cursor: pointer;",
    "background: #2c2c2c;\n  color: var(--white);",
    "outline: 3px solid var(--focus);\n  outline-offset: 2px;",
    "position: fixed;\n  z-index: var(--z-overlay);\n  left: 1rem;\n  top: -5rem;",
  ]) {
    assert.ok(
      inherited.includes(rule),
      `missing from globals.css: ${rule.slice(0, 40)}`,
    );
    assert.ok(
      mine.includes(rule),
      `missing from voting.css: ${rule.slice(0, 40)}`,
    );
  }
});

test("no Design Change Decision was raised, so no token may have moved", () => {
  assert.deepEqual([...FRONT04_DESIGN_CHANGE_DECISIONS], []);
});

test("the reduced-motion and 44px target rules are carried over", () => {
  const mine = readFileSync(VOTING_CSS, "utf8");
  assert.match(mine, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(mine, /min-height: 44px;/);
});

test("the four canonical German page titles are exact", () => {
  assert.equal(WS03_CONTENT.credential.title, "Stimmberechtigung übernehmen");
  assert.equal(WS03_CONTENT.ballot.title, "Stimmzettel");
  assert.equal(WS03_CONTENT.review.title, "Stimme prüfen");
  assert.equal(WS03_CONTENT.receipt.title, "Stimmabgabe verifizieren");
  assert.deepEqual(AUTHORITATIVE_DE_TITLES, {
    "/vote/credential": "Stimmberechtigung übernehmen",
    "/vote/ballot": "Stimmzettel",
    "/vote/review": "Stimme prüfen",
    "/vote/receipt": "Stimmabgabe verifizieren",
  });
});

test("the content catalogue is versioned and German is authoritative", () => {
  assert.equal(CONTENT_VERSION, "F04-DE-1.0.0");
  assert.match(
    WS03_CONTENT_EN.languageChangesNothing,
    /no route authority.*no eligibility.*no cast semantics/s,
  );
});

test("no interface text claims a completed cast, certification or activation", () => {
  const catalogue = JSON.stringify(WS03_CONTENT);
  for (const phrase of [
    "Sie haben abgestimmt",
    "Ihre Stimme wurde abgegeben",
    "Ihre Stimme wurde gezählt",
    "Sie haben teilgenommen",
    "Stimme erfolgreich",
    "Stimmabgabe erfolgreich",
    "BSI-zertifiziert",
    "produktionsbereit",
    "rechtsverbindlich",
  ]) {
    assert.ok(!catalogue.includes(phrase), phrase);
  }
  // Certification and activation appear only as negations, and the prototype
  // banner is where they appear.
  for (const match of catalogue.matchAll(
    /zertifiziert|aktiviert|freigegeben/g,
  )) {
    const window = catalogue.slice(Math.max(0, match.index - 40), match.index);
    assert.match(
      window,
      /nicht |keine |noch nicht |kein /,
      `unqualified claim near: ${catalogue.slice(Math.max(0, match.index - 40), match.index + 20)}`,
    );
  }
  assert.match(WS03_CONTENT.candidateNotice, /nicht zertifiziert/);
  assert.match(WS03_CONTENT.candidateNotice, /rechtlich nicht aktiviert/);
});

test("the interface states the no-tally rule to the voter", () => {
  assert.match(WS03_CONTENT.noTally, /keine Zwischenstände/);
  assert.match(WS03_CONTENT.noTally, /keine Beteiligungszahlen/);
});
