import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * FRONT-05 governed-test-profile browser gates.
 *
 * The profile supplies prototype desk material so the real operator journey can
 * be walked in a real browser. It supplies nothing else: every mutation —
 * a case transition, a saved draft, a submitted declaration, a publication
 * proposal, a conflict change — stays blocked here exactly as in production,
 * and the tests below assert that they do.
 */

const GOVERNED_TEST = process.env.FRONT05_TEST_PROFILE !== "production";

const ROUTES = [
  "/representative",
  "/representative/desk",
  "/representative/positions",
  "/representative/deviations",
  "/representative/declarations",
  "/representative/publication",
  "/representative/conflicts",
] as const;

/**
 * Phrases that would assert an accomplished act. None may appear anywhere.
 */
const PROHIBITED_SUCCESS = [
  "wurde übermittelt",
  "erfolgreich übermittelt",
  "wurde veröffentlicht",
  "erfolgreich veröffentlicht",
  "wurde freigegeben",
  "Freigabe erteilt",
  "wurde gespeichert",
  "erfolgreich gespeichert",
  "Meldepflicht erfüllt",
  "Vorgang abgeschlossen",
];

/** Vocabulary that would indicate a universal or cross-mandate mode. */
const PROHIBITED_UNIVERSAL = [
  "super_admin",
  "representative_all",
  "Alle Mandate",
  "Mandat wechseln",
  "Systemverwaltung",
  "Administrationsbereich",
  "cross_mandate",
];

/** Identifiers that must never reach this origin's DOM. */
const PROHIBITED_IDENTITY = [
  "member_id",
  "account_id",
  "person_id",
  "membership_id",
  "citizen_id",
  "voting_token",
  "ballot_id",
];

async function open(page: Page, route: string) {
  await page.goto(route);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
}

/* ------------------------------------------------------------- accessibility */

test.describe("canonical routes", () => {
  for (const route of ROUTES) {
    test(`@a11y ${route} has no serious or critical axe violations`, async ({
      page,
    }) => {
      await open(page, route);
      const results = await new AxeBuilder({ page }).analyze();
      const serious = results.violations.filter(({ impact }) =>
        ["serious", "critical"].includes(impact ?? ""),
      );
      expect(
        serious.map((v) => `${v.id}: ${v.help}`),
        JSON.stringify(serious, null, 1),
      ).toEqual([]);
    });

    test(`${route} renders exactly one level-one heading`, async ({ page }) => {
      await open(page, route);
      await expect(page.locator("h1")).toHaveCount(1);
    });

    test(`${route} carries the non-activation notice`, async ({ page }) => {
      await open(page, route);
      await expect(page.locator(".candidate-banner")).toContainText(
        "rechtlich nicht aktiviert",
      );
    });

    test(`${route} offers a working skip link`, async ({ page }) => {
      await open(page, route);
      await page.keyboard.press("Tab");
      const focused = page.locator(":focus");
      await expect(focused).toHaveText("Zum Inhalt springen");
      await focused.press("Enter");
      await expect(page.locator("main:focus")).toBeVisible();
    });
  }
});

/* ------------------------------------------------------------- prohibitions */

test.describe("prohibited content", () => {
  for (const route of ROUTES) {
    test(`${route} asserts no accomplished act`, async ({ page }) => {
      await open(page, route);
      const body = (await page.locator("body").innerText()).toLowerCase();
      for (const phrase of PROHIBITED_SUCCESS) {
        expect(body, `${route} contains "${phrase}"`).not.toContain(
          phrase.toLowerCase(),
        );
      }
    });

    test(`${route} offers no universal or cross-mandate mode`, async ({
      page,
    }) => {
      await open(page, route);
      const html = await page.content();
      for (const phrase of PROHIBITED_UNIVERSAL) {
        expect(html, `${route} contains "${phrase}"`).not.toContain(phrase);
      }
    });

    test(`${route} exposes no person or voting identifier`, async ({
      page,
    }) => {
      await open(page, route);
      const html = await page.content();
      for (const name of PROHIBITED_IDENTITY) {
        expect(html, `${route} contains "${name}"`).not.toContain(name);
      }
    });

    test(`${route} offers no unscoped search field`, async ({ page }) => {
      await open(page, route);
      await expect(page.locator('input[type="search"]')).toHaveCount(0);
      await expect(page.locator('[role="search"]')).toHaveCount(0);
    });
  }
});

/* ----------------------------------------------------------- browser storage */

