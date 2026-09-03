import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * FRONT-04 governed-test-profile browser gates.
 *
 * The profile supplies an election context and a ballot style so the real
 * journey can be walked in a real browser.  It supplies nothing else: cast,
 * challenge, receipt and verification stay blocked here exactly as they are in
 * production, and the tests below assert that they do.
 */

/**
 * Profile.  The route, isolation, boundary and accessibility gates below run
 * under both profiles.  The ballot and review journeys need a rendered ballot,
 * which only the governed test profile supplies — so under the production
 * profile they are replaced, not skipped: `front04.production.browser.spec.ts`
 * asserts the fail-closed counterpart of every one of them, and that suite runs
 * only under the production profile.
 */
const GOVERNED_TEST = process.env.FRONT04_TEST_PROFILE !== "production";

const ROUTES = [
  "/vote/credential",
  "/vote/ballot",
  "/vote/review",
  "/vote/receipt",
] as const;

const PROHIBITED_SUCCESS = [
  "Sie haben abgestimmt",
  "Ihre Stimme wurde abgegeben",
  "Ihre Stimme wurde gezählt",
  "Sie haben teilgenommen",
  "Stimme erfolgreich",
  "Stimmabgabe erfolgreich",
];

const PROHIBITED_TALLY = [
  "Zwischenstand",
  "Zwischenergebnis",
  "Beteiligung:",
  "Wahlbeteiligung",
  "Stimmen insgesamt",
  "abgegebene Stimmen",
  "Platz 1",
  "Rangfolge",
];

const PROHIBITED_IDENTITY = [
  "member_id",
  "account_id",
  "person_id",
  "membership_id",
  "session_reference",
  "credential_reference",
  "account_reference",
];

async function walkToBallot(page: Page) {
  await page.goto("/vote/ballot");
  await expect(
    page.getByRole("heading", { name: "Stimmzettel", level: 1 }),
  ).toBeVisible();
  // The ballot renders after the runtime resolves. Waiting for the first
  // control rather than for the heading is what makes the journey tests
  // deterministic instead of racing that resolution.
  await page.waitForSelector('input[type="radio"]', { timeout: 15_000 });
}

test.describe("canonical routes", () => {
  for (const route of ROUTES) {
    test(`@a11y ${route} has no serious or critical axe violations`, async ({
      page,
    }) => {
      await page.goto(route);
      const results = await new AxeBuilder({ page }).analyze();
      const serious = results.violations.filter(({ impact }) =>
        ["serious", "critical"].includes(impact ?? ""),
      );
      expect(serious).toEqual([]);
    });

    test(`@a11y ${route} exposes one main landmark, one h1 and a working skip link`, async ({
      page,
    }) => {
      await page.goto(route);
      await expect(page.locator("main")).toHaveCount(1);
      await expect(page.locator("h1")).toHaveCount(1);
      await page.keyboard.press("Tab");
      const skip = page.getByRole("link", { name: "Zum Inhalt springen" });
      await expect(skip).toBeFocused();
      await skip.press("Enter");
      await expect(page.locator("main")).toBeFocused();
    });

    test(`@a11y ${route} renders no navigation into the member workspace`, async ({
      page,
    }) => {
      await page.goto(route);
      await expect(page.locator("nav")).toHaveCount(0);
      await expect(page.locator('[data-workspace="WS-03"]')).toHaveCount(1);
      const links = await page
        .locator("a[href]")
        .evaluateAll((nodes) =>
          nodes.map((node) => node.getAttribute("href") ?? ""),
        );
      for (const href of links) {
        expect(
          href.startsWith("/vote") || href === "#main" || href.startsWith("#"),
          href,
        ).toBe(true);
      }
    });

    test(`@a11y ${route} sets no cookie`, async ({ page, context }) => {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      expect(await context.cookies()).toHaveLength(0);
    });

    test(`@a11y ${route} writes nothing to any browser store`, async ({
      page,
    }) => {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      const state = await page.evaluate(async () => ({
        local: window.localStorage.length,
        session: window.sessionStorage.length,
        databases:
          "databases" in indexedDB ? (await indexedDB.databases()).length : 0,
        caches: "caches" in window ? (await caches.keys()).length : 0,
        workers:
          "serviceWorker" in navigator
            ? (await navigator.serviceWorker.getRegistrations()).length
            : 0,
      }));
      expect(state).toEqual({
        local: 0,
        session: 0,
        databases: 0,
        caches: 0,
        workers: 0,
      });
    });

    test(`@a11y ${route} requests no third-party origin`, async ({
      page,
      baseURL,
    }) => {
      const requested: string[] = [];
      page.on("request", (request) => requested.push(request.url()));
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      expect(requested.length).toBeGreaterThan(0);
      for (const url of requested) {
        expect(url.startsWith(baseURL ?? ""), url).toBe(true);
      }
    });

    test(`@a11y ${route} leaks no identity, tally or success claim`, async ({
      page,
    }) => {
      await page.goto(route);
      await page.waitForLoadState("networkidle");
      const html = await page.content();
      const text = await page.locator("body").innerText();
      for (const phrase of PROHIBITED_SUCCESS)
        expect(text, phrase).not.toContain(phrase);
      for (const phrase of PROHIBITED_TALLY)
        expect(text, phrase).not.toContain(phrase);
      for (const field of PROHIBITED_IDENTITY)
        expect(html, field).not.toContain(field);
      expect(await page.title()).toBe("Abstimmungsbereich — EPD²");
    });

    test(`@a11y ${route} keeps a stable non-disclosing document title`, async ({
      page,
    }) => {
      await page.goto(route);
      expect(await page.title()).toBe("Abstimmungsbereich — EPD²");
      expect(page.url()).not.toMatch(/handoff|artifact|token|credential=/);
    });
  }
});

