import { defineConfig, devices } from "@playwright/test";
import chromium from "@sparticuz/chromium";
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

// Keep the extracted browser outside the repository. Some overlay filesystems
// reject the ownership metadata used by the Chromium runtime archive.
const browserTemp = "/tmp/epd2-front00-browser-runtime";
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
    baseURL: "http://127.0.0.1:3100",
    colorScheme: "light",
    locale: "de-DE",
    contextOptions: { reducedMotion: "reduce" },
    trace: "retain-on-failure",
    launchOptions: {
      executablePath,
      // The serverless default uses a single renderer process. Full-page
      // screenshots of the longer FRONT-00 fixtures can exhaust that process,
      // so browser verification uses Chromium's normal multi-process model.
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
  webServer: process.env.FRONT00_EXTERNAL_SERVER
    ? undefined
    : {
        command: "npm run build && node tests/start-next.mjs",
        port: 3100,
        reuseExistingServer: !process.env.CI,
        timeout: 180_000,
      },
});
