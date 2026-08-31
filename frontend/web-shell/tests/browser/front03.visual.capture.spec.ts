import { expect, type Page, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

async function applicant(page: Page) {
  await page.context().addCookies([
    {
      name: "front03_fixture_principal",
      value: "applicant",
      url: "http://127.0.0.1:3100",
    },
  ]);
}

const cases = [
  ["application", "/member/application", "ANTRAG-2026-0142"],
  ["home", "/member/home", "Aktiv · Bund"],
  ["membership", "/member/membership", "Provenienz"],
  ["initiatives", "/member/initiatives", "Offene kommunale Daten"],
  ["initiatives-new", "/member/initiatives/new", "Vorschau"],
  ["deliberation", "/member/deliberation", "Offene kommunale Daten"],
  ["delegation", "/member/delegation", "Kein akzeptierter Laufzeitvertrag"],
  [
    "assurance-authentication-session-assurance",
    "/member/assurance/authentication-session-assurance",
    "AL2",
  ],
  [
    "membership-appeal",
    "/member/membership/appeal",
    "Rechtliche und operative Aktivierung",
  ],
] as const;

for (const [key, route, readyText] of cases) {
  test(`capture immutable FRONT03 ${key}`, async ({ page }, testInfo) => {
    if (key === "application" || key === "membership-appeal") {
      await applicant(page);
    }
    await page.goto(route);
    await expect(
      page.getByText(readyText, { exact: false }).first(),
    ).toBeVisible();
    const directory = resolve(
      process.cwd(),
      "tests/browser/front03.browser.spec.ts-snapshots",
    );
    await mkdir(directory, { recursive: true });
    await page.screenshot({
      path: resolve(
        directory,
        `front03-${key}-${testInfo.project.name}-linux.png`,
      ),
      fullPage: true,
      animations: "disabled",
    });
  });
}
