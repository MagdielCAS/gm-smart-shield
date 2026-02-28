import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	Database,
	ExternalLink,
	Folder,
	Loader2,
	NotebookPen,
	RefreshCw,
	Settings,
	Tag,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
	getAppSettings,
	listNoteFolders,
	listNotes,
	syncVault,
	updateAppSettings,
} from "@/api/notes";
import { GlassButton } from "@/components/ui/GlassButton";
import { GlassCard } from "@/components/ui/GlassCard";

const SETTINGS_QUERY_KEY = ["app-settings"] as const;
const NOTES_QUERY_KEY = ["notes"] as const;
const FOLDERS_QUERY_KEY = ["note-folders"] as const;

function formatDate(value: string) {
	return new Intl.DateTimeFormat(undefined, {
		dateStyle: "medium",
		timeStyle: "short",
	}).format(new Date(value));
}

export default function NotesPage() {
	const queryClient = useQueryClient();
	const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);

	const settingsQuery = useQuery({
		queryKey: SETTINGS_QUERY_KEY,
		queryFn: getAppSettings,
	});

	const notesQuery = useQuery({
		queryKey: NOTES_QUERY_KEY,
		queryFn: listNotes,
	});

	const foldersQuery = useQuery({
		queryKey: FOLDERS_QUERY_KEY,
		queryFn: listNoteFolders,
	});

	const updateSettingsMutation = useMutation({
		mutationFn: updateAppSettings,
		onSuccess: async () => {
			await queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY });
		},
	});

	const syncVaultMutation = useMutation({
		mutationFn: syncVault,
		onSuccess: async () => {
			await queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
			await queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
		},
	});

	const notes = notesQuery.data ?? [];
	const folders = foldersQuery.data ?? [];
	const vaultPath = settingsQuery.data?.obsidian_vault_path;

	const handleSelectVault = async () => {
		// @ts-expect-error
		if (window.electron && window.electron.openDirectory) {
			// @ts-expect-error
			const path = await window.electron.openDirectory();
			if (path) {
				updateSettingsMutation.mutate({ obsidian_vault_path: path });
			}
		} else {
			alert("Directory selection is only supported in the desktop app.");
		}
	};

	const openInObsidian = () => {
		if (vaultPath) {
			// Open obsidian using custom protocol, or fallback
			// To ensure it opens, we'll try the vault name or path format.
			// In a real app we might need to properly URL encode this.
			const vaultName = vaultPath.split(/[/\\]/).pop();
			window.open(
				`obsidian://open?vault=${encodeURIComponent(vaultName || "")}`,
			);
		}
	};

	const stats = useMemo(() => {
		let tagsCount = 0;
		let linksCount = 0;

		for (const note of notes) {
			tagsCount += note.tags.length;
			if (note.frontmatter && (note.frontmatter as any).wiki_links) {
				linksCount += ((note.frontmatter as any).wiki_links as any[]).length;
			}
		}

		return {
			totalNotes: notes.length,
			totalPages: folders.length,
			tagsCount,
			linksCount,
		};
	}, [notes, folders]);

	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between gap-3">
				<div>
					<h1 className="text-2xl font-semibold">Obsidian Notes</h1>
					<p className="text-sm text-muted-foreground">
						Keep your knowledge base synced with your local Obsidian vault.
					</p>
				</div>
				<div className="flex items-center gap-3">
					{vaultPath && (
						<>
							<GlassButton onClick={openInObsidian} variant="secondary">
								<ExternalLink className="h-4 w-4" />
								Open Obsidian
							</GlassButton>
							<GlassButton
								onClick={() => syncVaultMutation.mutate()}
								disabled={syncVaultMutation.isPending}
							>
								{syncVaultMutation.isPending ? (
									<Loader2 className="h-4 w-4 animate-spin" />
								) : (
									<RefreshCw className="h-4 w-4" />
								)}
								Sync Vault
							</GlassButton>
						</>
					)}
				</div>
			</div>

			{!vaultPath ? (
				<GlassCard className="flex flex-col items-center justify-center p-12 text-center space-y-4">
					<Database className="h-12 w-12 text-primary/50" />
					<h2 className="text-xl font-semibold">No Vault Configured</h2>
					<p className="text-sm text-muted-foreground max-w-md">
						Connect your local Obsidian vault to automatically sync notes into
						your Knowledge Base for the AI assistant.
					</p>
					<GlassButton onClick={handleSelectVault} className="mt-4">
						<Folder className="h-4 w-4 mr-2" />
						Select Vault Folder
					</GlassButton>
				</GlassCard>
			) : (
				<div className="grid gap-4 lg:grid-cols-4">
					<GlassCard className="p-4 flex items-center justify-between">
						<div>
							<p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
								Total Notes
							</p>
							<p className="text-2xl font-bold mt-1">{stats.totalNotes}</p>
						</div>
						<NotebookPen className="h-8 w-8 text-primary/30" />
					</GlassCard>
					<GlassCard className="p-4 flex items-center justify-between">
						<div>
							<p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
								Total Folders
							</p>
							<p className="text-2xl font-bold mt-1">{stats.totalPages}</p>
						</div>
						<Folder className="h-8 w-8 text-primary/30" />
					</GlassCard>
					<GlassCard className="p-4 flex items-center justify-between">
						<div>
							<p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
								Total Tags
							</p>
							<p className="text-2xl font-bold mt-1">{stats.tagsCount}</p>
						</div>
						<Tag className="h-8 w-8 text-primary/30" />
					</GlassCard>
					<GlassCard className="p-4 flex items-center justify-between">
						<div>
							<p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
								Vault Path
							</p>
							<p
								className="text-xs font-mono mt-2 truncate w-32"
								title={vaultPath}
							>
								{vaultPath}
							</p>
						</div>
						<GlassButton size="sm" variant="ghost" onClick={handleSelectVault}>
							<Settings className="h-4 w-4 text-primary/50" />
						</GlassButton>
					</GlassCard>

					<div className="lg:col-span-1">
						<GlassCard className="space-y-4 p-4 h-full">
							<div>
								<h2 className="mb-3 text-sm font-semibold text-muted-foreground">
									Folders
								</h2>
								<div className="space-y-1">
									<button
										type="button"
										onClick={() => setSelectedFolderId(null)}
										className={`w-full rounded px-2 py-1 text-left text-xs ${selectedFolderId === null ? "bg-white/70 dark:bg-white/20" : "hover:bg-white/50 dark:hover:bg-white/10"}`}
									>
										All folders
									</button>
									{folders.map((folder) => (
										<button
											key={folder.id}
											type="button"
											onClick={() => setSelectedFolderId(folder.id)}
											className={`w-full rounded px-2 py-1 text-left text-xs ${selectedFolderId === folder.id ? "bg-white/70 dark:bg-white/20" : "hover:bg-white/50 dark:hover:bg-white/10"}`}
										>
											{folder.name}
										</button>
									))}
								</div>
							</div>
						</GlassCard>
					</div>

					<div className="lg:col-span-3">
						<GlassCard className="p-4 h-full">
							<h2 className="mb-3 text-sm font-semibold text-muted-foreground">
								Synced Notes
							</h2>
							{notesQuery.isLoading ? (
								<div className="flex items-center gap-2 text-sm text-muted-foreground">
									<Loader2 className="h-4 w-4 animate-spin" /> Loading notes…
								</div>
							) : (
								<div className="grid gap-3 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
									{notes
										.filter(
											(note) =>
												selectedFolderId === null ||
												note.folder_id === selectedFolderId,
										)
										.map((note) => (
											<div
												key={note.id}
												className="rounded-lg border border-white/30 bg-white/50 p-3 hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10 flex flex-col justify-between h-32"
											>
												<div>
													<p className="truncate text-sm font-semibold">
														{note.title}
													</p>
													<p className="text-xs text-muted-foreground mt-1 line-clamp-2">
														{note.content.substring(0, 100)}...
													</p>
												</div>
												<div className="flex items-center justify-between mt-2 pt-2 border-t border-white/20 dark:border-white/5">
													<div className="flex gap-1 overflow-hidden w-2/3">
														{note.tags.slice(0, 2).map((tag) => (
															<span
																key={tag}
																className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary truncate max-w-16"
															>
																#{tag}
															</span>
														))}
														{note.tags.length > 2 && (
															<span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
																+{note.tags.length - 2}
															</span>
														)}
													</div>
													<span className="text-[10px] text-muted-foreground">
														{formatDate(note.updated_at)}
													</span>
												</div>
											</div>
										))}
									{notes.length === 0 ? (
										<div className="col-span-full rounded-lg border border-dashed border-white/30 p-4 text-center text-sm text-muted-foreground">
											No notes found. Try syncing your vault.
										</div>
									) : null}
								</div>
							)}
						</GlassCard>
					</div>
				</div>
			)}
		</div>
	);
}
