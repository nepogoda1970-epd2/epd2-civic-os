import { expect, test } from "@playwright/test";

/**
 * FRONT-05 production-profile browser gates.
 *
 * This suite runs only under the production profile and asserts the fail-closed
 * counterpart of every journey the governed profile walks. The governed suite
 * shows that the interface works; this one shows that the shipped build has no
 * fixture in it and refuses everything, so a passing governed suite can never
 * be mistaken for evidence that the product functions.
 */

const PRODUCTION = process.env.FRONT05_TEST_PROFILE === "production";

test.describe("production profile", () => {
  test.skip(!PRODUCTION, "asserts the production build only");

  test("the fixture marker is absent from every served script", async ({
    page,
    request,
  }) => {
    const scripts: string[] = [];
    page.on("response", (response) => {
      if (response.url().includes("/_next/static/chunks/")) {
        scripts.push(response.url());
      }
    });
    await page.goto("/representative/desk");
    await page.waitForLoadState("networkidle");
    expect(scripts.length).toBeGreaterThan(3);
    for (const url of scripts) {
      const body = await (await request.get(url)).text();
      expect(body, url).not.toContain(
        "EPD2_FRONT05_GOVERNED_TEST_FIXTURE_MARKER",
      );
      expect(body, url).not.toContain("PROTOTYP-VORGANG");
      expect(body, url).not.toContain("PROTOTYP-MANDAT");
    }
  });

  test("no case queue is rendered and no empty list is claimed", async ({
    page,
  }) => {
    await page.goto("/representative/desk");
    await expect(page.locator("[data-case-queue]")).toHaveCount(0);
    await expect(page.locator("[data-dependency-panel]").first()).toBeVisible();
    // The dependency, not a vague error, is what the operator is shown.
    await expect(page.locator("[data-dependency-panel]").first()).toContainText(
      "accepted executable route",
    );
  });

  test("no mandate is resolved, and the interface says so", async ({
    page,
  }) => {
    await page.goto("/representative");
    await expect(page.locator("[data-mandate-label]")).toContainText(
      "Kein Mandat aufgelöst",
    );
    await expect(page.locator("[data-authority-state]")).toContainText(
      "Befugnis nicht aktiv",
    );
  });

  test("a case detail refuses without disclosing existence", async ({
    page,
  }) => {
    // Each page is read only once its outcome has resolved. Comparing a
    // resolved page against one still resolving fails for a reason that has
    // nothing to do with disclosure — and, worse, could pass by accident if
    // both happened to be caught mid-flight.
    const read = async (caseId: string) => {
      await page.goto(`/representative/desk/${caseId}`);
      await page.waitForSelector("[data-refusal]", { timeout: 15_000 });
      await expect(page.locator("[data-case-resolving]")).toHaveCount(0);
      return page.locator("main").innerText();
    };
    const first = await read("IRGENDEIN-VORGANG-0001");
    const second = await read("EIN-ANDERER-VORGANG-9999");
    expect(first).toBe(second);
  });

  test("every consequential action is refused with nothing committed", async ({
    page,
  }) => {
    await page.goto("/representative/positions");
    await page.fill("#position-body", "Text");
    await page.getByRole("button", { name: "Entwurf speichern" }).click();
    const panel = page.locator("[data-refusal]").first();
    await expect(panel).toBeVisible();
    await expect(panel).toContainText("Es wurde nichts geändert");
  });

  test("the conflict register is unreadable, so access stays restricted", async ({
    page,
  }) => {
    await page.goto("/representative/conflicts");
    await expect(page.locator("[data-any-restriction-active]")).toHaveAttribute(
      "data-any-restriction-active",
      "true",
    );
    await expect(page.locator("[data-restriction-list]")).toHaveCount(0);
  });

  test("the capability summary reports no executable network capability", async ({
    page,
  }) => {
    await page.goto("/representative");
    await expect(page.locator("[data-capability-summary]")).toContainText(
      "gesperrt",
    );
  });

  test("the workspace still hydrates under the production CSP", async ({
    page,
  }) => {
    // A blocked bootstrap script would leave inert markup that still looks
    // complete, so hydration is asserted directly rather than assumed.
    const violations: string[] = [];
    page.on("console", (message) => {
      if (message.text().includes("Content Security Policy")) {
        violations.push(message.text());
      }
    });
    await page.goto("/representative/desk");
    await page.waitForSelector("[data-dependency-panel]", { timeout: 15_000 });
    expect(violations).toEqual([]);
  });
});