test.describe("storage boundary", () => {
  for (const route of ROUTES) {
    test(`${route} writes nothing to a browser store`, async ({ page }) => {
      await open(page, route);
      const state = await page.evaluate(() => ({
        local: Object.keys(window.localStorage),
        session: Object.keys(window.sessionStorage),
        cookie: document.cookie,
        workers: "serviceWorker" in navigator,
      }));
      expect(state.local).toEqual([]);
      expect(state.session).toEqual([]);
      expect(state.cookie).toBe("");
    });
  }

  test("no service worker is registered", async ({ page }) => {
    await open(page, "/representative/desk");
    const registrations = await page.evaluate(async () => {
      if (!("serviceWorker" in navigator)) return 0;
      const list = await navigator.serviceWorker.getRegistrations();
      return list.length;
    });
    expect(registrations).toBe(0);
  });

  test("a case body typed into a draft never reaches a store", async ({
    page,
  }) => {
    await open(page, "/representative/positions");
    const secret = "VERTRAULICHER-ENTWURFSTEXT-4711";
    await page.fill("#position-body", secret);
    await page.getByRole("button", { name: "Entwurf speichern" }).click();
    // Which refusal arrives depends on the profile — under production the scope
    // is never resolved, so the request is refused before the save port is even
    // reached. Both are refusals that committed nothing, and that is what the
    // storage boundary depends on.
    const saveRefusal = page
      .locator('[aria-labelledby="position-draft"] [data-refusal]')
      .first();
    await expect(saveRefusal).toBeVisible();
    await expect(saveRefusal).toContainText("Es wurde nichts geändert");
    if (GOVERNED_TEST) {
      await expect(saveRefusal).toHaveAttribute(
        "data-refusal",
        "WS04_POSITION_PERSISTENCE_NOT_ACCEPTED",
      );
    }
    const leaked = await page.evaluate((needle) => {
      const dump = [
        JSON.stringify(Object.entries(window.localStorage)),
        JSON.stringify(Object.entries(window.sessionStorage)),
        document.cookie,
        window.location.href,
        document.title,
      ].join("|");
      return dump.includes(needle);
    }, secret);
    expect(leaked).toBe(false);
    // And the text is still on screen: blocked is not the same as discarded.
    await expect(page.locator("#position-body")).toHaveValue(secret);
  });
});

/* --------------------------------------------------------- security headers */

test.describe("origin boundary", () => {
  test("the response carries the isolation headers", async ({ page }) => {
    const response = await page.goto("/representative");
    expect(response).not.toBeNull();
    const headers = response!.headers();
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["referrer-policy"]).toBe("no-referrer");
    expect(headers["cross-origin-opener-policy"]).toBe("same-origin");
    expect(headers["cross-origin-resource-policy"]).toBe("same-origin");
    expect(headers["cache-control"]).toContain("no-store");
    expect(headers["content-security-policy"]).toContain(
      "frame-ancestors 'none'",
    );
    expect(headers["content-security-policy"]).toContain("object-src 'none'");
    expect(headers["content-security-policy"]).not.toContain("unsafe-inline");
    expect(headers["content-security-policy"]).not.toContain("unsafe-eval");
  });

  test("the page title never varies with the operator's state", async ({
    page,
  }) => {
    const titles: string[] = [];
    for (const route of ROUTES) {
      await open(page, route);
      titles.push(await page.title());
    }
    expect(new Set(titles).size).toBe(1);
    expect(titles[0]).toBe("Mandatsbereich — EPD²");
  });

  test("no URL carries case content in a query string", async ({ page }) => {
    for (const route of ROUTES) {
      await open(page, route);
      expect(new URL(page.url()).search).toBe("");
    }
  });
});

/* ------------------------------------------------------------- desk journey */

