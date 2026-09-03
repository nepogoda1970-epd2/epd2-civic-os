import { expect, test, type Page } from "@playwright/test";

/**
 * The FRONT-05 visual baseline.
 *
 * The shots are taken under the governed test profile, because a screenshot of
 * a surface that renders nothing proves nothing about the surface. Each state
 * below is one an operator can actually reach.
 */

const GOVERNED_TEST = process.env.FRONT05_TEST_PROFILE !== "production";

test.describe("@visual", () => {
  test.skip(
    !GOVERNED_TEST,
    "the baseline is captured under the governed profile",
  );

  async function shoot(page: Page, route: string, name: string) {
    await page.goto(route);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.waitForTimeout(500);
    await expect(page).toHaveScreenshot(`front05-${name}.png`, {
      fullPage: true,
    });
  }

  test("home", async ({ page }) => {
    await shoot(page, "/representative", "home");
  });

  test("desk", async ({ page }) => {
    await shoot(page, "/representative/desk", "desk");
  });

  test("case detail", async ({ page }) => {
    await shoot(
      page,
      "/representative/desk/PROTOTYP-VORGANG-0001",
      "case-detail",
    );
  });

  test("case refused", async ({ page }) => {
    await shoot(page, "/representative/desk/UNBEKANNT-0001", "case-refused");
  });

  test("positions", async ({ page }) => {
    await shoot(page, "/representative/positions", "positions");
  });

  test("deviations", async ({ page }) => {
    await shoot(page, "/representative/deviations", "deviations");
  });

  test("declarations", async ({ page }) => {
    await shoot(page, "/representative/declarations", "declarations");
  });

  test("declaration blocked", async ({ page }) => {
    await page.goto("/representative/declarations");
    await page.fill("#declaration-subject", "Prototyp-Gegenstand");
    await page.fill("#declaration-date", "2026-01-15");
    await page.fill("#declaration-counterparty", "Prototyp-Gegenüber");
    await page.getByRole("button", { name: "Erklärung übermitteln" }).click();
    await expect(page.locator("[data-obligation-open]")).toBeVisible();
    await expect(page).toHaveScreenshot("front05-declaration-blocked.png", {
      fullPage: true,
    });
  });

  test("publication", async ({ page }) => {
    await shoot(page, "/representative/publication", "publication");
  });

  test("conflicts", async ({ page }) => {
    await shoot(page, "/representative/conflicts", "conflicts");
  });

  test("not found", async ({ page }) => {
    await page.goto("/representative/gibt-es-nicht");
    await expect(page).toHaveScreenshot("front05-not-found.png", {
      fullPage: true,
    });
  });
});