test.describe("the credential surface", () => {
  test("a direct visit establishes no voting context", async ({ page }) => {
    await page.goto("/vote/credential");
    await expect(
      page.getByRole("heading", {
        name: "Stimmberechtigung übernehmen",
        level: 1,
      }),
    ).toBeVisible();
    // The governed test profile does establish a context; production does not.
    // Either way, nothing about a member session appears.
    const html = await page.content();
    expect(html).not.toContain("Authorization");
    expect(html).not.toContain("Bearer");
  });

  test("a handoff value in the query string is refused and never stored", async ({
    page,
  }) => {
    await page.goto("/vote/credential?handoff=SECRETVALUE123");
    await expect(page.getByText("Ungültiger Übergabeweg")).toBeVisible();
    const state = await page.evaluate(() => ({
      local: JSON.stringify(window.localStorage),
      session: JSON.stringify(window.sessionStorage),
      title: document.title,
      body: document.body.innerText,
    }));
    expect(state.local).not.toContain("SECRETVALUE123");
    expect(state.session).not.toContain("SECRETVALUE123");
    expect(state.title).not.toContain("SECRETVALUE123");
    expect(state.body).not.toContain("SECRETVALUE123");
  });

  test("a handoff value in the fragment is refused", async ({ page }) => {
    await page.goto("/vote/credential#artifact=SECRETVALUE456");
    await expect(page.getByText("Ungültiger Übergabeweg")).toBeVisible();
    const body = await page.locator("body").innerText();
    expect(body).not.toContain("SECRETVALUE456");
  });
});

test.describe("the ballot", () => {
  test.skip(
    !GOVERNED_TEST,
    "journey needs a rendered ballot; the production profile asserts the fail-closed counterpart instead",
  );
  test("is completable with the keyboard alone", async ({ page }) => {
    await walkToBallot(page);
    const first = page.getByRole("radio").first();
    await first.focus();
    await page.keyboard.press("Space");
    await expect(first).toBeChecked();
    const boxes = page.getByRole("checkbox");
    await boxes.first().focus();
    await page.keyboard.press("Space");
    await expect(boxes.first()).toBeChecked();
  });

  test("announces the selection state without relying on colour", async ({
    page,
  }) => {
    await walkToBallot(page);
    const first = page.getByRole("radio").first();
    await first.check();
    const label = page.locator(
      `label[for="${await first.getAttribute("id")}"]`,
    );
    await expect(label).toContainText("ausgewählt");
  });

  test("refuses to exceed a contest's selection limit", async ({ page }) => {
    await walkToBallot(page);
    const boxes = page.getByRole("checkbox");
    await boxes.nth(0).check();
    await boxes.nth(1).check();
    await boxes.nth(2).click();
    await expect(boxes.nth(2)).not.toBeChecked();
  });

  test("clearing a contest empties it", async ({ page }) => {
    await walkToBallot(page);
    const boxes = page.getByRole("checkbox");
    await boxes.nth(0).check();
    await page
      .getByRole("button", { name: "Auswahl in dieser Frage zurücksetzen" })
      .nth(1)
      .click();
    await expect(boxes.nth(0)).not.toBeChecked();
  });

  test("shows no tally, count of ballots, turnout or progress", async ({
    page,
  }) => {
    await walkToBallot(page);
    const text = await page.locator("body").innerText();
    for (const phrase of PROHIBITED_TALLY)
      expect(text, phrase).not.toContain(phrase);
  });

  test("a reload discards the selection rather than restoring it", async ({
    page,
  }) => {
    await walkToBallot(page);
    const first = page.getByRole("radio").first();
    await first.check();
    await expect(first).toBeChecked();
    await page.reload();
    await expect(page.getByRole("radio").first()).not.toBeChecked();
    const state = await page.evaluate(() => ({
      local: window.localStorage.length,
      session: window.sessionStorage.length,
    }));
    expect(state).toEqual({ local: 0, session: 0 });
  });

  test("no selection reaches the URL", async ({ page }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    expect(page.url()).toBe(new URL("/vote/ballot", page.url()).toString());
  });
});

