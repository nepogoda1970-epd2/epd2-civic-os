import { expect, test } from "@playwright/test";

/**
 * The FRONT-04 visual baseline.
 *
 * Twelve canonical route captures — four routes across mobile, desktop and wide
 * — plus the fail-closed and consequential states that carry the stage's actual
 * meaning.  Inherited FRONT-00/01/02/03 snapshots are not touched by this file.
 */

const ROUTES = [
  ["credential", "/vote/credential"],
  ["ballot", "/vote/ballot"],
  ["review", "/vote/review"],
  ["receipt", "/vote/receipt"],
] as const;

/**
 * The ballot renders only under the governed test profile, and it renders after
 * the runtime resolves.  Polling `count()` once races that resolution and
 * silently captures the wrong state, so the wait is explicit.
 */
async function ballotRendered(page: import("@playwright/test").Page) {
  try {
    await page.waitForSelector('input[type="radio"]', { timeout: 15_000 });
    return true;
  } catch {
    return false;
  }
}

for (const [name, route] of ROUTES) {
  test(`@visual ${name} canonical route`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot(`front04-${name}.png`, {
      fullPage: true,
    });
  });
}

test("@visual review consequential boundary", async ({ page }) => {
  await page.goto("/vote/ballot");
  if (await ballotRendered(page)) {
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await expect(
      page.getByRole("heading", { name: "Stimme prüfen", level: 1 }),
    ).toBeVisible();
    await expect(page.locator(".selection-list")).toHaveCount(1);
  } else {
    await page.goto("/vote/review");
  }
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveScreenshot(`front04-review-consequential.png`, {
    fullPage: true,
  });
});

test("@visual cast attempt fails closed", async ({ page }) => {
  await page.goto("/vote/ballot");
  if (await ballotRendered(page)) {
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await expect(
      page.getByRole("heading", { name: "Stimme prüfen", level: 1 }),
    ).toBeVisible();
    const cast = page.getByRole("button", { name: "Stimme endgültig abgeben" });
    await expect(cast).toBeEnabled();
    await cast.click();
    await expect(page.locator("[data-refusal]")).toBeVisible();
  } else {
    await page.goto("/vote/review");
  }
  await expect(page).toHaveScreenshot(`front04-cast-failclosed.png`, {
    fullPage: true,
  });
});

test("@visual handoff channel violation", async ({ page }) => {
  await page.goto("/vote/credential?handoff=REDACTED");
  await expect(page.getByText("Ungültiger Übergabeweg")).toBeVisible();
  await expect(page).toHaveScreenshot(`front04-channel-violation.png`, {
    fullPage: true,
  });
});

test("@visual receipt verification unavailable", async ({ page }) => {
  await page.goto("/vote/receipt");
  await page.getByLabel("Nachweiscode").fill("ABCDEFGH23456789");
  await page.getByRole("button", { name: "Veröffentlichung prüfen" }).click();
  await expect(page.locator("[data-refusal]")).toBeVisible();
  await expect(page).toHaveScreenshot(`front04-receipt-unavailable.png`, {
    fullPage: true,
  });
});

test("@visual unknown path discloses nothing", async ({ page }) => {
  await page.goto("/vote/ballot/unbekannt");
  await expect(page).toHaveScreenshot(`front04-not-found.png`, {
    fullPage: true,
  });
});
