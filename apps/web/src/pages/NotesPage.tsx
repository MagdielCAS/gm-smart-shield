import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	FolderPlus,
	Loader2,
	NotebookPen,
	Save,
	Sparkles,
	Tag,
} from "lucide-react";
import {
	type KeyboardEvent,
	type MouseEvent,
	type ReactElement,
	useMemo,
	useRef,
	useState,
} from "react";
import {
	createNote,
	createNoteFolder,
	listNoteFolders,
	listNotes,
	type Note,
	previewNoteTransform,
	suggestInlineText,
	type TransformAction,
	type TransformPreview,
	updateNote,
} from "@/api/notes";
import { GlassButton } from "@/components/ui/GlassButton";
import { GlassCard } from "@/components/ui/GlassCard";

const NOTES_QUERY_KEY = ["notes"] as const;
const FOLDERS_QUERY_KEY = ["note-folders"] as const;
const PHRASE_BOUNDARY_REGEX = /[.!?;:]$/;

const CONTEXT_ACTIONS: Array<{ label: string; action: TransformAction }> = [
	{ label: "Rewrite", action: "rewrite" },
	{ label: "Format", action: "format" },
	{ label: "Make it dramatic", action: "make_dramatic" },
	{ label: "Generate content", action: "generate_content" },
	{ label: "Add reference link", action: "add_reference_link" },
	{ label: "Search reference link", action: "search_reference_link" },
];

function parseInlineMarkdown(text: string) {
	const tokens = text
		.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g)
		.filter(Boolean);
	let cursor = 0;

	return tokens.map((token) => {
		const start = cursor;
		cursor += token.length;
		const key = `${token}-${start}`;
		if (token.startsWith("**") && token.endsWith("**")) {
			return <strong key={key}>{token.slice(2, -2)}</strong>;
		}
		if (token.startsWith("*") && token.endsWith("*")) {
			return <em key={key}>{token.slice(1, -1)}</em>;
		}
		if (token.startsWith("`") && token.endsWith("`")) {
			return (
				<code
					key={key}
					className="rounded bg-black/10 px-1 py-0.5 dark:bg-white/10"
				>
					{token.slice(1, -1)}
				</code>
			);
		}
		if (token.startsWith("[") && token.includes("](")) {
			const match = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
			if (match) {
				return (
					<a
						key={key}
						href={match[2]}
						className="text-primary underline"
						target="_blank"
						rel="noreferrer"
					>
						{match[1]}
					</a>
				);
			}
		}
		return <span key={key}>{token}</span>;
	});
}

