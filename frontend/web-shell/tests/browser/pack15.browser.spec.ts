import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const PROHIBITED_PHRASES = [
  "Sie haben abgestimmt",
  "Ihre Stimme wurde abgegeben",
  "Sie haben teilgenommen",
  "Ihre Stimme wurde gezählt",
  "Stimme erfolgreich",
];

for (const path of ["/mitwirkung/abstimmungen", "/vote"]) {
  test(`@a11y ${path} has no serious or critical axe violations`, async ({
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

test("@a11y voting origin exposes one main landmark and a skip link", async ({
  page,
}) => {
  await page.goto("/vote");
  await expect(page.locator("main")).toHaveCount(1);
  await expect(page.locator("h1")).toHaveCount(1);
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Zum Inhalt springen" });
  await expect(skip).toBeFocused();
  await skip.press("Enter");
  await expect(page.locator("main")).toBeFocused();
});

test("@a11y voting origin renders no navigation into the member area", async ({
  page,
}) => {
  await page.goto("/vote");
  await expect(page.locator("nav")).toHaveCount(0);
  await expect(page.locator('[data-workspace="WS-03"]')).toHaveCount(1);
});

test("@a11y voting origin sets no cookies", async ({ context, page }) => {
  await page.goto("/vote");
  await page.waitForLoadState("networkidle");
  expect((await context.cookies()).length).toBe(0);
});

test("@a11y voting origin writes nothing to browser storage", async ({
  page,
}) => {
  await page.goto("/vote");
  await page.waitForLoadState("networkidle");
  const empty = await page.evaluate(
    () =>
      window.localStorage.length === 0 && window.sessionStorage.length === 0,
  );
  expect(empty).toBe(true);
});

test("@a11y voting origin requests no third-party origin", async ({
  baseURL,
  page,
}) => {
  const origin = baseURL ?? "";
  const requested: string[] = [];
  page.on("request", (request) => {
    requested.push(request.url());
  });
  await page.goto("/vote");
  await page.waitForLoadState("networkidle");
  expect(requested.length).toBeGreaterThan(0);
  for (const url of requested) {
    expect(url.startsWith(origin), url).toBe(true);
  }
});

test("@a11y voting origin reports no participation or casting status", async ({
  page,
}) => {
  await page.goto("/vote");
  const text = await page.locator("body").innerText();
  for (const phrase of PROHIBITED_PHRASES) {
    expect(text, phrase).not.toContain(phrase);
  }
});

test("@a11y participation surface renders no access value or ballot status", async ({
  page,
}) => {
  await page.goto("/mitwirkung/abstimmungen");
  const text = await page.locator("body").innerText();
  for (const phrase of PROHIBITED_PHRASES) {
    expect(text, phrase).not.toContain(phrase);
  }
  await expect(
    page.locator('[data-participation-state="access_available"]'),
  ).toHaveCount(1);
  await expect(page.getByRole("link", { name: "Fortfahren" })).toHaveAttribute(
    "href",
    "/vote",
  );
});
