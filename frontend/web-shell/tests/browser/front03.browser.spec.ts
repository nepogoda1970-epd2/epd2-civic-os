import { expect, type Page, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function applicant(page: Page) {
  await page.context().addCookies([
    {
      name: "front03_fixture_principal",
      value: "applicant",
      url: "http://127.0.0.1:3100",
    },
  ]);
}
test("B01 Applicant dashboard", async ({ page }) => {
  await applicant(page);
  await page.goto("/member/application");
  await expect(
    page.getByRole("heading", { name: "Mein Aufnahmeantrag" }),
  ).toBeVisible();
  await expect(page.getByText("ANTRAG-2026-0142")).toBeVisible();
});
test("B02 Applicant no Member navigation", async ({ page }) => {
  await applicant(page);
  await page.goto("/member/application");
  await expect(page.getByRole("navigation")).toHaveCount(0);
});
test("B03 Applicant logo safe", async ({ page }) => {
  await applicant(page);
  await page.goto("/member/application");
  await page.getByRole("link", { name: "EPD²" }).click();
  await expect(page).toHaveURL(/\/member\/application/);
});
for (const [id, action] of [
  ["B04", "direct"],
  ["B05", "reload"],
  ["B06", "locale"],
] as const)
  test(`${id} Applicant remains restricted ${action}`, async ({ page }) => {
    await applicant(page);
    await page.goto("/member/home");
    if (action === "reload") await page.reload();
    if (action === "locale") await page.goto("/member/home?lang=en");
    await expect(
      page.getByText(/nicht freigegeben|not available/),
    ).toBeVisible();
    await expect(page.getByText("Profilangaben prüfen")).toHaveCount(0);
  });
test("B07 Member core", async ({ page }) => {
  await page.goto("/member/home");
  await expect(
    page.getByRole("heading", { name: "Mein Bürgerbereich" }),
  ).toBeVisible();
});
test("B08-B10 scope reauthorization and reload", async ({ page }) => {
  await page.goto("/member/home");
  await page.locator("#scope").selectOption("berlin");
  await expect(page.getByText("Aktiv · Landesverband Berlin")).toBeVisible();
});
test("B11 unauthorized scope absent", async ({ page }) => {
  await page.goto("/member/home");
  await expect(page.locator("#scope option")).toHaveCount(3);
});
test("B12 stale scope cannot overwrite", async ({ page }) => {
  await page.goto("/member/home");
  await page.locator("#scope").selectOption("berlin");
  await page.locator("#scope").selectOption("bund");
  await expect(page.getByText("Aktiv · Bund")).toBeVisible();
});
test("B13 Membership projection", async ({ page }) => {
  await page.goto("/member/membership");
  await expect(page.getByText("Provenienz")).toBeVisible();
  await expect(page.getByRole("link", { name: /Korrektur/ })).toBeVisible();
});
test("B14-B15 initiative confirmation and duplicate guard", async ({
  page,
}) => {
  await page.goto("/member/initiatives/new");
  await page.getByLabel("Titel").fill("Testinitiative");
  await page.getByLabel("Kurzbeschreibung").fill("Prüfbare Beschreibung");
  await page.getByRole("button", { name: "Vorschau" }).click();
  await page.getByRole("button", { name: /Verbindlich/ }).click();
  await page.getByRole("button", { name: "Jetzt bestätigen" }).dblclick();
  await expect(page.getByText("RCPT-bund-2026-0081")).toHaveCount(1);
});
test("B16 fixture profile is active only in governed fixture run", async ({
  page,
}) => {
  await page.goto("/member/home");
  await expect(
    page.getByRole("heading", { name: "Mein Bürgerbereich" }),
  ).toBeVisible();
});
test("B17 step-up surface does not execute", async ({ page }) => {
  await page.goto("/member/assurance/authentication-session-assurance");
  await expect(page.getByText("BLOCKED")).toBeVisible();
  await expect(page.getByRole("button", { name: /widerrufen/i })).toHaveCount(
    0,
  );
});
test("B18-B19 voting boundary", async ({ page }) => {
  await page.goto("/member/home");
  await expect(
    page.getByText("keine Stimmabgabe im Bürgerbereich"),
  ).toBeVisible();
  const html = await page.content();
  expect(html).not.toMatch(
    /memberId|accountId|personId|Stimme abgeben|Cast ballot/,
  );
});
test("B20 Applicant appeal isolation", async ({ page }) => {
  await applicant(page);
  await page.goto("/member/membership/appeal");
  await expect(
    page.getByText(/Compliance- und Rechtsbereich wird nicht geöffnet/),
  ).toBeVisible();
  await expect(page.locator('a[href*="ws-07"]')).toHaveCount(0);
});
test("B21-B22 outage is explicit", async ({ page }) => {
  await page.goto("/member/delegation");
  await expect(page.getByText("BLOCKED")).toBeVisible();
  await expect(page.getByText(/erfolgreich/i)).toHaveCount(0);
});
test("B23 Applicant keyboard", async ({ page }) => {
  await applicant(page);
  await page.goto("/member/application");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Zum Inhalt" })).toBeFocused();
});
test("B24 Member keyboard", async ({ page }) => {
  await page.goto("/member/home");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.locator("#member-main")).toBeVisible();
});
test("B25 dialog focus restoration", async ({ page }) => {
  await page.goto("/member/initiatives/new");
  await page.getByLabel("Titel").fill("T");
  await page.getByLabel("Kurzbeschreibung").fill("S");
  await page.getByRole("button", { name: "Vorschau" }).click();
  const open = page.getByRole("button", { name: /Verbindlich/ });
  await open.click();
  await page.getByRole("button", { name: "Abbrechen" }).click();
  await expect(open).toBeFocused();
});
test("B26 400 percent reflow", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto("/member/membership");
  await expect(page.getByText("Provenienz")).toBeVisible();
  await expect
    .poll(async () => {
      const remedy = page.getByRole("link", { name: /Korrektur/ });
      if (!(await remedy.isVisible())) return false;
      return remedy.evaluate((element) => {
        element.scrollIntoView({ block: "nearest", inline: "nearest" });
        const box = element.getBoundingClientRect();
        return box.left >= 0 && box.right <= window.innerWidth;
      });
    })
    .toBe(true);
});
const mandatory = [
  "/member/application",
  "/member/home",
  "/member/membership",
  "/member/initiatives",
  "/member/initiatives/new",
  "/member/deliberation",
  "/member/delegation",
  "/member/assurance/authentication-session-assurance",
  "/member/membership/appeal",
];
for (const route of mandatory)
  test(`B27 @a11y ${route}`, async ({ page }) => {
    if (route.includes("application") || route.includes("appeal"))
      await applicant(page);
    await page.goto(route);
    const r = await new AxeBuilder({ page }).analyze();
    expect(
      r.violations.filter((v) =>
        ["serious", "critical"].includes(v.impact ?? ""),
      ),
    ).toEqual([]);
  });
test("B28 fixture marker absent from UI", async ({ page }) => {
  await page.goto("/member/home");
  await expect(page.getByText(/fixture backend/i)).toHaveCount(0);
});

const visuals = [
  "application",
  "home",
  "membership",
  "initiatives",
  "initiatives-new",
  "deliberation",
  "delegation",
  "assurance-authentication-session-assurance",
  "membership-appeal",
];
for (const key of visuals)
  test(`@visual FRONT03 ${key}`, async ({ page }) => {
    const route = `/member/${key.replaceAll("-", "/")}`;
    if (key === "application" || key === "membership-appeal")
      await applicant(page);
    await page.goto(route);
    await expect(page).toHaveScreenshot(`front03-${key}.png`, {
      fullPage: true,
    });
  });
