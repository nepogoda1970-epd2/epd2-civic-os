import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const visualPages = [
  ["homepage", "/"],
  ["about-goals", "/ziele"],
  ["open-program", "/programm/struktur"],
  ["program-detail", "/programm/status"],
  ["initiative-lifecycle", "/initiativen"],
  ["voting-explanation", "/abstimmungen"],
  ["transparency-model", "/transparenz"],
  ["technology-security", "/sicherheit"],
  ["participation", "/mitmachen"],
  ["roadmap-status", "/status"],
] as const;

for (const [name, path] of visualPages) {
  test(`@front01-visual ${name} matches reviewed public baseline`, async ({
    page,
  }) => {
    await page.goto(path);
    await expect(page).toHaveScreenshot(`front01-${name}.png`, {
      fullPage: true,
      mask: [page.locator(".candidate-banner")],
      maskColor: "#fff8dc",
    });
  });
}

for (const path of [
  "/",
  "/programm/struktur",
  "/initiativen",
  "/abstimmungen",
  "/transparenz",
  "/status",
]) {
  test(`@front01-a11y ${path} has no serious or critical axe violations`, async ({
    page,
  }) => {
    await page.goto(path);
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter(({ impact }) =>
        ["serious", "critical"].includes(impact ?? ""),
      ),
    ).toEqual([]);
  });
}

test("@front01-a11y public shell supports keyboard and semantic landmarks", async ({
  page,
}) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Zum Inhalt springen" });
  await expect(skip).toBeFocused();
  await skip.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await expect(page.locator("h1")).toHaveCount(1);
  await expect(page.locator("header")).toHaveCount(1);
  await expect(page.locator("main")).toHaveCount(1);
  await expect(page.locator("footer")).toHaveCount(1);
});

test("all FRONT-01 internal links resolve without error", async ({
  page,
  request,
}) => {
  await page.goto("/");
  const hrefs = await page
    .locator('a[href^="/"]')
    .evaluateAll((links) => [
      ...new Set(
        links.map((link) => link.getAttribute("href")).filter(Boolean),
      ),
    ]);
  for (const href of hrefs) {
    const response = await request.get(href!);
    expect(response.status(), href!).toBeLessThan(400);
  }
});

test("voting and finance pages expose no mutation forms", async ({ page }) => {
  for (const path of ["/abstimmungen", "/finanzen", "/buergerbuero"]) {
    await page.goto(path);
    await expect(page.locator("form")).toHaveCount(0);
    await expect(
      page.locator('[data-workspace="WS-01"]').first(),
    ).toBeVisible();
  }
});