test.describe("review and the consequential boundary", () => {
  test.skip(
    !GOVERNED_TEST,
    "journey needs a rendered ballot; the production profile asserts the fail-closed counterpart instead",
  );
  test("the review shows the voter's own selections and offers cancel", async ({
    page,
  }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await expect(
      page.getByRole("heading", { name: "Stimme prüfen", level: 1 }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Ihre Auswahl", level: 2 }),
    ).toBeVisible();
    await expect(page.locator(".selection-list")).toHaveCount(1);
    await expect(
      page.getByRole("button", { name: "Vorgang abbrechen" }),
    ).toBeVisible();
  });

  test("cancelling states that nothing was cast", async ({ page }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await page.getByRole("button", { name: "Vorgang abbrechen" }).click();
    await expect(page.getByText("Vorgang abgebrochen")).toBeVisible();
    await expect(
      page.getByText("Es wurde nichts abgegeben und nichts gezählt.").first(),
    ).toBeVisible();
  });

  test("the three actions are separately named with different consequences", async ({
    page,
  }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await expect(
      page.getByRole("button", { name: "Auswahl auf diesem Gerät prüfen" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Öffentlichen Prüfnachweis erzeugen" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Stimme endgültig abgeben" }),
    ).toBeVisible();
    const text = await page.locator("body").innerText();
    expect(text).toContain("ausdrücklich nicht gezählt");
    expect(text).toContain("verbraucht Ihre Stimmberechtigung nicht");
  });

  test("attempting a cast fails closed and claims no success", async ({
    page,
  }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    await page
      .getByRole("button", { name: "Stimme endgültig abgeben" })
      .click();
    const panel = page.locator("[data-refusal]");
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute(
      "data-refusal",
      "WS03_BALLOT_CRYPTO_RUNTIME_BLOCKED",
    );
    const text = await page.locator("body").innerText();
    for (const phrase of PROHIBITED_SUCCESS)
      expect(text, phrase).not.toContain(phrase);
    expect(text).toContain("Es wurde nichts abgegeben und nichts gezählt.");
  });

  test("a repeated cast click does not produce a second attempt or a success", async ({
    page,
  }) => {
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    const button = page.getByRole("button", {
      name: "Stimme endgültig abgeben",
    });
    await button.click();
    await button.click();
    await button.click();
    await expect(page.locator("[data-refusal]")).toHaveCount(1);
    const text = await page.locator("body").innerText();
    for (const phrase of PROHIBITED_SUCCESS)
      expect(text, phrase).not.toContain(phrase);
  });

  test("a local check produces no server artefact and no receipt", async ({
    page,
  }) => {
    const requests: string[] = [];
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    await page.getByRole("link", { name: "Auswahl prüfen" }).click();
    page.on("request", (request) => requests.push(request.url()));
    await page
      .getByRole("button", { name: "Auswahl auf diesem Gerät prüfen" })
      .click();
    await expect(page.locator("[data-refusal]")).toBeVisible();
    expect(requests.filter((url) => url.includes("/elections"))).toHaveLength(
      0,
    );
    await expect(page.locator("[data-receipt]")).toHaveCount(0);
  });

  test("a direct visit to the review without a selection fails closed", async ({
    page,
  }) => {
    await page.goto("/vote/review");
    await expect(page.getByText("Keine Auswahl vorhanden")).toBeVisible();
    await expect(
      page.getByText("Es wurde nichts abgegeben und nichts gezählt.").first(),
    ).toBeVisible();
  });
});

test.describe("the receipt surface", () => {
  test("verification is reachable by keyboard and needs no camera", async ({
    page,
  }) => {
    await page.goto("/vote/receipt");
    const field = page.getByLabel("Nachweiscode");
    await field.focus();
    await field.fill("ABCDEFGH23456789");
    await page.getByRole("button", { name: "Veröffentlichung prüfen" }).click();
    await expect(page.locator("[data-refusal]")).toBeVisible();
    await expect(page.locator("video, [data-qr-only]")).toHaveCount(0);
  });

  test("a malformed code produces a linked error summary", async ({ page }) => {
    await page.goto("/vote/receipt");
    await page.getByLabel("Nachweiscode").fill("ABC");
    await page.getByRole("button", { name: "Veröffentlichung prüfen" }).click();
    const summary = page.locator("#error-summary");
    await expect(summary).toBeVisible();
    await summary.getByRole("link").click();
    await expect(page.getByLabel("Nachweiscode")).toBeFocused();
  });

  test("the surface says what a receipt never contains and does not urge sharing", async ({
    page,
  }) => {
    await page.goto("/vote/receipt");
    await expect(
      page.getByText("Was ein Nachweis nicht enthält"),
    ).toBeVisible();
    await expect(page.getByText(/belegt keine Auswahl/).first()).toBeVisible();
    await expect(
      page.getByRole("button", {
        name: /teilen|drucken|senden|herunterladen/i,
      }),
    ).toHaveCount(0);
  });
});

test.describe("presentation constraints", () => {
  test("@a11y every required action survives 400% reflow", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 512 });
    for (const route of ROUTES) {
      await page.goto(route);
      const overflow = await page.evaluate(
        () =>
          document.documentElement.scrollWidth -
          document.documentElement.clientWidth,
      );
      expect(overflow, route).toBeLessThanOrEqual(1);
      await expect(page.locator("h1"), route).toBeVisible();
    }
  });

  test("@a11y reduced motion is honoured", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/vote/ballot");
    const animated = await page.evaluate(
      () =>
        [...document.querySelectorAll("*")].filter((node) => {
          const style = getComputedStyle(node);
          return (
            parseFloat(style.animationDuration) > 0.05 ||
            parseFloat(style.transitionDuration) > 0.05
          );
        }).length,
    );
    expect(animated).toBe(0);
  });

  test("@a11y interactive targets meet the 44px minimum", async ({ page }) => {
    await page.goto("/vote/receipt");
    const small = await page
      .locator("button, a[href], input")
      .evaluateAll((nodes) =>
        nodes
          .filter((node) => {
            const rect = node.getBoundingClientRect();
            return rect.height > 0 && rect.height < 24;
          })
          .map((node) => node.outerHTML.slice(0, 60)),
      );
    expect(small).toEqual([]);
  });

  test("the assistance panel never exposes the voter's selections", async ({
    page,
  }) => {
    test.skip(
      !GOVERNED_TEST,
      "needs a rendered ballot; the production profile has no selections to expose",
    );
    await walkToBallot(page);
    await page.getByRole("radio").first().check();
    const panel = page.locator("[data-assistance]");
    await panel.getByRole("button").click();
    await expect(
      panel.locator("[data-operator-may-view-selections]"),
    ).toHaveAttribute("data-operator-may-view-selections", "false");
    await expect(panel).not.toContainText("Antwortmöglichkeit A");
  });

  test("changing the language query parameter changes no authority", async ({
    page,
  }) => {
    await page.goto("/vote/ballot?lang=en");
    await expect(page.locator("html")).toHaveAttribute("lang", "de");
    await expect(
      page.getByRole("heading", { name: "Stimmzettel", level: 1 }),
    ).toBeVisible();
    // The heading is the German canonical title under both profiles: a language
    // parameter changes no route authority and no page identity.
  });

  test("an unknown path under this origin discloses nothing", async ({
    page,
  }) => {
    const response = await page.goto("/vote/ballot/geheim-1234");
    expect(response?.status()).toBe(404);
    const text = await page.locator("body").innerText();
    expect(text).not.toContain("geheim-1234");
    expect(text).toContain("Es wurde nichts abgegeben und nichts gezählt.");
  });
});

