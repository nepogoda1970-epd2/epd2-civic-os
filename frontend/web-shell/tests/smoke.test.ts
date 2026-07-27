import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

// A minimal, dependency-free smoke test reads the route and governed content
// sources directly. Render-level assertions live in front01.render.test.tsx.
// See docs/canonical/TZ-00-domain-event-canon.md's CLAUDE-PACK-01
// requirement: "Добавь минимальный smoke test, проверяющий наличие
// заголовка EPD² Civic OS."

const here = dirname(fileURLToPath(import.meta.url));
const pageSource = readFileSync(join(here, "..", "app", "page.tsx"), "utf-8");
const contentSource = readFileSync(
  join(here, "..", "public", "content.ts"),
  "utf-8",
);

test("home page renders the governed EPD² public page", () => {
  assert.match(pageSource, /PublicPageView/);
  assert.match(contentSource, /EPD² · Partei, Plattform und Civic OS/);
  assert.match(
    contentSource,
    /Politische Beteiligung, nachvollziehbar aufgebaut/,
  );
});

test("home page does not reference forbidden concerns", () => {
  assert.doesNotMatch(pageSource + contentSource, /api\/|fetch\(|<form/i);
});
