import { defineConfig, devices } from "@playwright/test";
import chromium from "@sparticuz/chromium";
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

const browserTemp = "/tmp/epd2-front04-browser-runtime";
mkdirSync(browserTemp, { recursive: true });
process.env.TMPDIR = browserTemp;
process.env.XDG_CACHE_HOME = resolve(browserTemp, "cache");
process.env.FONTCONFIG_PATH = resolve(browserTemp, "fonts");
process.env.FONTCONFIG_FILE = resolve(browserTemp, "fonts", "fonts.conf");
process.env.LD_LIBRARY_PATH = [
  resolve(browserTemp, "al2023/lib"),
  process.env.LD_LIBRARY_PATH,
]
  .filter(Boolean)
  .join(":");
mkdirSync(process.env.XDG_CACHE_HOME, { recursive: true });
const executablePath = execFileSync(
  process.execPath,
  [resolve(process.cwd(), "tests/resolve-chromium.mjs")],
  { encoding: "utf8", env: { ...process.env, TMPDIR: browserTemp } },
).trim();
chromium.setGraphicsMode = false;

/**
 * Two profiles, two builds.
 *
 * `production` is the build a deployment would ship: the fixture module is
 * replaced at build time and every capability is blocked.  `governed_test`
 * additionally carries the fixture election context and ballot style, so the
 * ballot, review and cancellation journeys can be exercised against a real
 * browser.  Neither profile can cast, encrypt or produce a receipt.
 */
const PROFILE =
  process.env.FRONT04_TEST_PROFILE === "production"
    ? "production"
    : "governed_test";
const flag = PROFILE === "production" ? "0" : "1";
const command = `NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_FRONT04_GOVERNED_TEST=${flag} npm run build && NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_FRONT04_GOVERNED_TEST=${flag} node tests/start-next.mjs`;

export default defineConfig({
  testDir: "./tests/browser",
  outputDir: "test-results",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["line"], ["html", { open: "never" }]] : "line",
  expect: {
    toHaveScreenshot: {
      animations: "disabled",
      maxDiffPixelRatio: 0.015,
      threshold: 0.2,
    },
  },
  use: {
    baseURL: "http://127.0.0.1:3200",
    colorScheme: "light",
    locale: "de-DE",
    contextOptions: { reducedMotion: "reduce" },
    trace: "retain-on-failure",
    launchOptions: {
      executablePath,
      args: chromium.args.filter(
        (argument) =>
          argument !== "--single-process" && argument !== "--no-zygote",
      ),
    },
  },
  projects: [
    { name: "mobile", use: { ...devices["Pixel 7"] } },
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: "wide",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1920, height: 1080 },
      },
    },
  ],
  webServer: process.env.FRONT04_EXTERNAL_SERVER
    ? undefined
    : {
        command,
        port: 3200,
        reuseExistingServer: !process.env.CI,
        timeout: 240_000,
      },
});
