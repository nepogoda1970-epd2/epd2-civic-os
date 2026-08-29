import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const allowed = (project: string, names: readonly string[]) => names.includes(project);
const masks = (page: Page) => [page.locator(".candidate-banner")];
async function snap(page: Page, name: string) {
  await expect(page).toHaveScreenshot(name, {
    fullPage: true,
    mask: masks(page),
    maskColor: "#fff8dc",
  });
}

test.describe("FRONT-02 acceptance inventory", () => {
  test("@front02 @visual F02-SS-01 homepage DE", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "de");
    await expect(page.getByText("Erste Partei Direkte Demokratie")).toBeVisible();
    await snap(page, "F02-SS-01-home-de.png");
  });

  test("@front02 @visual F02-SS-02 homepage EN", async ({ page }, info) => {
    test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
    await page.goto("/?lang=en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator('[data-locale="en"]')).toBeVisible();
    await expect(page.locator('[data-translation-state="fallback"]')).toBeVisible();
    await snap(page, "F02-SS-02-home-en.png");
  });

  for (const [id, path, heading] of [
    ["F02-SS-03", "/aktuelles", "Aktuelles"],
    ["F02-SS-04", "/regionen", "Regionen"],
    ["F02-SS-05", "/presse", "Presse"],
    ["F02-SS-05", "/termine", "Termine"],
    ["F02-SS-06", "/hilfe", "Hilfe"],
    ["F02-SS-06", "/suche", "Suche"],
  ] as const) {
    test(`@front02 @visual ${id} ${path}`, async ({ page }, info) => {
      test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await snap(page, `${id}-${path.slice(1)}.png`);
    });
  }

  test("@front02 @visual F02-SS-03 unavailable detail", async ({ page }, info) => {
    test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
    await page.goto("/aktuelles/nicht-verfuegbar");
    await expect(page.getByRole("heading", { level: 1, name: "Öffentliche Rendition nicht verfügbar" })).toBeVisible();
    await expect(page.getByText("Kein Datensatz wird vorausgesetzt")).toBeVisible();
    await snap(page, "F02-SS-03-detail-unavailable.png");
  });

  test("@front02 @visual F02-SS-04 regional hub", async ({ page }, info) => {
    test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
    await page.goto("/regionen/beispiel");
    await expect(page.getByRole("navigation", { name: "Regionale Bereiche" })).toBeVisible();
    await expect(page.getByText(/Organisation-Scope: Beispielregion/)).toBeVisible();
    await snap(page, "F02-SS-04-regional-hub.png");
  });

  test("@front02 @visual F02-SS-07 transparency hub", async ({ page }, info) => {
    test.skip(info.project.name !== "desktop");
    await page.goto("/transparenz");
    for (const heading of ["Politik & Entscheidungen", "Finanzen & Dokumente", "Technologie & Civic OS"]) {
      await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    }
    await expect(page.locator('[data-projection-state="stale"]')).toBeVisible();
    await snap(page, "F02-SS-07-transparency.png");
  });

  for (const [id, shot] of [
    ["ws-02", "F02-SS-08-ws02.png"],
    ["ws-03", "F02-SS-09-ws03.png"],
    ["ws-06", "F02-SS-10-ws06.png"],
    ["ws-10", "F02-SS-10-ws10.png"],
  ] as const) {
    test(`@front02 @visual workspace ${id}`, async ({ page }, info) => {
      test.skip(info.project.name !== "desktop");
      await page.goto(`/foundation/workspaces/${id}`);
      await expect(page.locator(`[data-workspace="${id.toUpperCase()}"]`)).toBeVisible();
      await expect(page.getByText("Keine gemeinsame Sitzung")).toBeVisible();
      await snap(page, shot);
    });
  }

  test("@front02 @visual F02-SS-11 translation fallback", async ({ page }, info) => {
    test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
    await page.goto("/satzung?lang=en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator('[data-translation-state="fallback"]')).toBeVisible();
    await snap(page, "F02-SS-11-translation-fallback.png");
  });

  for (const [name, path] of [
    ["404", "/front02-does-not-exist"],
    ["denied", "/foundation/states/denied"],
    ["error", "/foundation/states/error"],
    ["recovery", "/foundation/states/recovery"],
  ] as const) {
    test(`@front02 @visual F02-SS-12 ${name}`, async ({ page }, info) => {
      test.skip(!allowed(info.project.name, ["mobile", "desktop"]));
      await page.goto(path);
      await page.keyboard.press("Tab");
      await expect(page.getByRole("link", { name: "Zum Inhalt springen" })).toBeFocused();
      await snap(page, `F02-SS-12-${name}.png`);
    });
  }
});

test.describe("FRONT-02 routes and boundaries", () => {
  for (const [path, heading] of [
    ["/aktuelles", "Aktuelles"], ["/presse", "Presse"], ["/termine", "Termine"],
    ["/regionen", "Regionen"], ["/personen", "Personen"], ["/wahlen", "Wahlen"],
    ["/hilfe", "Hilfe"], ["/suche", "Suche"],
  ] as const) {
    test(`@front02 route ${path}`, async ({ page }) => {
      await page.goto(path);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await expect(page.locator('[data-workspace="WS-01"]')).toBeVisible();
    });
  }

  for (const [source, destination] of [
    ["/home", "/"], ["/principles", "/grundsaetze"], ["/participate", "/mitmachen"],
    ["/structure", "/struktur"], ["/news", "/aktuelles"], ["/elections", "/wahlen"],
    ["/aktuelle-wahlen", "/wahlen"], ["/donate", "/spenden"], ["/technology", "/technologie"],
    ["/roadmap", "/status"], ["/faq", "/hilfe"], ["/kandidieren", "/kandidatur"],
    ["/mitglied-werden", "/mitgliedschaft"],
  ] as const) {
    test(`@front02 redirect ${source}`, async ({ page }) => {
      await page.goto(source);
      expect(new URL(page.url()).pathname).toBe(destination);
    });
  }

  test("@front02 locale preserves route", async ({ page }) => {
    await page.goto("/wahlen?lang=en");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await page.getByRole("link", { name: "DE" }).click();
    expect(new URL(page.url()).pathname).toBe("/wahlen");
    await expect(page.locator("html")).toHaveAttribute("lang", "de");
  });
});

for (const path of [
  "/", "/aktuelles", "/regionen", "/transparenz", "/hilfe", "/suche",
  "/foundation/workspaces/ws-02", "/foundation/workspaces/ws-03",
  "/foundation/workspaces/ws-06", "/foundation/workspaces/ws-10",
  "/foundation/states/denied", "/foundation/states/error", "/foundation/states/recovery",
]) {
  test(`@front02 @a11y ${path}`, async ({ page }) => {
    await page.goto(path);
    const result = await new AxeBuilder({ page }).analyze();
    expect(result.violations.filter(({ impact }) => impact === "serious" || impact === "critical")).toEqual([]);
  });
}

test("@front02 @a11y keyboard focus landmarks language", async ({ page }) => {
  await page.goto("/?lang=en");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Zum Inhalt springen" });
  await expect(skip).toBeFocused();
  await skip.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("header")).toHaveCount(1);
  await expect(page.locator("main")).toHaveCount(1);
  await expect(page.locator("footer")).toHaveCount(1);
  await expect(page.locator("h1")).toHaveCount(1);
  await expect(page.getByRole("group", { name: "Sprache / language" })).toBeVisible();
});
