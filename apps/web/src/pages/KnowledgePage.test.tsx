import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import KnowledgePage from "./KnowledgePage";

// Mock API_BASE_URL
vi.mock("../config", () => ({
	API_BASE_URL: "/api",
}));

// Mock electron
const mockOpenFile = vi.fn();

// Mock fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

const makeQueryClient = () =>
	new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false },
		},
	});

// ── Default fetch responses ──────────────────────────────────────────────────

const emptyListResponse = { items: [] };
const populatedListResponse = {
	items: [
		{
			id: 1,
			source: "/docs/monster-manual.pdf",
			filename: "monster-manual.pdf",
			chunk_count: 42,
			status: "completed",
			progress: 100,
			current_step: "Done",
			started_at: "2023-01-01T00:00:00Z",
			last_indexed_at: "2023-01-01T00:00:00Z",
			error_message: null,
			features: ["indexation"],
		},
		{
			id: 2,
			source: "/docs/rulebook.txt",
			filename: "rulebook.txt",
			chunk_count: 18,
			status: "running",
			progress: 50,
			current_step: "Embedding",
			started_at: "2023-01-01T00:00:00Z",
			last_indexed_at: null,
			error_message: null,
			features: [],
		},
	],
};
const statsResponse = { document_count: 2, chunk_count: 60 };
const emptyStatsResponse = { document_count: 0, chunk_count: 0 };

function mockGetResponses(
	list: object = emptyListResponse,
	stats: object = emptyStatsResponse,
) {
	mockFetch.mockImplementation(async (url: string) => {
		if (url.includes("/stats")) {
			return { ok: true, json: async () => stats };
		}
		if (url.endsWith("/knowledge/")) {
			return { ok: true, json: async () => list };
		}
		return { ok: false, json: async () => ({}) };
	});
}

const wrapper = ({ children }: { children: React.ReactNode }) => (
	<QueryClientProvider client={makeQueryClient()}>
		{children}
	</QueryClientProvider>
);

// ── Tests ────────────────────────────────────────────────────────────────────

describe("KnowledgePage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		window.electron = { openFile: mockOpenFile };
	});

	it("renders page structure correctly", async () => {
		mockGetResponses();
		render(<KnowledgePage />, { wrapper });
		expect(screen.getByText("Knowledge Base")).toBeInTheDocument();
		expect(screen.getByText("Add New Source")).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: "Select File" }),
		).toBeInTheDocument();
	});

	it("shows empty state when no sources are ingested", async () => {
		mockGetResponses(emptyListResponse, emptyStatsResponse);
		render(<KnowledgePage />, { wrapper });

		await waitFor(() => {
			expect(screen.getByText("No sources yet")).toBeInTheDocument();
		});
	});

	it("shows loading spinner while fetching", () => {
		// Never resolve — keep loading state
		mockFetch.mockImplementation(() => new Promise(() => {}));
		render(<KnowledgePage />, { wrapper });
		expect(screen.getByText("Loading sources…")).toBeInTheDocument();
	});

	it("renders real stats from the API", async () => {
		mockGetResponses(populatedListResponse, statsResponse);
		render(<KnowledgePage />, { wrapper });

		await waitFor(() => {
			expect(screen.getByText("2")).toBeInTheDocument(); // document_count
			expect(screen.getByText("60")).toBeInTheDocument(); // chunk_count
		});
	});

	it("renders document list from the API", async () => {
		mockGetResponses(populatedListResponse, statsResponse);
		render(<KnowledgePage />, { wrapper });

		await waitFor(() => {
			expect(screen.getByText("monster-manual.pdf")).toBeInTheDocument();
			expect(screen.getByText("rulebook.txt")).toBeInTheDocument();
			expect(screen.getByText(/42 chunks/i)).toBeInTheDocument();
			expect(screen.getByText(/18 chunks/i)).toBeInTheDocument();
		});
	});

	it("shows chunk count singular correctly", async () => {
		mockGetResponses(
			{
				items: [
					{
						id: 3,
						source: "/docs/tiny.md",
						filename: "tiny.md",
						chunk_count: 1,
						status: "completed",
						progress: 100,
						current_step: "Done",
						started_at: null,
						last_indexed_at: null,
						error_message: null,
						features: [],
					},
				],
			},
			{ document_count: 1, chunk_count: 1 },
		);
		render(<KnowledgePage />, { wrapper });

		await waitFor(() => {
			expect(screen.getByText(/1 chunk/i)).toBeInTheDocument();
		});
	});

	it("handles file selection and success API call", async () => {
		mockOpenFile.mockResolvedValue("/path/to/test.txt");

		// GET responses (list + stats)
		mockGetResponses(emptyListResponse, emptyStatsResponse);

		// Delay the POST so we can see the "Selected" state
		mockFetch.mockImplementation(async (url: string, opts?: RequestInit) => {
			if (opts?.method === "POST") {
				await new Promise((resolve) => setTimeout(resolve, 100));
				return {
					ok: true,
					json: async () => ({
						task_id: "123",
						status: "pending",
						message: "Processing started",
					}),
				};
			}
			if (url.includes("/stats"))
				return { ok: true, json: async () => emptyStatsResponse };
			return { ok: true, json: async () => emptyListResponse };
		});

		render(<KnowledgePage />, { wrapper });

		const button = screen.getByRole("button", { name: "Select File" });
		fireEvent.click(button);

		await waitFor(() => {
			expect(mockOpenFile).toHaveBeenCalled();
		});

		await waitFor(() => {
			expect(screen.getByText("Selected:")).toBeInTheDocument();
			expect(screen.getByText("test.txt")).toBeInTheDocument();
		});

		await waitFor(() => {
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/v1/knowledge/",
				expect.objectContaining({
					method: "POST",
					body: JSON.stringify({ file_path: "/path/to/test.txt" }),
				}),
			);
		});

		await waitFor(() => {
			expect(
				screen.getByText(/Successfully queued for processing/),
			).toBeInTheDocument();
			expect(screen.getByText(/Task ID: 123/)).toBeInTheDocument();
		});
	});

	it("handles API error on upload", async () => {
		mockOpenFile.mockResolvedValue("/path/to/error.txt");
		mockGetResponses(emptyListResponse, emptyStatsResponse);

		mockFetch.mockImplementation(async (url: string, opts?: RequestInit) => {
			if (opts?.method === "POST") {
				return {
					ok: false,
					json: async () => ({ detail: "Something went wrong" }),
				};
			}
			if (url.includes("/stats"))
				return { ok: true, json: async () => emptyStatsResponse };
			return { ok: true, json: async () => emptyListResponse };
		});

		render(<KnowledgePage />, { wrapper });

		fireEvent.click(screen.getByRole("button", { name: "Select File" }));

		await waitFor(() => {
			expect(screen.getByText("Something went wrong")).toBeInTheDocument();
		});
	});

	it("shows error message when list fetch fails", async () => {
		mockFetch.mockImplementation(async () => ({
			ok: false,
			json: async () => ({}),
		}));
		render(<KnowledgePage />, { wrapper });

		await waitFor(() => {
			expect(
				screen.getByText("Failed to load knowledge sources."),
			).toBeInTheDocument();
		});
	});
});
