import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { API_BASE_URL } from "../config";

interface KnowledgeSourceCreate {
	file_path: string;
	description?: string;
}

interface KnowledgeSourceResponse {
	task_id: string;
	status: string;
	message: string;
}

const KnowledgePage = () => {
	const [selectedFile, setSelectedFile] = useState<string | null>(null);

	const mutation = useMutation<
		KnowledgeSourceResponse,
		Error,
		KnowledgeSourceCreate
	>({
		mutationFn: async (newSource) => {
			const response = await fetch(`${API_BASE_URL}/v1/knowledge/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(newSource),
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || "Failed to add source");
			}

			return response.json();
		},
	});

	const handleSelectFile = async () => {
		if (!window.electron) {
			alert(
				"Electron API is not available. This feature works only in the Electron app.",
			);
			return;
		}

		try {
			const filePath = await window.electron.openFile();
			if (filePath) {
				setSelectedFile(filePath);
				mutation.mutate({ file_path: filePath });
			}
		} catch (error) {
			console.error("Failed to open file:", error);
		}
	};

	return (
		<div className="container mx-auto p-4">
			<h1 className="text-2xl font-bold mb-4">Knowledge Base</h1>

			<div className="mb-8 p-4 border rounded shadow-sm bg-white">
				<h2 className="text-xl mb-2">Add New Source</h2>
				<p className="text-gray-600 mb-4">
					Select a local file (PDF, TXT, MD, CSV) to add to the knowledge base.
				</p>

				<button
					type="button"
					onClick={handleSelectFile}
					disabled={mutation.isPending}
					className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
				>
					{mutation.isPending ? "Processing..." : "Select File"}
				</button>

				{selectedFile && (
					<div className="mt-2 text-sm text-gray-500">
						Selected: {selectedFile}
					</div>
				)}

				{mutation.isError && (
					<div className="mt-4 p-2 bg-red-100 text-red-700 rounded">
						Error: {mutation.error.message}
					</div>
				)}

				{mutation.isSuccess && (
					<div className="mt-4 p-2 bg-green-100 text-green-700 rounded">
						Success! Task ID: {mutation.data.task_id}
						<br />
						{mutation.data.message}
					</div>
				)}
			</div>
		</div>
	);
};

export default KnowledgePage;
