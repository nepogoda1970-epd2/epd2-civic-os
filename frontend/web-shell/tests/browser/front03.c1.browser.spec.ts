import { expect, test, type Page, type Route } from "@playwright/test";

const ORG = "2f5b9d24-6c1e-4a37-9f18-0b7d3c5e8a41";

const account = {
  account_id: "discarded-account-reference",
  account_status: "active",
  email_status: "verified",
  mfa_status: "configured",
  locale: "de",
  membership_state: "membership_governed",
  identity_verified: false,
};
const membership = {
  account_reference: "discarded-account-reference",
  organization_id: ORG,
  membership_state: "membership_governed",
  is_governed_membership: true,
  unreachable_states: [],
  unreachable_reason: "",
  latest_application_status: "accepted",
};

async function fulfill(route: Route, body: unknown, status = 200) {
  expect(route.request().method()).toBe("GET");
  expect(route.request().headers()["authorization"]).toBeUndefined();
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function bindMemberApi(page: Page) {
  await page.route("**/api/v1/account/me", (route) => fulfill(route, account));
  await page.route("**/api/v1/membership/me", (route) =>
    fulfill(route, membership),
  );
}

test("C1 production adapter resolves governed Member and exact current scope", async ({
  page,
}) => {
  await bindMemberApi(page);
  await page.goto("/member/home");
  await expect(
    page.getByRole("heading", { name: "Mein Bürgerbereich" }),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Mitgliederbereich" }),
  ).toBeVisible();
  const scope = page.locator("#scope");
  await expect(scope).toHaveValue(ORG);
  await expect(scope.locator("option")).toHaveCount(1);
  await expect(scope.locator("option")).toHaveText(
    "Aktueller autorisierter Organisationskontext",
  );
  await expect(page.getByText(/Anna Beispiel|ANTRAG-2026-0142/)).toHaveCount(0);
});

test("C1 production adapter keeps non-governed account out of Member routes", async ({
  page,
}) => {
  await page.route("**/api/v1/account/me", (route) =>
    fulfill(route, { ...account, membership_state: "application_pending" }),
  );
  await page.route("**/api/v1/membership/me", (route) =>
    fulfill(route, {
      ...membership,
      membership_state: "application_pending",
      is_governed_membership: false,
      latest_application_status: "under_review",
    }),
  );
  await page.goto("/member/home");
  await expect(
    page.getByText("Dieser Bereich ist für Ihr Konto nicht freigegeben."),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Mitgliederbereich" }),
  ).toHaveCount(0);
});

test("C1 assurance surface uses accepted read routes and never renders opaque references", async ({
  page,
}) => {
  await bindMemberApi(page);
  await page.route("**/api/v1/identity/security-state", (route) =>
    fulfill(route, {
      account_status: "active",
      activated: true,
      credential_count: 1,
      credential_types: ["passkey"],
      factor_classes: ["possession"],
      active_session_count: 1,
      lock_in_force: false,
      restriction_in_force: false,
      closure_requested: false,
    }),
  );
  await page.route("**/api/v1/identity/sessions", (route) =>
    fulfill(route, {
      sessions: [
        {
          session_reference: "opaque-session-reference-must-not-render",
          workspace: "member",
          origin: "https://app.epd.example",
          assurance: "substantial",
          issued_at: "2026-09-01T00:00:00Z",
          idle_deadline: "2026-09-01T01:00:00Z",
          absolute_deadline: "2026-09-02T00:00:00Z",
          device_label: "Notebook",
          status: "active",
          current: true,
        },
      ],
    }),
  );
  await page.route("**/api/v1/identity/credentials", (route) =>
    fulfill(route, {
      credentials: [
        {
          credential_reference: "opaque-credential-reference-must-not-render",
          credential_type: "passkey",
          nickname: "Notebook",
          binding: "device_bound",
          status: "active",
        },
      ],
    }),
  );
  await page.goto("/member/assurance/authentication-session-assurance");
  await expect(
    page.getByText("Aktuelle Sitzung · substantial · active"),
  ).toBeVisible();
  await expect(page.getByText("passkey · Notebook · active")).toBeVisible();
  await expect(
    page.getByText(/opaque-session-reference|opaque-credential-reference/),
  ).toHaveCount(0);
});

test("C1 browser persistence contains display preference only, never bearer authority", async ({
  page,
}) => {
  await bindMemberApi(page);
  await page.goto("/member/home");
  await expect(page.locator("#scope")).toHaveValue(ORG);
  const state = await page.evaluate(async () => {
    const local = Object.fromEntries(Object.entries(localStorage));
    const session = Object.fromEntries(Object.entries(sessionStorage));
    const dbs = "databases" in indexedDB ? await indexedDB.databases() : [];
    return { local, session, indexedDbNames: dbs.map((x) => x.name ?? "") };
  });
  const encoded = JSON.stringify(state);
  expect(encoded).not.toMatch(
    /bearer|access[_-]?token|refresh[_-]?token|epd2_session|credential_reference/i,
  );
  expect(Object.keys(state.local)).toEqual(["epd2.display.last-scope"]);
  expect(state.local["epd2.display.last-scope"]).toBe(ORG);
  expect(Object.keys(state.session)).toHaveLength(0);
});
