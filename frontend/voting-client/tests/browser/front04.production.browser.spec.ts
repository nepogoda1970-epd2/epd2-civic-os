import { expect, test } from "@playwright/test";

/**
 * Production-profile gates.
 *
 * These run against the build a deployment would ship.  Their whole subject is
 * what the client does when nothing is available: it must fail closed, say so
 * honestly, and never fabricate an election, a ballot, a receipt or a cast.
 *
 * The suite is skipped unless FRONT04_TEST_PROFILE=production, because the
 * governed test profile deliberately supplies presentation material that these
 * assertions would see.
 */
const PRODUCTION = process.env.FRONT04_TEST_PROFILE === "production";

test.describe("production fail-closed composition", () => {
  test.skip(!PRODUCTION, "runs only against the production profile");

  test("the credential surface establishes no voting context", async ({
    page,
  }) => {
    await page.goto("/vote/credential");
    await expect(page.locator("[data-refusal]")).toBeVisible();
    await expect(page.locator("[data-refusal]")).toHaveAttribute(
      "data-refusal",
      "WS03_HANDOFF_CHANNEL_NOT_ACCEPTED",
    );
    await expect(page.locator("[data-voting-context-established]")).toHaveCount(
      0,
    );
  });

  test("no fake election and no fake ballot is rendered", async ({ page }) => {
    await page.goto("/vote/ballot");
    await expect(page.locator("[data-refusal]")).toBeVisible();
    await expect(page.getByRole("radio")).toHaveCount(0);
    await expect(page.getByRole("checkbox")).toHaveCount(0);
    const text = await page.locator("body").innerText();
    expect(text).not.toContain("Beispielabstimmung");
    expect(text).not.toContain("Antwortmöglichkeit");
    expect(text).not.toContain("PROTOTYP-STIMMZETTEL");
  });

  test("the review offers no selections and no successful cast", async ({
    page,
  }) => {
    await page.goto("/vote/review");
    await expect(page.getByText("Keine Auswahl vorhanden")).toBeVisible();
    for (const phrase of [
      "Sie haben abgestimmt",
      "Ihre Stimme wurde abgegeben",
      "Stimme erfolgreich",
    ]) {
      expect(await page.locator("body").innerText()).not.toContain(phrase);
    }
  });

  test("no fake receipt is produced for any code", async ({ page }) => {
    await page.goto("/vote/receipt");
    await page.getByLabel("Nachweiscode").fill("ABCDEFGH23456789");
    await page.getByRole("button", { name: "Veröffentlichung prüfen" }).click();
    await expect(page.locator("[data-refusal]")).toBeVisible();
    await expect(page.locator("[data-receipt]")).toHaveCount(0);
  });

  test("the fixture marker is absent from every served script", async ({
    page,
    baseURL,
  }) => {
    const scripts: string[] = [];
    page.on("response", async (response) => {
      if (
        response.url().endsWith(".js") &&
        response.url().startsWith(baseURL ?? "")
      ) {
        scripts.push(await response.text().catch(() => ""));
      }
    });
    for (const route of [
      "/vote/credential",
      "/vote/ballot",
      "/vote/review",
      "/vote/receipt",
    ]) {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
    }
    expect(scripts.length).toBeGreaterThan(0);
    for (const body of scripts) {
      expect(body).not.toContain("EPD2_FRONT04_GOVERNED_TEST_FIXTURE_MARKER");
      expect(body).not.toContain("PROTOTYP-STIMMZETTEL-0001");
      expect(body).not.toContain("Antwortmöglichkeit A");
    }
  });

  test("every surface still answers the four questions on failure", async ({
    page,
  }) => {
    for (const route of ["/vote/credential", "/vote/ballot"]) {
      await page.goto(route);
      const panel = page.locator("[data-refusal]").first();
      await expect(panel).toBeVisible();
      await expect(panel).toContainText("Stand der Abgabe");
      await expect(panel).toContainText("Stimmberechtigung");
      await expect(panel).toContainText("Nächster sicherer Schritt");
    }
  });

  test("the governed fallback is reachable from every failure state", async ({
    page,
  }) => {
    for (const route of [
      "/vote/credential",
      "/vote/ballot",
      "/vote/review",
      "/vote/receipt",
    ]) {
      await page.goto(route);
      await expect(
        page.getByRole("heading", { name: "Ersatzweg" }).first(),
      ).toBeVisible();
    }
  });

  test("browser storage stays empty across the whole journey", async ({
    page,
  }) => {
    for (const route of [
      "/vote/credential",
      "/vote/ballot",
      "/vote/review",
      "/vote/receipt",
    ]) {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      const state = await page.evaluate(async () => ({
        local: window.localStorage.length,
        session: window.sessionStorage.length,
        databases:
          "databases" in indexedDB ? (await indexedDB.databases()).length : 0,
        caches: "caches" in window ? (await caches.keys()).length : 0,
      }));
      expect(state, route).toEqual({
        local: 0,
        session: 0,
        databases: 0,
        caches: 0,
      });
    }
  });
});
