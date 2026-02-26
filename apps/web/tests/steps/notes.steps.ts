import { expect } from "@playwright/test";
import { createBdd } from "playwright-bdd";

const { Given, When, Then } = createBdd();

type NoteRecord = {
	id: number;
	title: string;
	content: string;
	created_at: string;
	updated_at: string;
	tags: string[];
	links: Array<{
		source_id: string | null;
		source_file: string | null;
		page_number: number | null;
		chunk_id: string | null;
	}>;
	frontmatter: Record<string, unknown> | null;
	metadata: Record<string, unknown>;
	folder_id: number | null;
};

Given("notes API responses are mocked", async ({ page }) => {
	const notes: NoteRecord[] = [
		{
			id: 1,
			title: "Session One",
			content: "# Session notes\n",
			created_at: "2026-01-01T10:00:00Z",
			updated_at: "2026-01-01T10:00:00Z",
			tags: ["session"],
			links: [],
			frontmatter: null,
			metadata: {},
			folder_id: null,
		},
	];

	await page.route("**/api/v1/notes**", async (route, request) => {
		const method = request.method();
		if (method === "GET") {
			await route.fulfill({
				status: 200,
				contentType: "application/json",
				body: JSON.stringify({ items: notes }),
			});
			return;
		}

		if (method === "POST") {
			const payload = request.postDataJSON() as { title: string; content: string };
			const created: NoteRecord = {
				id: notes.length + 1,
				title: payload.title,
				content: payload.content,
				created_at: "2026-01-02T10:00:00Z",
				updated_at: "2026-01-02T10:00:00Z",
				tags: ["session"],
				links: [],
				frontmatter: null,
				metadata: {},
				folder_id: null,
			};
			notes.push(created);
			await route.fulfill({
				status: 200,
				contentType: "application/json",
				body: JSON.stringify(created),
			});
			return;
		}
		await route.fallback();
	});

	await page.route("**/api/v1/notes/*", async (route, request) => {
		if (request.method() !== "PUT") {
			await route.fallback();
			return;
		}
		const noteId = Number.parseInt(request.url().split("/").pop() ?? "0", 10);
		const payload = request.postDataJSON() as { title: string; content: string };
		const existing = notes.find((note) => note.id === noteId);
		if (!existing) {
			await route.fulfill({ status: 404, body: JSON.stringify({ detail: "Note not found" }) });
			return;
		}
		existing.title = payload.title;
		existing.content = payload.content;
		existing.updated_at = "2026-01-03T10:00:00Z";
		await route.fulfill({
			status: 200,
			contentType: "application/json",
			body: JSON.stringify(existing),
		});
	});

	await page.route("**/api/v1/notes/inline-suggest", async (route) => {
		await route.fulfill({
			status: 200,
			contentType: "application/json",
			body: JSON.stringify({ suggestion: " Next, ", reason: "punctuation" }),
		});
	});

	await page.route("**/api/v1/notes/transform/preview", async (route, request) => {
		const payload = request.postDataJSON() as { action: string };
		if (payload.action === "add_reference_link") {
			await route.fulfill({
				status: 200,
				contentType: "application/json",
				body: JSON.stringify({
					action: "add_reference_link",
					original_text: "Waterdeep",
					preview_text: "[Waterdeep](ref://knowledge/waterdeep)",
					selection_start: 4,
					selection_end: 13,
					mode: "replace",
				}),
			});
			return;
		}
		await route.fulfill({
			status: 200,
			contentType: "application/json",
			body: JSON.stringify({
				action: "rewrite",
				original_text: "caravan",
				preview_text: "caravan (rewritten for clarity)",
				selection_start: 4,
				selection_end: 11,
				mode: "replace",
			}),
		});
	});
});

Given("I am on the notes page", async ({ page }) => {
	await page.goto("http://localhost:5173/notes");
});

When("I create a note titled {string}", async ({ page }, title: string) => {
	await page.getByLabel("Title").fill(title);
	await page.getByRole("button", { name: "Save note" }).click();
});

Then("I should see the note {string} in the list", async ({ page }, title: string) => {
	await expect(page.getByRole("button", { name: new RegExp(title) })).toBeVisible();
});

When("I edit note {string} with content {string}", async ({ page }, title: string, content: string) => {
	await page.getByRole("button", { name: new RegExp(title) }).click();
	await page.getByLabel("Markdown").fill(content);
	await page.getByRole("button", { name: "Save note" }).click();
});

Then("the notes API should receive an update for {string}", async ({ page }, title: string) => {
	await expect(page.getByRole("button", { name: new RegExp(title) })).toBeVisible();
	await expect(page.getByLabel("Markdown")).toHaveValue("Updated mystery thread");
});

When("I trigger inline AI suggestion for punctuation", async ({ page }) => {
	await page.getByLabel("Markdown").fill("The caravan vanished.");
});

Then("I should see a ghost suggestion hint", async ({ page }) => {
	await expect(page.getByText("Ghost suggestion:")).toBeVisible();
});

When("I run add reference link from the note context menu", async ({ page }) => {
	const markdown = page.getByLabel("Markdown");
	await markdown.fill("The Waterdeep docks");
	await markdown.click();
	await page.keyboard.down("Shift");
	for (let index = 0; index < 9; index += 1) {
		await page.keyboard.press("ArrowRight");
	}
	await page.keyboard.up("Shift");
	await markdown.click({ button: "right" });
	await page.getByRole("button", { name: "Add reference link" }).click();
});

Then("I should see an add reference preview", async ({ page }) => {
	await expect(page.getByText("Preview: add_reference_link")).toBeVisible();
	await expect(page.getByText("[Waterdeep](ref://knowledge/waterdeep)")).toBeVisible();
});
