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

const queryClient = new QueryClient({
	defaultOptions: {
		queries: { retry: false },
		mutations: { retry: false },
	},
});

describe("KnowledgePage", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		window.electron = {
			openFile: mockOpenFile,
		};
	});

	it("renders correctly", () => {
		render(
			<QueryClientProvider client={queryClient}>
				<KnowledgePage />
			</QueryClientProvider>,
		);
		expect(screen.getByText("Knowledge Base")).toBeInTheDocument();
		expect(screen.getByText("Add New Source")).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: "Select File" }),
		).toBeInTheDocument();
	});

	it("handles file selection and success API call", async () => {
		mockOpenFile.mockResolvedValue("/path/to/test.txt");

		// Add delay to ensure "Selected" state is visible before success
		mockFetch.mockImplementation(async () => {
			await new Promise((resolve) => setTimeout(resolve, 100));
			return {
				ok: true,
				json: async () => ({
					task_id: "123",
					status: "pending",
					message: "Processing started",
				}),
			};
		});

		render(
			<QueryClientProvider client={queryClient}>
				<KnowledgePage />
			</QueryClientProvider>,
		);

		const button = screen.getByRole("button", { name: "Select File" });
		fireEvent.click(button);

		await waitFor(() => {
			expect(mockOpenFile).toHaveBeenCalled();
		});

		// Check for selected file text
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

		// Check for success message
		await waitFor(() => {
			expect(
				screen.getByText(/Successfully queued for processing/),
			).toBeInTheDocument();
			expect(screen.getByText(/Task ID: 123/)).toBeInTheDocument();
		});
	});

	it("handles API error", async () => {
		mockOpenFile.mockResolvedValue("/path/to/error.txt");

		// Setup initial success fetch mock for the previous test contamination prevention
		mockFetch.mockResolvedValueOnce({
			ok: false,
			json: async () => ({ detail: "Something went wrong" }),
		});

		render(
			<QueryClientProvider client={queryClient}>
				<KnowledgePage />
			</QueryClientProvider>,
		);

		fireEvent.click(screen.getByRole("button", { name: "Select File" }));

		// We need to wait for the mutation to settle
		await waitFor(() => {
			// The error message is rendered inside a p tag without "Error:" prefix in the new UI
			expect(screen.getByText("Something went wrong")).toBeInTheDocument();
		});
	});
});
