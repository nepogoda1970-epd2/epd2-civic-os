import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { resolve } from "node:path";

import { publicPages, topNavigation } from "../public/content";
import { capabilityStatuses } from "../public/status";

const requiredRoutes = [
  "/",
  "/ueber-uns",
  "/ziele",
  "/grundsaetze",
  "/programm",
  "/programm/struktur",
  "/programm/status",
  "/mitmachen",
  "/mitgliedschaft",
  "/organisation",
  "/struktur",
  "/transparenz",
  "/technologie",
  "/sicherheit",
  "/datenschutz",
  "/barrierefreiheit",
  "/kontakt",
  "/impressum",
  "/initiativen",
  "/beratung",
  "/abstimmungen",
  "/ki-assistenz",
  "/buergerbuero",
  "/abgeordnetentisch",
  "/finanzen",
  "/versammlungen",
  "/kandidatur",
  "/compliance",
  "/rechtsgovernance",
] as const;

test("FRONT-01 implements every required public route in WS-01", () => {
  const routes = new Set(publicPages.map((page) => page.path));
  for (const route of requiredRoutes) assert.ok(routes.has(route), route);
  assert.equal(
    new Set(publicPages.map((page) => page.id)).size,
    publicPages.length,
  );
  assert.ok(publicPages.length >= 30);
});

test("every capability uses a controlled status and complete banner metadata", () => {
  const allowed = new Set<string>(capabilityStatuses);
  for (const page of publicPages) {
    assert.ok(allowed.has(page.status), `${page.path}: ${page.status}`);
    assert.ok(page.pack.length > 0);
    assert.ok(page.prerequisites.length > 0);
  }
});

test("navigation is coherent, limited and points to real routes", () => {
  assert.equal(topNavigation.length, 8);
  const routes = new Set(publicPages.map((page) => page.path));
  for (const link of topNavigation) assert.ok(routes.has(link.href));
});

test("audit C1 corrects PACK-09 and C6 keeps PACK-10 non-runtime", () => {
  const text = publicPages
    .flatMap((page) => [
      page.title,
      page.lead,
      ...page.sections.flatMap((s) => [s.title, s.text]),
    ])
    .join("\n");
  assert.match(text, /PACK-09 ist FINAL PASS/);
  assert.doesNotMatch(text, /PACK-09 CANDIDATE-2/);
  const finance = publicPages.find((page) => page.path === "/finanzen")!;
  assert.equal(finance.status, "specified");
  assert.match(
    finance.sections.map((section) => section.text).join(" "),
    /nicht aktiv/,
  );
});

test("voting remains explanation-only with the complete isolation boundary", () => {
  const vote = publicPages.find((page) => page.path === "/abstimmungen")!;
  const text = [
    vote.lead,
    ...vote.sections.map((section) => section.text),
  ].join(" ");
  assert.equal(vote.status, "not_activated");
  for (const phrase of [
    "Eigener Origin",
    "keine gemeinsamen Cookies",
    "kein gemeinsamer LocalStorage oder IndexedDB",
    "keine gemeinsame Identitätssitzung",
    "keine Analytics",
    "kein Fingerprinting",
    "ein einmaliges, zweckgebundenes Übergabeartefakt",
    "keine dauerhafte Mitgliedskennung",
    "keine Stimmzetteldaten",
    "Zwischenauszählungen sind ausgeschlossen",
    "Systembrowser",
  ])
    assert.match(text, new RegExp(phrase, "i"));
});

test("citizen office and representative desk keep ownership and access separate", () => {
  const office = publicPages.find((page) => page.path === "/buergerbuero")!;
  const representative = publicPages.find(
    (page) => page.path === "/abgeordnetentisch",
  )!;
  assert.equal(office.pack, "PACK-33");
  assert.equal(representative.pack, "PACK-29");
  assert.match(representative.lead, /nicht direkt auf WS-04/);
});

test("program skeleton and lifecycle controlled states are present in source", () => {
  const component = readFileSync(
    resolve(process.cwd(), "components/public-site.tsx"),
    "utf8",
  );
  for (const state of [
    "empty",
    "in_formation",
    "partially_formed",
    "formed",
    "under_revision",
    "conflict_detected",
    "superseded",
  ])
    assert.match(component, new RegExp(`"${state}"`));
  for (const step of [
    "Entwurf",
    "Formal- und Risikoprüfung",
    "Zulässigkeitsentscheidung",
    "Unterstützungsphase",
    "Rechts- und Fachprüfung",
    "Abstimmungsreife",
    "Umsetzung und Fortschritt",
  ])
    assert.match(component, new RegExp(step));
});

test("all 61 legacy HTML pages have exactly one migration decision", () => {
  const csv = readFileSync(
    resolve(
      process.cwd(),
      "../../docs/frontend/FRONT-01-LEGACY-MIGRATION-MAP.csv",
    ),
    "utf8",
  )
    .trim()
    .split(/\r?\n/);
  assert.equal(csv.length - 1, 61);
  const sources = csv.slice(1).map((line) => line.split(",")[0]);
  assert.equal(new Set(sources).size, 61);
});

test("FRONT-01 source contains no operational forms or cross-workspace client assumptions", () => {
  const component = readFileSync(
    resolve(process.cwd(), "components/public-site.tsx"),
    "utf8",
  );
  const content = readFileSync(
    resolve(process.cwd(), "public/content.ts"),
    "utf8",
  );
  assert.doesNotMatch(component, /<form|<input|<textarea|<select/);
  assert.doesNotMatch(
    component + content,
    /document\.cookie|localStorage\.setItem|indexedDB\.open|analytics\(/,
  );
  assert.doesNotMatch(
    component + content,
    /castVote|submitDonation|createCase/,
  );
});
