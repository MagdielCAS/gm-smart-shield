import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NotesPage from "./NotesPage";

const mockFetch = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", mockFetch);

const makeClient = () =>
	new QueryClient({ defaultOptions: { queries: { retry: false } } });

const wrapper = ({ children }: { children: React.ReactNode }) => (
	<QueryClientProvider client={makeClient()}>{children}</QueryClientProvider>
);

const mockInitialQueries = ({
	notes,
	folders,
}: {
	notes: unknown[];
	folders: unknown[];
}) => {
	mockFetch
		.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ items: notes }),
		} as Response)
		.mockResolvedValueOnce({
			ok: true,
			json: async () => ({ items: folders }),
		} as Response);
};

describe("NotesPage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("creates a note and refreshes list", async () => {
		mockInitialQueries({ notes: [], folders: [] });
		mockFetch
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
		});
	});

	it("preserves metadata and links when updating an existing note", async () => {
		mockInitialQueries({
			notes: [
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
			folders: [{ id: 7, name: "Investigations", parent_id: null }],
		});
		mockFetch
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
				expect.objectContaining({ method: "PUT" }),
			);
		});
	});

	it("shows ghost suggestion and applies preview action", async () => {
		mockInitialQueries({ notes: [], folders: [] });
		mockFetch
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
	});

	it("creates a folder and filters notes by selected folder", async () => {
		mockInitialQueries({
			notes: [
				{
					id: 9,
					title: "Town hooks",
					content: "# Hooks",
					frontmatter: null,
					metadata: {},
					folder_id: 4,
					created_at: "2026-01-01T10:00:00Z",
					updated_at: "2026-01-01T10:00:00Z",
					tags: [],
					links: [],
				},
				{
					id: 10,
					title: "Combat prep",
					content: "# Combat",
					frontmatter: null,
					metadata: {},
					folder_id: null,
					created_at: "2026-01-01T10:00:00Z",
					updated_at: "2026-01-01T10:00:00Z",
					tags: [],
					links: [],
				},
			],
			folders: [{ id: 4, name: "Session 5", parent_id: null }],
		});

		mockFetch
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ id: 5, name: "Lore", parent_id: null }),
			} as Response)
			.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					items: [
						{ id: 4, name: "Session 5", parent_id: null },
						{ id: 5, name: "Lore", parent_id: null },
					],
				}),
			} as Response);

		render(<NotesPage />, { wrapper });

		fireEvent.change(screen.getByPlaceholderText("New folder"), {
			target: { value: "Lore" },
		});
		fireEvent.click(screen.getByRole("button", { name: "Create folder" }));

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/notes/folders",
				expect.objectContaining({ method: "POST" }),
			);
		});

		fireEvent.click(screen.getByRole("button", { name: "Session 5" }));
		expect(screen.getByText("Town hooks")).toBeInTheDocument();
		expect(screen.queryByText("Combat prep")).not.toBeInTheDocument();
	});
});
