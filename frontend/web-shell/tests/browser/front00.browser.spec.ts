import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const fixtures = [
  ["index", "/foundation/examples/public"],
  ["dashboard", "/foundation/examples/cockpit"],
  ["kommunikation", "/foundation/examples/communication"],
  ["buerger-login", "/foundation/examples/form"],
  ["abstimmungen", "/foundation/examples/table"],
] as const;

for (const [name, path] of fixtures) {
  test(`@visual ${name} matches approved migrated fixture`, async ({
    page,
  }) => {
    await page.goto(path);
    await expect(page).toHaveScreenshot(`${name}.png`, {
      fullPage: true,
      mask: [page.locator(".candidate-banner")],
      maskColor: "#fff8dc",
    });
  });

  test(`@a11y ${name} has no serious or critical axe violations`, async ({
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

  test(`@a11y ${name} has keyboard skip link, headings and landmarks`, async ({
    page,
  }) => {
    await page.goto(path);
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
}

test("@a11y showcase dialog semantics and focus lifecycle", async ({
  page,
}) => {
  await page.goto("/foundation");
  const opener = page.getByRole("button", { name: "Bestätigung öffnen" });
  await opener.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(page.getByRole("button", { name: "Abbrechen" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(opener).toBeFocused();
});

test("@a11y reduced motion is requested by the browser project", async ({
  page,
}) => {
  await page.goto("/foundation");
  expect(
    await page.evaluate(
      () => matchMedia("(prefers-reduced-motion: reduce)").matches,
    ),
  ).toBe(true);
});
