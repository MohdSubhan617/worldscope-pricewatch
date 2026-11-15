import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function loaded(page: Page): Promise<void> {
  await page.goto("/index.html");
  await expect(page.locator("table tr[tabindex]")).toHaveCount(3);
}

async function expectNoViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const summary = results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length} node(s))`);
  expect(summary, summary.join("\n")).toEqual([]);
}

test("page states that all data is simulated", async ({ page }) => {
  await loaded(page);
  await expect(page.locator(".banner")).toContainText("SIMULATED DATA");
  await expect(page.locator("footer")).toContainText("simulated");
  await expect(page.locator("table")).toContainText("(sim)");
});

test("no axe violations: light, default view", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await loaded(page);
  await expectNoViolations(page);
});

test("no axe violations: dark colour scheme", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await loaded(page);
  await expectNoViolations(page);
});

test("no axe violations: phone viewport", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await loaded(page);
  await expectNoViolations(page);
});

test("no axe violations after filtering and opening a detail", async ({ page }) => {
  await loaded(page);
  await page.getByRole("button", { name: "Phones", exact: true }).click();
  await expect(page.locator("table tr[tabindex]")).toHaveCount(2);
  const row = page.locator("table tr[tabindex]").first();
  await row.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("img", { name: /Simulated price history/ })).toBeVisible();
  await expectNoViolations(page);
});

test("control: axe really reports violations on a deliberately bad page", async ({ page }) => {
  await page.setContent(
    '<html lang="en"><head><title>x</title></head><body><img src="data:,"><button></button></body></html>',
  );
  const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const ids = results.violations.map((v) => v.id);
  expect(ids).toContain("image-alt");
  expect(ids).toContain("button-name");
});
