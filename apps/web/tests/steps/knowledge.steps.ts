import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Given, When, Then } = createBdd();

// Background
Given("the knowledge base has existing sources", async ({ page }) => {
    // Mock the API response for list
    await page.route("**/api/v1/knowledge/", async (route) => {
        if (route.request().method() === "GET") {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    items: [
                        {
                            id: 1,
                            source: "/docs/rulebook.pdf",
                            filename: "rulebook.pdf",
                            chunk_count: 10,
                            status: "completed",
                            progress: 100,
                            current_step: "Done",
                            last_indexed_at: new Date().toISOString(),
                            error_message: null,
                            features: ["indexation"],
                        }
                    ]
                }),
            });
        } else {
            await route.continue();
        }
    });

    // Mock stats
    await page.route("**/api/v1/knowledge/stats", async (route) => {
        await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ document_count: 1, chunk_count: 10 }),
        });
    });

    await page.goto("/knowledge");
    // Verify list is visible
    await expect(page.locator("h2:has-text('Knowledge Base')")).toBeVisible();
});

// View knowledge sources list and status
When("I navigate to the knowledge page", async ({ page }) => {
    // Already there from background or just reload
    await page.goto("/knowledge");
});

Then("I should see a list of knowledge sources", async ({ page }) => {
    // Check for the mock item - target the filename specifically to avoid ambiguity
    await expect(page.locator("p.font-medium", { hasText: "rulebook.pdf" })).toBeVisible();
});

Then("I should see status badges for each source \\(e.g., {string}, {string}\\)", async ({ page }, s1, s2) => {
    // We check if we see "Completed" which corresponds to our mock
    await expect(page.getByText(s1)).toBeVisible();
});

// Ingest a new file and see progress
Given("I have selected a file {string}", async ({ page }, filePath) => {
    // Mock the file selection logic.
    await page.addInitScript((path) => {
        (window as any).electron = {
            openFile: () => Promise.resolve(path),
        };
    }, filePath);

    // Handle potential alerts if mock fails
    page.on('dialog', dialog => {
        console.log(`Dialog appeared: ${dialog.message()}`);
        dialog.accept();
    });

    // Reload to apply init script
    await page.reload();
});

When("I click the \"Add Source\" button", async ({ page }) => {
    // Mock the POST request
    await page.route("**/api/v1/knowledge/", async (route) => {
        if (route.request().method() === "POST") {
            await route.fulfill({
                status: 202,
                contentType: "application/json",
                body: JSON.stringify({
                    task_id: "task-123",
                    status: "pending",
                    message: "Processing started"
                }),
            });
        } else if (route.request().method() === "GET") {
             // Return updated list with pending item
             await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    items: [
                        {
                            id: 2,
                            source: "/docs/new_monster.md",
                            filename: "new_monster.md",
                            chunk_count: 0,
                            status: "running",
                            progress: 45,
                            current_step: "Embedding",
                            started_at: new Date(Date.now() - 60000).toISOString(), // 1 min ago
                            last_indexed_at: null,
                            error_message: null,
                            features: [],
                        }
                    ]
                }),
            });
        }
    });

    // Try text locator
    await page.locator("text=Select File").click({ force: true });
});

Then("I should see the new source appear in the list with status {string} or {string}", async ({ page }, s1, s2) => {
    // Wait for the list to refresh (polling)
    await expect(page.locator("p.font-medium", { hasText: "new_monster.md" })).toBeVisible();
    await expect(page.getByText(s2)).toBeVisible(); // "Running"
});

Then("I should see a progress bar for the running task", async ({ page }) => {
    // Check for progress text "45%"
    await expect(page.getByText("45%")).toBeVisible();
});

Then("I should see an estimated time remaining message", async ({ page }) => {
    // "1 min ago" started, 45% done -> roughly 1 min remaining
    await expect(page.getByText("remaining")).toBeVisible();
});

// Refresh an existing source
Given("I have a {string} knowledge source in the list", async ({ page }, status) => {
    // Reset mocks to show completed item
    await page.route("**/api/v1/knowledge/", async (route) => {
         await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
                items: [
                    {
                        id: 1,
                        source: "/docs/rulebook.pdf",
                        filename: "rulebook.pdf",
                        chunk_count: 10,
                        status: status.toLowerCase(),
                        progress: 100,
                        current_step: "Done",
                        last_indexed_at: new Date().toISOString(),
                        error_message: null,
                        features: ["indexation"],
                    }
                ]
            }),
        });
    });

    // Mock stats
    await page.route("**/api/v1/knowledge/stats", async (route) => {
        await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ document_count: 1, chunk_count: 10 }),
        });
    });

    await page.goto("/knowledge");
    await expect(page.getByText(status)).toBeVisible();
});

When("I click the \"Refresh\" button for that source", async ({ page }) => {
    // Mock the refresh POST
    await page.route("**/api/v1/knowledge/*/refresh", async (route) => {
        await route.fulfill({
            status: 202,
            contentType: "application/json",
            body: JSON.stringify({
                task_id: "task-refresh-123",
                status: "pending",
                message: "Refresh started"
            }),
        });
    });

    // Let's hook the next GET request to return running
    await page.route("**/api/v1/knowledge/", async (route) => {
         await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
                items: [
                    {
                        id: 1,
                        source: "/docs/rulebook.pdf",
                        filename: "rulebook.pdf",
                        chunk_count: 10,
                        status: "running", // Changed to running
                        progress: 0,
                        current_step: "Queued",
                        last_indexed_at: null,
                        error_message: null,
                        features: ["indexation"],
                    }
                ]
            }),
        });
    });

    // Find the row
    const row = page.locator("div.group").filter({ hasText: "rulebook.pdf" });

    // Hover to reveal button
    await row.hover();

    // Click refresh - using getByTitle
    await page.getByTitle("Refresh source").first().click({ force: true });
});

Then("the status badge should change to {string} or {string}", async ({ page }, s1, s2) => {
    await expect(page.getByText(s2)).toBeVisible();
});

Then("I should see a loading spinner or progress indicator", async ({ page }) => {
    // The refresh button itself spins when pending
    // But we also checked for "Running" status which implies progress UI
    await expect(page.getByText("Queued")).toBeVisible();
});
