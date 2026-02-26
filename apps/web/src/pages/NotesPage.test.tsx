import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NotesPage from "./NotesPage";

const mockFetch = vi.fn<typeof fetch>();
global.fetch = mockFetch;

const makeClient = () =>
	new QueryClient({ defaultOptions: { queries: { retry: false } } });

const wrapper = ({ children }: { children: React.ReactNode }) => (
	<QueryClientProvider client={makeClient()}>{children}</QueryClientProvider>
);

describe("NotesPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("creates a note and refreshes list", async () => {
		mockFetch
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ items: [] }),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					id: 1,
					title: "Session 1",
					content: "# Session notes",
					frontmatter: null,
					metadata: {},
					folder_id: null,
					created_at: "2026-01-01T10:00:00Z",
					updated_at: "2026-01-01T10:00:00Z",
					tags: ["session"],
					links: [
						{
							source_id: "rules",
							source_file: "/rules/phb.pdf",
							page_number: 10,
							chunk_id: "rules_10",
						},
					],
				}),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					items: [
						{
							id: 1,
							title: "Session 1",
							content: "# Session notes",
							frontmatter: null,
							metadata: {},
							folder_id: null,
							created_at: "2026-01-01T10:00:00Z",
							updated_at: "2026-01-01T10:00:00Z",
							tags: ["session"],
							links: [
								{
									source_id: "rules",
									source_file: "/rules/phb.pdf",
									page_number: 10,
									chunk_id: "rules_10",
								},
							],
						},
					],
				}),
			} as Response);

		render(<NotesPage />, { wrapper });

		fireEvent.change(screen.getByLabelText("Title"), {
			target: { value: "Session 1" },
		});
		fireEvent.click(screen.getByRole("button", { name: "Save note" }));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes",
				expect.objectContaining({ method: "POST" }),
			);
		});

		await waitFor(() => {
			expect(screen.getByText("Session 1")).toBeInTheDocument();
			expect(screen.getByText("/rules/phb.pdf")).toBeInTheDocument();
			expect(screen.getByText("session")).toBeInTheDocument();
			expect(screen.getByText(/^Created:/)).not.toHaveTextContent("Not saved");
			expect(screen.getByText(/^Updated:/)).not.toHaveTextContent("Not saved");
		});
	});

	it("preserves metadata and links when updating an existing note", async () => {
		mockFetch
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					items: [
						{
							id: 2,
							title: "Investigation",
							content: "Initial content",
							frontmatter: { location: "Dock Ward" },
							metadata: {},
							folder_id: 7,
							created_at: "2026-01-01T10:00:00Z",
							updated_at: "2026-01-01T10:00:00Z",
							tags: ["mystery"],
							links: [
								{
									source_id: "gazetteer",
									source_file: "/world/dock-ward.md",
									page_number: null,
									chunk_id: "dock_ward_1",
								},
							],
						},
					],
				}),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					id: 2,
					title: "Investigation",
					content: "Updated content",
					frontmatter: { location: "Dock Ward" },
					metadata: {},
					folder_id: 7,
					created_at: "2026-01-01T10:00:00Z",
					updated_at: "2026-01-02T10:00:00Z",
					tags: ["mystery"],
					links: [
						{
							source_id: "gazetteer",
							source_file: "/world/dock-ward.md",
							page_number: null,
							chunk_id: "dock_ward_1",
						},
					],
				}),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					items: [
						{
							id: 2,
							title: "Investigation",
							content: "Updated content",
							frontmatter: { location: "Dock Ward" },
							metadata: {},
							folder_id: 7,
							created_at: "2026-01-01T10:00:00Z",
							updated_at: "2026-01-02T10:00:00Z",
							tags: ["mystery"],
							links: [
								{
									source_id: "gazetteer",
									source_file: "/world/dock-ward.md",
									page_number: null,
									chunk_id: "dock_ward_1",
								},
							],
						},
					],
				}),
			} as Response);

		render(<NotesPage />, { wrapper });

		await waitFor(() => {
			expect(screen.getByText("Investigation")).toBeInTheDocument();
		});

		fireEvent.click(screen.getByText("Investigation"));
		fireEvent.change(screen.getByLabelText("Markdown"), {
			target: { value: "Updated content" },
		});
		fireEvent.click(screen.getByRole("button", { name: "Save note" }));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes/2",
				expect.objectContaining({
					method: "PUT",
					body: JSON.stringify({
						title: "Investigation",
						content: "Updated content",
						folder_id: 7,
						frontmatter: { location: "Dock Ward" },
						tags: ["mystery"],
						sources: [
							{
								source_id: "gazetteer",
								source_file: "/world/dock-ward.md",
								page_number: null,
								chunk_id: "dock_ward_1",
							},
						],
					}),
				}),
			);
		});
	});

	it("shows ghost suggestion and applies preview action", async () => {
		mockFetch
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ items: [] }),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ suggestion: " Next, ", reason: "punctuation" }),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					action: "rewrite",
					original_text: "caravan",
					preview_text: "caravan (rewritten for clarity)",
					selection_start: 4,
					selection_end: 11,
					mode: "replace",
				}),
			} as Response);

		render(<NotesPage />, { wrapper });

		const markdownInput = screen.getByLabelText("Markdown");
		fireEvent.change(markdownInput, {
			target: { value: "The caravan vanished.", selectionStart: 20 },
		});

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes/inline-suggest",
				expect.objectContaining({ method: "POST" }),
			);
		});

		(markdownInput as HTMLTextAreaElement).setSelectionRange(4, 11);
		fireEvent.contextMenu(markdownInput, {
			clientX: 100,
			clientY: 100,
		});
		fireEvent.click(screen.getByRole("button", { name: "Rewrite" }));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes/transform/preview",
				expect.objectContaining({ method: "POST" }),
			);
		});

		fireEvent.click(screen.getByRole("button", { name: "Apply to draft" }));
		expect(
			screen.getByDisplayValue(/rewritten for clarity/),
		).toBeInTheDocument();
	});

	it("invokes add reference link context action", async () => {
		mockFetch
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ items: [] }),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					action: "add_reference_link",
					original_text: "Waterdeep",
					preview_text: "[Waterdeep](ref://knowledge/waterdeep)",
					selection_start: 4,
					selection_end: 13,
					mode: "replace",
				}),
			} as Response);

		render(<NotesPage />, { wrapper });

		const markdownInput = screen.getByLabelText("Markdown");
		fireEvent.change(markdownInput, {
			target: { value: "The Waterdeep docks", selectionStart: 13 },
		});

		(markdownInput as HTMLTextAreaElement).setSelectionRange(4, 13);
		fireEvent.contextMenu(markdownInput, {
			clientX: 120,
			clientY: 120,
		});
		fireEvent.click(screen.getByRole("button", { name: "Add reference link" }));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes/transform/preview",
				expect.objectContaining({
					method: "POST",
					body: JSON.stringify({
						action: "add_reference_link",
						content: "The Waterdeep docks",
						selection_start: 4,
						selection_end: 13,
					}),
				}),
			);
		});
	});
});
