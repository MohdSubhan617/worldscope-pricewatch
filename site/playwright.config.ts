import { defineConfig, devices } from "@playwright/test";

const channel = process.env["PW_CHANNEL"]; // e.g. "msedge" locally; unset in CI (bundled Chromium)

export default defineConfig({
  testDir: "e2e",
  fullyParallel: true,
  forbidOnly: !!process.env["CI"],
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:4173" },
  projects: [
    {
      name: "chromium",
      use: channel === undefined ? { ...devices["Desktop Chrome"] } : { ...devices["Desktop Chrome"], channel },
    },
  ],
  webServer: {
    command: "node scripts/serve.mjs",
    url: "http://127.0.0.1:4173/index.html",
    env: { E2E_FIXTURES: "1" },
    reuseExistingServer: false,
  },
});