function renderMarkdown(value: string) {
	const lines = value.split("\n");
	const blocks: ReactElement[] = [];
	let i = 0;
	let inCodeBlock = false;
	let codeLines: string[] = [];

	while (i < lines.length) {
		const line = lines[i];
		if (line.startsWith("```")) {
			if (!inCodeBlock) {
				inCodeBlock = true;
				codeLines = [];
			} else {
				blocks.push(
					<pre
						key={`code-${i}`}
						className="overflow-x-auto rounded bg-black/80 p-3 text-xs text-white"
					>
						<code>{codeLines.join("\n")}</code>
					</pre>,
				);
				inCodeBlock = false;
			}
			i += 1;
			continue;
		}
		if (inCodeBlock) {
			codeLines.push(line);
			i += 1;
			continue;
		}

		if (line.startsWith("|")) {
			const row = line
				.split("|")
				.map((cell) => cell.trim())
				.filter(Boolean);
			if (row.length) {
				blocks.push(
					<div key={`table-${i}`} className="overflow-x-auto">
						<table className="w-full border-collapse text-xs">
							<tbody>
								<tr>
									{row.map((cell) => (
										<td
											key={`${cell}-${i}`}
											className="border border-white/30 px-2 py-1"
										>
											{parseInlineMarkdown(cell)}
										</td>
									))}
								</tr>
							</tbody>
						</table>
					</div>,
				);
			}
			i += 1;
			continue;
		}

		if (line.startsWith("- ") || /^\d+\.\s/.test(line)) {
			const items: string[] = [];
			const ordered = /^\d+\.\s/.test(line);
			while (
				i < lines.length &&
				(ordered ? /^\d+\.\s/.test(lines[i]) : lines[i].startsWith("- "))
			) {
				items.push(lines[i].replace(ordered ? /^\d+\.\s/ : /^-\s/, ""));
				i += 1;
			}
			const ListTag = ordered ? "ol" : "ul";
			blocks.push(
				<ListTag
					key={`list-${i}`}
					className={ordered ? "list-decimal pl-6" : "list-disc pl-6"}
				>
					{items.map((item) => (
						<li key={`${item}-${i}`}>{parseInlineMarkdown(item)}</li>
					))}
				</ListTag>,
			);
			continue;
		}

		if (line.startsWith("> ")) {
			blocks.push(
				<blockquote
					key={`quote-${i}`}
					className="border-l-2 border-primary/40 pl-3 italic"
				>
					{parseInlineMarkdown(line.slice(2))}
				</blockquote>,
			);
			i += 1;
			continue;
		}

		if (line.startsWith("### ")) {
			blocks.push(
				<h3 key={`h3-${i}`} className="text-lg font-semibold">
					{parseInlineMarkdown(line.slice(4))}
				</h3>,
			);
		} else if (line.startsWith("## ")) {
			blocks.push(
				<h2 key={`h2-${i}`} className="text-xl font-semibold">
					{parseInlineMarkdown(line.slice(3))}
				</h2>,
			);
		} else if (line.startsWith("# ")) {
			blocks.push(
				<h1 key={`h1-${i}`} className="text-2xl font-semibold">
					{parseInlineMarkdown(line.slice(2))}
				</h1>,
			);
		} else if (!line.trim()) {
			blocks.push(<br key={`br-${i}`} />);
		} else {
			blocks.push(
				<p key={`p-${i}`} className="leading-relaxed">
					{parseInlineMarkdown(line)}
				</p>,
			);
		}
		i += 1;
	}

	return blocks;
}

function formatDate(value: string) {
	return new Intl.DateTimeFormat(undefined, {
		dateStyle: "medium",
		timeStyle: "short",
	}).format(new Date(value));
}

function applyPreview(content: string, preview: TransformPreview): string {
	if (preview.mode === "insert") {
		return `${content.slice(0, preview.selection_end)}${preview.preview_text}${content.slice(preview.selection_end)}`;
	}
	return `${content.slice(0, preview.selection_start)}${preview.preview_text}${content.slice(preview.selection_end)}`;
}