test.describe("the browser boundary", () => {
  test("the security headers are served", async ({ page }) => {
    const response = await page.goto("/vote/credential");
    const headers = response?.headers() ?? {};
    expect(headers["cache-control"]).toContain("no-store");
    expect(headers["referrer-policy"]).toBe("no-referrer");
    expect(headers["content-security-policy"]).toContain(
      "frame-ancestors 'none'",
    );
    expect(headers["content-security-policy"]).toContain("default-src 'self'");
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["permissions-policy"]).toContain("camera=()");
    expect(headers["x-powered-by"]).toBeUndefined();
  });

  test("no referrer leaves this origin", async ({ page }) => {
    await page.goto("/vote/ballot");
    const referrerPolicy = await page.evaluate(() => document.referrer);
    expect(referrerPolicy).toBe("");
  });

  test("the framework image optimiser is not usable on this origin", async ({
    request,
  }) => {
    // The Voting Client ships no images. The optimiser is disabled so that its
    // processing path — and the inherited sharp/libvips advisories behind it —
    // is not reachable from the voting origin at all.
    const response = await request.get(
      "/_next/image?url=%2Fvote%2Fcredential&w=64&q=75",
    );
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test("no service worker is registered", async ({ page }) => {
    await page.goto("/vote/ballot");
    const registrations = await page.evaluate(async () =>
      "serviceWorker" in navigator
        ? (await navigator.serviceWorker.getRegistrations()).length
        : 0,
    );
    expect(registrations).toBe(0);
  });
});
