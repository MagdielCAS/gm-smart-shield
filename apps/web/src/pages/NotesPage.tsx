import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, NotebookPen, Save, Tag } from "lucide-react";
import { Fragment, type ReactNode, useMemo, useState } from "react";
import { createNote, listNotes, type Note, updateNote } from "@/api/notes";
import { GlassButton } from "@/components/ui/GlassButton";
import { GlassCard } from "@/components/ui/GlassCard";

const NOTES_QUERY_KEY = ["notes"] as const;

function parseInlineMarkdown(text: string): ReactNode[] {
	const tokens = text
		.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g)
		.filter(Boolean);
	let cursor = 0;

	return tokens.map((token) => {
		const tokenStart = cursor;
		cursor += token.length;
		if (token.startsWith("**") && token.endsWith("**")) {
			return (
				<strong key={`${token}-${tokenStart}`}>{token.slice(2, -2)}</strong>
			);
		}
		if (token.startsWith("*") && token.endsWith("*")) {
			return <em key={`${token}-${tokenStart}`}>{token.slice(1, -1)}</em>;
		}
		if (token.startsWith("`") && token.endsWith("`")) {
			return (
				<code
					key={`${token}-${tokenStart}`}
					className="rounded bg-black/10 px-1 py-0.5 dark:bg-white/10"
				>
					{token.slice(1, -1)}
				</code>
			);
		}
		return <Fragment key={`${token}-${tokenStart}`}>{token}</Fragment>;
	});
}

function renderMarkdown(value: string) {
	const lines = value.split("\n");

	let offset = 0;

	return lines.map((line) => {
		const lineOffset = offset;
		offset += line.length + 1;
		if (line.startsWith("### ")) {
			return (
				<h3 key={`${line}-${lineOffset}`} className="text-lg font-semibold">
					{parseInlineMarkdown(line.slice(4))}
				</h3>
			);
		}
		if (line.startsWith("## ")) {
			return (
				<h2 key={`${line}-${lineOffset}`} className="text-xl font-semibold">
					{parseInlineMarkdown(line.slice(3))}
				</h2>
			);
		}
		if (line.startsWith("# ")) {
			return (
				<h1 key={`${line}-${lineOffset}`} className="text-2xl font-semibold">
					{parseInlineMarkdown(line.slice(2))}
				</h1>
			);
		}
		if (!line.trim()) {
			return <br key={`break-${lineOffset}`} />;
		}

		return (
			<p key={`${line}-${lineOffset}`} className="leading-relaxed">
				{parseInlineMarkdown(line)}
			</p>
		);
	});
}

function formatDate(value: string) {
	return new Intl.DateTimeFormat(undefined, {
		dateStyle: "medium",
		timeStyle: "short",
	}).format(new Date(value));
}

export default function NotesPage() {
	const queryClient = useQueryClient();
	const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
	const [draftTitle, setDraftTitle] = useState("Untitled note");
	const [draftContent, setDraftContent] = useState("# Session notes\n");
	const [saveError, setSaveError] = useState<string | null>(null);

	const notesQuery = useQuery({
		queryKey: NOTES_QUERY_KEY,
		queryFn: listNotes,
	});

	const saveMutation = useMutation({
		mutationFn: async () => {
			const payload = {
				title: draftTitle.trim(),
				content: draftContent,
				folder_id: selectedNote?.folder_id ?? null,
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
			await queryClient.invalidateQueries({ queryKey: NOTES_QUERY_KEY });
		},
		onError: (error: Error) => {
			setSaveError(error.message);
		},
	});

	const notes = notesQuery.data ?? [];
	const selectedNote = useMemo(
		() => notes.find((note) => note.id === selectedNoteId) ?? null,
		[notes, selectedNoteId],
	);

	const selectNote = (note: Note) => {
		setSelectedNoteId(note.id);
		setDraftTitle(note.title);
		setDraftContent(note.content);
		setSaveError(null);
	};

	const createNewDraft = () => {
		setSelectedNoteId(null);
		setDraftTitle("Untitled note");
		setDraftContent("# Session notes\n");
		setSaveError(null);
	};

	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between gap-4">
				<div>
					<h1 className="text-2xl font-semibold tracking-tight">
						Campaign Notes
					</h1>
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
				<GlassCard className="p-4">
					<h2 className="mb-3 text-sm font-semibold text-muted-foreground">
						Notes
					</h2>
					{notesQuery.isLoading ? (
						<div className="flex items-center gap-2 text-sm text-muted-foreground">
							<Loader2 className="h-4 w-4 animate-spin" /> Loading notes…
						</div>
					) : (
						<ul className="space-y-2">
							{notes.map((note) => (
								<li key={note.id}>
									<button
										type="button"
										onClick={() => selectNote(note)}
										className="w-full rounded-lg border border-white/30 bg-white/50 p-2 text-left hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
									>
										<p className="truncate text-sm font-medium">{note.title}</p>
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
				</GlassCard>

				<GlassCard className="space-y-3 p-4">
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
							htmlFor="note-markdown"
							className="text-xs font-medium text-muted-foreground"
						>
							Markdown
						</label>
						<textarea
							id="note-markdown"
							rows={18}
							value={draftContent}
							onChange={(event) => setDraftContent(event.target.value)}
							className="w-full rounded-lg border border-white/30 bg-white/70 px-3 py-2 text-sm outline-none ring-primary/40 focus:ring dark:border-white/10 dark:bg-white/10"
						/>
					</div>
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