test.describe("the desk", () => {
  test.skip(!GOVERNED_TEST, "needs the governed profile's prototype material");

  test("the queue renders and every row is scoped to one mandate", async ({
    page,
  }) => {
    await open(page, "/representative/desk");
    await page.waitForSelector("[data-case-queue]", { timeout: 15_000 });
    const rows = page.locator("[data-case-row]");
    await expect(rows).toHaveCount(3);
    const mandates = await page.locator("[data-mandate-label]").allInnerTexts();
    expect(new Set(mandates).size).toBe(1);
  });

  test("a restricted case is not linked and its subject is withheld", async ({
    page,
  }) => {
    await open(page, "/representative/desk");
    await page.waitForSelector("[data-case-queue]", { timeout: 15_000 });
    const restricted = page.locator('[data-case-row="PROTOTYP-VORGANG-0003"]');
    await expect(restricted).toContainText("Zugriff eingeschränkt");
    await expect(restricted.locator("a")).toHaveCount(0);
  });

  test("a case detail opens and every action is refused", async ({ page }) => {
    await open(page, "/representative/desk/PROTOTYP-VORGANG-0001");
    await page.waitForSelector("[data-case-detail]", { timeout: 15_000 });
    const buttons = page.locator("[data-action] button");
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
    for (let index = 0; index < count; index += 1) {
      await expect(buttons.nth(index)).toBeDisabled();
      await expect(buttons.nth(index)).toHaveAttribute("data-offered", "false");
    }
  });

  /**
   * The non-disclosure property, checked across every negative outcome rather
   * than a pair of them. An earlier version of the surface rendered a distinct
   * panel for the conflict-restricted case, naming the conflict register — which
   * distinguished "restricted" from "does not exist" and reinstated the oracle
   * in a politer font. Comparing all four texts is what caught it.
   */
  test("every negative case outcome renders identical text", async ({
    page,
  }) => {
    const texts: Record<string, string> = {};
    for (const [label, caseId] of [
      ["unknown", "PROTOTYP-VORGANG-9999"],
      ["foreign", "FREMD-MANDAT-VORGANG-0001"],
      ["restricted", "PROTOTYP-VORGANG-0003"],
      ["malformed", "..%2F..%2Fetc"],
    ] as const) {
      await open(page, `/representative/desk/${caseId}`);
      // Wait for the outcome, so a transient loading state cannot be compared
      // against a resolved one.
      await page.waitForSelector("[data-refusal], [data-case-detail]", {
        timeout: 15_000,
      });
      await expect(page.locator("[data-case-resolving]")).toHaveCount(0);
      texts[label] = await page.locator("main").innerText();
    }
    const distinct = new Set(Object.values(texts));
    expect(
      distinct.size,
      `outcomes differ: ${JSON.stringify(Object.keys(texts))}`,
    ).toBe(1);
  });

  test("the refusal names no resource and no reason", async ({ page }) => {
    await open(page, "/representative/desk/PROTOTYP-VORGANG-0003");
    const panel = page.locator("[data-refusal]").first();
    await expect(panel).toHaveAttribute("data-non-disclosing", "true");
    await expect(panel).toHaveAttribute(
      "data-refusal",
      "WS04-CASE-UNAVAILABLE",
    );
    const text = await panel.innerText();
    expect(text).not.toContain("PROTOTYP-VORGANG-0003");
    expect(text).not.toContain("Konflikt");
    expect(text).not.toContain("Beschränkung");
  });

  test("the case identifier never reaches the title or a query string", async ({
    page,
  }) => {
    await open(page, "/representative/desk/PROTOTYP-VORGANG-0001");
    expect(await page.title()).toBe("Mandatsbereich — EPD²");
    expect(new URL(page.url()).search).toBe("");
  });
});

/* ------------------------------------------------------- consequential paths */

