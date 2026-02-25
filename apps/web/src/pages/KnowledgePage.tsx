import { useMutation } from "@tanstack/react-query";
import {
	AlertCircle,
	CheckCircle2,
	Database,
	FileText,
	Loader2,
	UploadCloud,
} from "lucide-react";
import { useState } from "react";
import { GlassButton } from "@/components/ui/GlassButton";
import { GlassCard } from "@/components/ui/GlassCard";
import { SFIcon } from "@/components/ui/SFIcon";
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
		<div className="space-y-8">
			{/* Header Section */}
			<div className="flex items-end justify-between">
				<div>
					<h2 className="text-3xl font-bold tracking-tight">Knowledge Base</h2>
					<p className="mt-2 text-muted-foreground max-w-lg">
						Manage your game master resources. Add documents, rules, and notes
						to feed the AI assistant.
					</p>
				</div>
				<GlassButton variant="secondary" size="sm" className="hidden sm:flex">
					<SFIcon icon={Database} className="mr-2 h-4 w-4" />
					View All Data
				</GlassButton>
			</div>

			{/* Main Grid */}
			<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				{/* Add Source Card */}
				<GlassCard className="col-span-full lg:col-span-2 relative overflow-hidden group">
					<div className="absolute top-0 right-0 -mt-10 -mr-10 h-64 w-64 rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 blur-3xl group-hover:bg-primary/30 transition-all duration-700"></div>

					<div className="relative z-10">
						<div className="mb-6 flex items-center gap-3">
							<div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/50 shadow-inner">
								<SFIcon icon={UploadCloud} className="h-5 w-5 text-primary" />
							</div>
							<h3 className="text-xl font-semibold">Add New Source</h3>
						</div>

						<p className="mb-8 text-muted-foreground">
							Select a local file to ingest. Supported formats:{" "}
							<span className="font-medium text-foreground">
								PDF, TXT, MD, CSV
							</span>
							. The file will be processed locally and added to the vector
							database.
						</p>

						<div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
							<GlassButton
								onClick={handleSelectFile}
								disabled={mutation.isPending}
								size="lg"
								className="w-full sm:w-auto"
							>
								{mutation.isPending ? (
									<>
										<Loader2 className="mr-2 h-4 w-4 animate-spin" />
										Processing...
									</>
								) : (
									<>
										<SFIcon icon={FileText} className="mr-2 h-4 w-4" />
										Select File
									</>
								)}
							</GlassButton>

							{selectedFile && !mutation.isError && !mutation.isSuccess && (
								<span className="text-sm text-muted-foreground animate-in fade-in slide-in-from-left-2">
									Selected:{" "}
									<span className="font-mono text-xs bg-black/5 px-2 py-1 rounded-md ml-1">
										{selectedFile.split(/[/\\]/).pop()}
									</span>
								</span>
							)}
						</div>

						{/* Status Messages */}
						<div className="mt-6 space-y-3">
							{mutation.isError && (
								<div className="flex items-center gap-3 rounded-xl bg-destructive/10 p-4 text-destructive border border-destructive/20 animate-in zoom-in-95">
									<AlertCircle className="h-5 w-5 shrink-0" />
									<p className="text-sm font-medium">
										{mutation.error.message}
									</p>
								</div>
							)}

							{mutation.isSuccess && (
								<div className="flex items-center gap-3 rounded-xl bg-green-500/10 p-4 text-green-700 border border-green-500/20 animate-in zoom-in-95">
									<CheckCircle2 className="h-5 w-5 shrink-0" />
									<div className="space-y-1">
										<p className="text-sm font-medium">
											Successfully queued for processing
										</p>
										<p className="text-xs opacity-80 font-mono">
											Task ID: {mutation.data.task_id}
										</p>
									</div>
								</div>
							)}
						</div>
					</div>
				</GlassCard>

				{/* Placeholder for Stats or Recent */}
				<GlassCard className="flex flex-col justify-between bg-white/40">
					<div>
						<h3 className="text-lg font-semibold mb-2">Quick Stats</h3>
						<div className="space-y-4 mt-6">
							<div className="flex justify-between items-center pb-2 border-b border-black/5">
								<span className="text-sm text-muted-foreground">Documents</span>
								<span className="font-mono font-medium">12</span>
							</div>
							<div className="flex justify-between items-center pb-2 border-b border-black/5">
								<span className="text-sm text-muted-foreground">
									Vector Chunks
								</span>
								<span className="font-mono font-medium">1,420</span>
							</div>
							<div className="flex justify-between items-center pb-2 border-b border-black/5">
								<span className="text-sm text-muted-foreground">Storage</span>
								<span className="font-mono font-medium">4.2 MB</span>
							</div>
						</div>
					</div>
					<div className="mt-6 pt-4 text-xs text-center text-muted-foreground">
						Local Database Active
					</div>
				</GlassCard>
			</div>

			{/* Recent Files List (Mockup) */}
			<div className="mt-10">
				<h3 className="text-lg font-semibold mb-4 px-1">Recent Sources</h3>
				<div className="rounded-3xl border border-white/20 bg-white/30 backdrop-blur-md overflow-hidden">
					<div className="grid grid-cols-1 divide-y divide-white/10">
						{[1, 2, 3].map((i) => (
							<div
								key={i}
								className="group flex items-center justify-between p-4 hover:bg-white/40 transition-colors cursor-default"
							>
								<div className="flex items-center gap-4">
									<div className="h-10 w-10 rounded-lg bg-white/60 flex items-center justify-center text-muted-foreground group-hover:text-primary transition-colors">
										<SFIcon icon={FileText} className="h-5 w-5" />
									</div>
									<div>
										<p className="font-medium">Rulebook_Core_v{i}.pdf</p>
										<p className="text-xs text-muted-foreground">
											Added 2 hours ago • 2.4 MB
										</p>
									</div>
								</div>
								<div className="flex items-center gap-2">
									<span className="inline-flex items-center rounded-full bg-green-500/10 px-2.5 py-0.5 text-xs font-medium text-green-700">
										Indexed
									</span>
								</div>
							</div>
						))}
					</div>
				</div>
			</div>
		</div>
	);
};

export default KnowledgePage;
