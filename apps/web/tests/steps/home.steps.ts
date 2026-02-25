import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Given, Then } = createBdd();

Given("I am on the home page", async ({ page }) => {
	await page.goto("http://localhost:5173");
});

Then("I should see {string}", async ({ page }, text) => {
	await expect(page.getByText(text)).toBeVisible();
});
