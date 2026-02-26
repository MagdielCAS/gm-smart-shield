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
		});
	});
});
