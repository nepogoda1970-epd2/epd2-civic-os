import { expect, test } from "@playwright/test";

test("production-like profile is fail-closed and cannot fabricate fixture data", async ({ page }) => {
  await page.goto("/member/home");
  await expect(
    page.getByText("Verbindung zur zuständigen Laufzeit nicht verfügbar"),
  ).toBeVisible();
  await expect(
    page.getByText(/Anna Beispiel|ANTRAG-2026-0142|Offene kommunale Daten/),
  ).toHaveCount(0);
  await expect(page.getByText(/Stimme abgeben|Cast ballot/)).toHaveCount(0);
  await expect(page.locator("#scope")).toHaveCount(0);
});

test("production-like applicant route does not fabricate applicant case", async ({ page }) => {
  await page.context().addCookies([
    {
      name: "front03_fixture_principal",
      value: "applicant",
      url: "http://127.0.0.1:3100",
    },
  ]);
  await page.goto("/member/application");
  await expect(
    page.getByText("Verbindung zur zuständigen Laufzeit nicht verfügbar"),
  ).toBeVisible();
  await expect(page.getByText("ANTRAG-2026-0142")).toHaveCount(0);
});
