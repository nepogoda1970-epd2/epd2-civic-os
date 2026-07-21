import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

// A minimal, dependency-free smoke test: this repository skeleton has no
// running server or React test renderer available yet, so the check reads
// the page source directly and asserts the required heading is present.
// See docs/canonical/TZ-00-domain-event-canon.md's CLAUDE-PACK-01
// requirement: "Добавь минимальный smoke test, проверяющий наличие
// заголовка EPD² Civic OS."

const here = dirname(fileURLToPath(import.meta.url));
const pageSource = readFileSync(join(here, "..", "app", "page.tsx"), "utf-8");

test("home page renders the required EPD² Civic OS heading", () => {
  assert.match(pageSource, /<h1>EPD² Civic OS<\/h1>/);
});

test("home page does not reference forbidden concerns", () => {
  assert.doesNotMatch(pageSource, /api\/|fetch\(|<form/i);
});