test.describe("consequential actions", () => {
  test("a declaration submission is blocked and the obligation is stated", async ({
    page,
  }) => {
    await open(page, "/representative/declarations");
    await page.fill("#declaration-subject", "Prototyp-Gegenstand");
    await page.fill("#declaration-date", "2026-01-15");
    await page.fill("#declaration-counterparty", "Prototyp-Gegenüber");
    await page.getByRole("button", { name: "Erklärung übermitteln" }).click();
    await expect(page.locator("[data-obligation-open]")).toBeVisible();
    await expect(page.locator("[data-obligation-open]")).toContainText(
      "Meldepflicht bleibt offen",
    );
  });

  test("a deviation without a decision reference is refused locally", async ({
    page,
  }) => {
    await open(page, "/representative/deviations");
    await page.fill("#deviation-issue", "Thema");
    await page.fill("#deviation-explanation", "x".repeat(60));
    await page.getByRole("button", { name: "Abweichung erfassen" }).click();
    await expect(page.locator("#error-summary")).toBeVisible();
  });

  test("a well-formed deviation is refused by the runtime, not accepted", async ({
    page,
  }) => {
    await open(page, "/representative/deviations");
    await page.fill("#deviation-issue", "Thema");
    await page.fill("#deviation-decision", "PROTOTYP-ENTSCHEIDUNG-0001");
    await page.fill("#deviation-explanation", "x".repeat(60));
    await page.getByRole("button", { name: "Abweichung erfassen" }).click();
    const refusal = page
      .locator('[aria-labelledby="deviation-new"] [data-refusal]')
      .first();
    await expect(refusal).toBeVisible();
    await expect(refusal).toContainText("Es wurde nichts geändert");
    if (GOVERNED_TEST) {
      await expect(refusal).toHaveAttribute(
        "data-refusal",
        "WS04_DEVIATION_CONTRACT_NOT_ACCEPTED",
      );
    }
  });

  test("a publication proposal is blocked and never reads as approval", async ({
    page,
  }) => {
    await open(page, "/representative/publication");
    await expect(page.locator("[data-proposal-disclaimer]")).toContainText(
      "keine Freigabe",
    );
    await page
      .getByRole("button", { name: "Veröffentlichung vorschlagen" })
      .click();
    const proposalRefusal = page
      .locator('[aria-labelledby="proposal-actions"] [data-refusal]')
      .first();
    await expect(proposalRefusal).toBeVisible();
    if (GOVERNED_TEST) {
      await expect(proposalRefusal).toHaveAttribute(
        "data-refusal",
        "WS04_PUBLICATION_PROPOSAL_MODEL_ABSENT",
      );
    }
    await expect(page.locator("[data-approval-reachable]")).toHaveAttribute(
      "data-approval-reachable",
      "false",
    );
  });

  test("the caller-asserted authorization boundary is shown as a finding", async ({
    page,
  }) => {
    await open(page, "/representative/publication");
    const gap = page.locator("[data-governance-gap]");
    await expect(gap).toHaveAttribute(
      "data-classification",
      "SECURITY_SENSITIVE_BOUNDARY",
    );
    await expect(page.locator("[data-security-finding]")).toContainText(
      "self-asserted",
    );
    await expect(
      page.locator("[data-caller-asserted-sufficient]"),
    ).toHaveAttribute("data-caller-asserted-sufficient", "false");
    // The remedies that would not resolve it are named, so none can be
    // mistaken for a fix by a later round.
    await expect(gap).toContainText(
      "adding a proposal route while authorization stays caller-supplied",
    );
  });

  test("no approval control exists on the publication surface", async ({
    page,
  }) => {
    await open(page, "/representative/publication");
    for (const name of [/freigeben/i, /genehmigen/i, /veröffentlichen$/i]) {
      await expect(page.getByRole("button", { name })).toHaveCount(0);
    }
  });

  test("the conflict surface offers no self-clearing control", async ({
    page,
  }) => {
    await open(page, "/representative/conflicts");
    await expect(page.locator("[data-no-self-clear]")).toHaveAttribute(
      "data-no-self-clear",
      "false",
    );
    for (const name of [/aufheben/i, /entfernen/i, /freigeben/i]) {
      await expect(page.getByRole("button", { name })).toHaveCount(0);
    }
  });

  test("an unreadable restriction register restricts rather than permits", async ({
    page,
  }) => {
    await open(page, "/representative/conflicts");
    if (GOVERNED_TEST) {
      await expect(page.locator("[data-restriction-list]")).toBeVisible();
    } else {
      await expect(
        page.locator("[data-any-restriction-active]"),
      ).toHaveAttribute("data-any-restriction-active", "true");
    }
  });
});

/* ------------------------------------------------------------------ reflow */

test.describe("reflow", () => {
  for (const route of ROUTES) {
    test(`${route} does not scroll the document horizontally`, async ({
      page,
    }) => {
      await page.setViewportSize({ width: 320, height: 720 });
      await open(page, route);
      const overflow = await page.evaluate(
        () =>
          document.documentElement.scrollWidth >
          document.documentElement.clientWidth + 1,
      );
      expect(overflow).toBe(false);
    });
  }
});

/* --------------------------------------------------------- keyboard operation */

test.describe("keyboard operation", () => {
  test("every navigation destination is reachable by keyboard", async ({
    page,
  }) => {
    await open(page, "/representative");
    const links = page.locator(".workspace-nav a");
    const count = await links.count();
    expect(count).toBe(7);
    for (let index = 0; index < count; index += 1) {
      await links.nth(index).focus();
      await expect(links.nth(index)).toBeFocused();
    }
  });

  test("the focus ring is visible on an interactive element", async ({
    page,
  }) => {
    await open(page, "/representative");
    const link = page.locator(".workspace-nav a").first();
    await link.focus();
    const outline = await link.evaluate(
      (element) => getComputedStyle(element).outlineWidth,
    );
    expect(outline).toBe("3px");
  });
});
