import assert from "node:assert/strict";
import test from "node:test";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { CONTENT_VERSION, WS04_CONTENT } from "../content/de";
import { CONTENT_VERSION_EN, WS04_CONTENT_EN } from "../content/en";
import {
  FRONT05_DESIGN_CHANGE_DECISIONS,
  INHERITED_DESIGN_TOKENS,
  PRESERVATION_RULES,
} from "../policies/visualBaseline";

const HERE = resolve(import.meta.dirname, "..");
const GLOBALS = resolve(HERE, "../web-shell/app/globals.css");
const WORKSPACE_CSS = resolve(HERE, "app/workspace.css");

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
  const mine = tokensOf(readFileSync(WORKSPACE_CSS, "utf8"));
  for (const [name, value] of Object.entries(INHERITED_DESIGN_TOKENS)) {
    assert.equal(inherited.get(name), value, `${name} in globals.css`);
    assert.equal(mine.get(name), value, `${name} in workspace.css`);
  }
  // This workspace introduces no token of its own.
  for (const name of mine.keys()) {
    assert.ok(
      name in INHERITED_DESIGN_TOKENS,
      `workspace.css introduces an unregistered token: ${name}`,
    );
  }
});

test("the shared primitive rules keep the inherited proportions", () => {
  const inherited = readFileSync(GLOBALS, "utf8");
  const mine = readFileSync(WORKSPACE_CSS, "utf8");
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
      `missing from workspace.css: ${rule.slice(0, 40)}`,
    );
  }
});

test("the WS-04 additions use only inherited tokens", () => {
  const mine = readFileSync(WORKSPACE_CSS, "utf8");
  const additions = mine.slice(mine.indexOf("/*\n * WS-04 additions."));
  assert.ok(additions.length > 0, "the additions block must be identifiable");
  // No literal colour may appear in the additions: every colour is a token.
  const literalColours = additions.match(/#[0-9a-fA-F]{3,8}\b/g) ?? [];
  assert.deepEqual(
    literalColours,
    [],
    `the WS-04 additions introduce literal colours: ${literalColours.join(", ")}`,
  );
});

test("the four permitted deviations are the only ones declared", () => {
  assert.equal(PRESERVATION_RULES.focusRingPx, 3);
  assert.equal(PRESERVATION_RULES.minimumInteractiveTargetPx, 44);
  assert.equal(PRESERVATION_RULES.statusCarriesTextNotColourAlone, true);
  assert.equal(PRESERVATION_RULES.authorityNoticesStateNonActivation, true);
  assert.equal(PRESERVATION_RULES.fixtureOrDisabledWhereBackendAbsent, true);
});

test("no Design Change Decision was raised, so none may be claimed", () => {
  assert.deepEqual(FRONT05_DESIGN_CHANGE_DECISIONS, []);
});

test("the interactive minimum target size is enforced in the stylesheet", () => {
  const mine = readFileSync(WORKSPACE_CSS, "utf8");
  assert.ok(mine.includes("min-height: 44px;"));
});

test("content versions are declared and distinct per language", () => {
  assert.equal(CONTENT_VERSION, "F05-DE-1.0.0");
  assert.equal(CONTENT_VERSION_EN, "F05-EN-1.0.0");
  assert.notEqual(CONTENT_VERSION, CONTENT_VERSION_EN);
});

test("the candidate notice states non-activation in both languages", () => {
  for (const text of [
    WS04_CONTENT.candidateNotice,
    WS04_CONTENT_EN.candidateNotice,
  ]) {
    assert.ok(text.length > 0);
  }
  assert.match(WS04_CONTENT.candidateNotice, /nicht freigegeben/);
  assert.match(WS04_CONTENT.candidateNotice, /rechtlich nicht aktiviert/);
  assert.match(WS04_CONTENT_EN.candidateNotice, /not legally activated/);
});

test("no content string claims certification or acceptance", () => {
  const forbidden = [
    /BSI[- ]zertifiziert/i,
    /BSI certified/i,
    /CC[- ]compliant/i,
    /EAL4/i,
    /FRONT-05 ACCEPTED/i,
    /production ready/i,
    /produktionsbereit/i,
  ];
  const blob = JSON.stringify(WS04_CONTENT) + JSON.stringify(WS04_CONTENT_EN);
  for (const pattern of forbidden) {
    assert.ok(!pattern.test(blob), `forbidden claim present: ${pattern}`);
  }
});