export default function NotesPage() {
	const queryClient = useQueryClient();
	const debounceRef = useRef<number | null>(null);
	const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
	const [draftTitle, setDraftTitle] = useState("Untitled note");
	const [draftContent, setDraftContent] = useState("# Session notes\n");
	const [newFolderName, setNewFolderName] = useState("");
	const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
	const [saveError, setSaveError] = useState<string | null>(null);
	const [ghostText, setGhostText] = useState("");
	const [preview, setPreview] = useState<TransformPreview | null>(null);
	const [previewError, setPreviewError] = useState<string | null>(null);
	const [menuState, setMenuState] = useState<{
		x: number;
		y: number;
		start: number;
		end: number;
	} | null>(null);

	const notesQuery = useQuery({
		queryKey: NOTES_QUERY_KEY,
		queryFn: listNotes,
	});

	const foldersQuery = useQuery({
		queryKey: FOLDERS_QUERY_KEY,
		queryFn: listNoteFolders,
	});

	const saveMutation = useMutation({
		mutationFn: async () => {
			const payload = {
				title: draftTitle.trim(),
				content: draftContent,
				folder_id: selectedFolderId,
				frontmatter: selectedNote?.frontmatter ?? null,
				tags: selectedNote?.tags ?? [],
				sources: selectedNote?.links ?? [],
			};
			if (selectedNoteId) {
				return updateNote(selectedNoteId, payload);
			}
			return createNote(payload);
		},
		onSuccess: async (savedNote) => {
			setSaveError(null);
			setSelectedNoteId(savedNote.id);
			setSelectedFolderId(savedNote.folder_id ?? null);
			await queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
		},
		onError: (error: Error) => {
			setSaveError(error.message);
		},
	});

	const folderMutation = useMutation({
		mutationFn: async () =>
			createNoteFolder({
				name: newFolderName.trim(),
			}),
		onSuccess: async (folder) => {
			setNewFolderName("");
			setSelectedFolderId(folder.id);
			await queryClient.invalidateQueries({ queryKey: FOLDERS_QUERY_KEY });
		},
	});

	const inlineMutation = useMutation({
		mutationFn: suggestInlineText,
		onSuccess: (data) => {
			setGhostText(data.suggestion);
		},
		onError: () => {
			setGhostText("");
		},
	});

	const transformMutation = useMutation({
		mutationFn: previewNoteTransform,
		onSuccess: (data) => {
			setPreview(data);
			setPreviewError(null);
			setMenuState(null);
		},
		onError: (error: Error) => {
			setPreviewError(error.message);
		},
	});

	const notes = notesQuery.data ?? [];
	const folders = foldersQuery.data ?? [];
	const selectedNote = useMemo(
		() => notes.find((note) => note.id === selectedNoteId) ?? null,
		[notes, selectedNoteId],
	);

	const requestSuggestion = (content: string, cursorIndex: number) => {
		inlineMutation.mutate({ content, cursor_index: cursorIndex });
	};

	const handleDraftChange = (value: string, cursorIndex: number) => {
		setDraftContent(value);
		setGhostText("");
		if (debounceRef.current) {
			window.clearTimeout(debounceRef.current);
		}
		const lastChar = value.slice(0, cursorIndex).slice(-1);
		if (lastChar === "\n" || PHRASE_BOUNDARY_REGEX.test(lastChar)) {
			requestSuggestion(value, cursorIndex);
			return;
		}
		debounceRef.current = window.setTimeout(() => {
			requestSuggestion(value, cursorIndex);
		}, 800);
	};

	const handleTabAccept = (event: KeyboardEvent<HTMLTextAreaElement>) => {
		if (event.key !== "Tab" || !ghostText) {
			return;
		}
		event.preventDefault();
		const target = event.currentTarget;
		const start = target.selectionStart;
		const end = target.selectionEnd;
		const next = `${draftContent.slice(0, start)}${ghostText}${draftContent.slice(end)}`;
		setDraftContent(next);
		setGhostText("");
	};

	const createNewDraft = () => {
		setSelectedNoteId(null);
		setDraftTitle("Untitled note");
		setDraftContent("# Session notes\n");
		setSelectedFolderId(null);
		setSaveError(null);
		setPreview(null);
		setPreviewError(null);
	};

	const selectNote = (note: Note) => {
		setSelectedNoteId(note.id);
		setDraftTitle(note.title);
		setDraftContent(note.content);
		setSelectedFolderId(note.folder_id ?? null);
		setSaveError(null);
		setPreview(null);
		setPreviewError(null);
	};

	const openContextMenu = (event: MouseEvent<HTMLTextAreaElement>) => {
		event.preventDefault();
		const target = event.currentTarget;
		setMenuState({
			x: event.clientX,
			y: event.clientY,
			start: target.selectionStart,
			end: target.selectionEnd,
		});
	};

	const runAction = (action: TransformAction) => {
		if (!menuState) {
			return;
		}
		transformMutation.mutate({
			action,
			content: draftContent,
			selection_start: menuState.start,
			selection_end: menuState.end,
		});
	};

	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between gap-3">
				<div>
					<h1 className="text-2xl font-semibold">Notes Workspace</h1>
					<p className="text-sm text-muted-foreground">
						Create and organize markdown notes with linked source context.
					</p>
				</div>
				<GlassButton onClick={createNewDraft} variant="secondary">
					<NotebookPen className="h-4 w-4" />
					New note
				</GlassButton>
			</div>

			<div className="grid gap-4 lg:grid-cols-[280px_1fr_1fr]">
				<GlassCard className="space-y-4 p-4">
					<div>
						<h2 className="mb-3 text-sm font-semibold text-muted-foreground">
							Folders
						</h2>
						<div className="flex gap-2">
							<input
								value={newFolderName}
								onChange={(event) => setNewFolderName(event.target.value)}
								placeholder="New folder"
								className="w-full rounded-lg border border-white/30 bg-white/70 px-2 py-1.5 text-xs outline-none ring-primary/40 focus:ring dark:border-white/10 dark:bg-white/10"
							/>
							<GlassButton
								aria-label="Create folder"
								type="button"
								onClick={() => folderMutation.mutate()}
								disabled={!newFolderName.trim() || folderMutation.isPending}
								variant="secondary"
							>
								<FolderPlus className="h-4 w-4" />
							</GlassButton>
						</div>
						<div className="mt-2 space-y-1">
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

					<div>
						<h2 className="mb-3 text-sm font-semibold text-muted-foreground">
							Notes
						</h2>
						{notesQuery.isLoading ? (
							<div className="flex items-center gap-2 text-sm text-muted-foreground">
								<Loader2 className="h-4 w-4 animate-spin" /> Loading notes…
							</div>
						) : (
							<ul className="space-y-2">
								{notes
									.filter(
										(note) =>
											selectedFolderId === null ||
											note.folder_id === selectedFolderId,
									)
									.map((note) => (
										<li key={note.id}>
											<button
												type="button"
												onClick={() => selectNote(note)}
												className="w-full rounded-lg border border-white/30 bg-white/50 p-2 text-left hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
											>
												<p className="truncate text-sm font-medium">
													{note.title}
												</p>
												<p className="text-xs text-muted-foreground">
													Updated {formatDate(note.updated_at)}
												</p>
											</button>
										</li>
									))}
								{notes.length === 0 ? (
									<li className="rounded-lg border border-dashed border-white/30 p-3 text-sm text-muted-foreground">
										No notes yet.
									</li>
								) : null}
							</ul>
						)}
					</div>
				</GlassCard>

				<GlassCard className="relative space-y-3 p-4">
					<div className="space-y-1">
						<label
							htmlFor="note-title"
							className="text-xs font-medium text-muted-foreground"
						>
							Title
						</label>
						<input
							id="note-title"
							value={draftTitle}
							onChange={(event) => setDraftTitle(event.target.value)}
							className="w-full rounded-lg border border-white/30 bg-white/70 px-3 py-2 text-sm outline-none ring-primary/40 focus:ring dark:border-white/10 dark:bg-white/10"
						/>
					</div>
					<div className="space-y-1">
						<label
							htmlFor="note-folder"
							className="text-xs font-medium text-muted-foreground"
						>
							Folder
						</label>
						<select
							id="note-folder"
							value={selectedFolderId ?? ""}
							onChange={(event) =>
								setSelectedFolderId(
									event.target.value ? Number(event.target.value) : null,
								)
							}
							className="w-full rounded-lg border border-white/30 bg-white/70 px-3 py-2 text-sm outline-none ring-primary/40 focus:ring dark:border-white/10 dark:bg-white/10"
						>
							<option value="">No folder</option>
							{folders.map((folder) => (
								<option key={folder.id} value={folder.id}>
									{folder.name}
								</option>
							))}
						</select>
					</div>
					<div className="space-y-1">
						<label
							htmlFor="note-markdown"
							className="text-xs font-medium text-muted-foreground"
						>
							Markdown
						</label>
						<textarea
							id="note-markdown"
							rows={18}
							value={draftContent}
							onChange={(event) =>
								handleDraftChange(
									event.target.value,
									event.target.selectionStart,
								)
							}
							onKeyDown={handleTabAccept}
							onContextMenu={openContextMenu}
							className="w-full rounded-lg border border-white/30 bg-white/70 px-3 py-2 text-sm outline-none ring-primary/40 focus:ring dark:border-white/10 dark:bg-white/10"
						/>
						{ghostText ? (
							<p className="text-xs text-muted-foreground">
								<Sparkles className="mr-1 inline h-3 w-3" />
								Ghost suggestion: <span className="font-mono">{ghostText}</span>{" "}
								(Tab to accept)
							</p>
						) : null}
					</div>
					{menuState ? (
						<div
							className="fixed z-50 w-52 rounded-lg border border-white/30 bg-background/95 p-1 shadow-xl"
							style={{ left: menuState.x, top: menuState.y }}
						>
							{CONTEXT_ACTIONS.map((item) => (
								<button
									key={item.action}
									type="button"
									className="w-full rounded px-2 py-1 text-left text-sm hover:bg-accent"
									onClick={() => runAction(item.action)}
								>
									{item.label}
								</button>
							))}
						</div>
					) : null}
					{preview ? (
						<div className="space-y-2 rounded-lg border border-white/30 bg-white/60 p-3 text-xs dark:border-white/10 dark:bg-white/5">
							<p className="font-medium">Preview: {preview.action}</p>
							<p className="text-muted-foreground">{preview.preview_text}</p>
							<div className="flex gap-2">
								<GlassButton
									type="button"
									variant="secondary"
									onClick={() => setPreview(null)}
								>
									Dismiss
								</GlassButton>
								<GlassButton
									type="button"
									onClick={() => {
										setDraftContent(applyPreview(draftContent, preview));
										setPreview(null);
									}}
								>
									Apply to draft
								</GlassButton>
							</div>
						</div>
					) : null}
					{previewError ? (
						<p className="text-xs text-red-500">{previewError}</p>
					) : null}
					<div className="flex items-center gap-3">
						<GlassButton
							onClick={() => saveMutation.mutate()}
							disabled={saveMutation.isPending || !draftTitle.trim()}
						>
							{saveMutation.isPending ? (
								<Loader2 className="h-4 w-4 animate-spin" />
							) : (
								<Save className="h-4 w-4" />
							)}
							Save note
						</GlassButton>
						{saveError ? (
							<p className="text-xs text-red-500">{saveError}</p>
						) : null}
					</div>
				</GlassCard>

				<GlassCard className="space-y-4 p-4">
					<h2 className="text-sm font-semibold text-muted-foreground">
						Preview & Details
					</h2>
					<div className="min-h-52 space-y-2 rounded-lg border border-white/20 bg-white/60 p-3 text-sm dark:border-white/10 dark:bg-white/5">
						{renderMarkdown(draftContent)}
					</div>

					<div className="space-y-2 text-xs text-muted-foreground">
						<p>
							Created:{" "}
							{selectedNote ? formatDate(selectedNote.created_at) : "Not saved"}
						</p>
						<p>
							Updated:{" "}
							{selectedNote ? formatDate(selectedNote.updated_at) : "Not saved"}
						</p>
					</div>

					<div className="space-y-2">
						<p className="text-xs font-medium text-muted-foreground">
							Extracted Tags
						</p>
						<div className="flex flex-wrap gap-2">
							{selectedNote?.tags.length ? (
								selectedNote.tags.map((tag) => (
									<span
										key={tag}
										className="inline-flex items-center gap-1 rounded-full border border-white/30 bg-white/70 px-2 py-1 text-xs dark:border-white/10 dark:bg-white/10"
									>
										<Tag className="h-3 w-3" /> {tag}
									</span>
								))
							) : (
								<span className="text-xs text-muted-foreground">
									No tags extracted yet.
								</span>
							)}
						</div>
					</div>

					<div className="space-y-2">
						<p className="text-xs font-medium text-muted-foreground">
							Linked Sources
						</p>
						<ul className="space-y-2 text-xs">
							{selectedNote?.links.length ? (
								selectedNote.links.map((link, index) => (
									<li
										key={`${link.chunk_id ?? link.source_file ?? "source"}-${index}`}
										className="rounded-lg border border-white/30 bg-white/60 p-2 dark:border-white/10 dark:bg-white/5"
									>
										<p>
											{link.source_file ?? link.source_id ?? "Unknown source"}
										</p>
										<p className="text-muted-foreground">
											{link.page_number
												? `Page ${link.page_number}`
												: "No page"}
											{link.chunk_id ? ` • Chunk ${link.chunk_id}` : ""}
										</p>
									</li>
								))
							) : (
								<li className="text-muted-foreground">No linked sources.</li>
							)}
						</ul>
					</div>
				</GlassCard>
			</div>
		</div>
	);
}
