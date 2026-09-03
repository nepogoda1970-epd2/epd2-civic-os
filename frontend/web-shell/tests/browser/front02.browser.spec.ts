import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = [
  "/aktuelles",
  "/presse",
  "/termine",
  "/regionen",
  "/personen",
  "/wahlen",
  "/hilfe",
  "/suche",
];
const detailRoutes = [
  "/aktuelles/aufbau",
  "/presse/stellungnahme",
  "/termine/berlin",
  "/regionen/berlin",
  "/personen/sprecherin",
  "/wahlen/bundestag",
];
const redirects = [
  ["/home", "/"],
  ["/principles", "/grundsaetze"],
  ["/participate", "/mitmachen"],
  ["/structure", "/struktur"],
  ["/news", "/aktuelles"],
  ["/elections", "/wahlen"],
  ["/aktuelle-wahlen", "/wahlen"],
  ["/donate", "/spenden"],
  ["/technology", "/technologie"],
  ["/roadmap", "/status"],
  ["/faq", "/hilfe"],
  ["/kandidieren", "/kandidatur"],
  ["/mitglied-werden", "/mitgliedschaft"],
] as const;

test("@front02 public information architecture and fixture details are reachable", async ({
  page,
}) => {
  for (const route of routes) {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("h1")).toHaveCount(1);
  }
  for (const route of detailRoutes) {
    await page.goto(route);
    await expect(page.locator("[data-front02-detail]")).toBeVisible();
    await expect(page.getByText("Fixturequelle FRONT-02")).toBeVisible();
  }
  await page.goto("/aktuelles/unknown");
  await expect(page.getByRole("heading", { name: "404" })).toBeVisible();
});

test("@front02 locale is URL-bound, visible and preserves navigation", async ({
  page,
}) => {
  await page.goto("/hilfe?lang=en");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(
    page.getByRole("heading", { name: "Help", exact: true }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Über uns" }).click();
  await expect(page).toHaveURL(/lang=en/);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByText("English rendition unavailable.")).toBeVisible();
  await expect(page.locator(".public-hero")).toHaveAttribute("lang", "de");
  await page.goto("/hilfe?lang=invalid");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  await page.getByRole("button", { name: "EN" }).press("Enter");
  await expect(page).toHaveURL(/lang=en/);
});

test("@front02 redirects retain locale hints", async ({ page }) => {
  for (const [source, target] of redirects) {
    await page.goto(`${source}?lang=en`);
    await expect(page).toHaveURL(
      new RegExp(`${target === "/" ? "127.0.0.1:3100/" : target}.*lang=en`),
    );
  }
});

test("@front02 system state and separate workspace shells are explicit", async ({
  page,
}) => {
  await page.goto("/foundation/front02");
  for (const state of [
    "not_found",
    "auth_required",
    "session_expired",
    "loading",
    "empty",
    "validation",
    "stale_conflict",
    "duplicate",
    "dependency_unavailable",
    "partial_outage",
    "maintenance",
    "upload_failed",
    "submission_interrupted",
    "read_only",
    "retry",
    "offline_channel",
    "completed",
    "receipt_evidence",
  ])
    await expect(page.locator(`[data-front02-state="${state}"]`)).toBeVisible();
  for (let index = 1; index <= 10; index += 1)
    await expect(
      page.locator(
        `[data-front02-workspace="WS-${String(index).padStart(2, "0")}"]`,
      ),
    ).toBeVisible();
  const a11y = await new AxeBuilder({ page }).analyze();
  expect(
    a11y.violations.filter(({ impact }) =>
      ["serious", "critical"].includes(impact ?? ""),
    ),
  ).toEqual([]);
});
