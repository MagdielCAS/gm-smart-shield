import { API_BASE_URL } from "../../config";

export interface StreamChatOptions {
	query: string;
	onChunk: (chunk: string) => void;
	onComplete: () => void;
	onError: (error: Error) => void;
}

/**
 * Stream a chat response from the API.
 *
 * Uses the fetch API and ReadableStream to process chunks as they arrive.
 */
export async function streamChat({
	query,
	onChunk,
	onComplete,
	onError,
}: StreamChatOptions): Promise<void> {
	try {
		const response = await fetch(`${API_BASE_URL}/v1/chat/query`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ query }),
		});

		if (!response.ok) {
			throw new Error(`Chat API error: ${response.statusText}`);
		}

		if (!response.body) {
			throw new Error("No response body");
		}

		const reader = response.body.getReader();
		const decoder = new TextDecoder("utf-8");

		while (true) {
			const { done, value } = await reader.read();
			if (done) {
				break;
			}
			const chunk = decoder.decode(value, { stream: true });
			onChunk(chunk);
		}

		// Flush any remaining bytes
		const remaining = decoder.decode();
		if (remaining) {
			onChunk(remaining);
		}

		onComplete();
	} catch (err) {
		onError(err instanceof Error ? err : new Error(String(err)));
	}
}
