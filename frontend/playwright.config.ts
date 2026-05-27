import { defineConfig, devices } from "@playwright/test";

const headed = process.env.ZAIKON_E2E_HEADED === "1";
const slowMo = Number(process.env.ZAIKON_E2E_SLOWMO ?? (headed ? "450" : "0"));

export default defineConfig({
  testDir: "./e2e",
  timeout: 10 * 60 * 1000,
  expect: {
    timeout: 20_000
  },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: process.env.ZAIKON_E2E_UI_BASE ?? "http://127.0.0.1:5173",
    headless: !headed,
    launchOptions: {
      slowMo
    },
    actionTimeout: 30_000,
    navigationTimeout: 30_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: headed ? "off" : "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" }
    }
  ]
});
