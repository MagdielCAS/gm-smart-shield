import { useEffect, useState } from "react";
import { type Note, type NoteUpdate } from "../../lib/api/notes";
import { GlassCard } from "../ui/GlassCard";
import { TagList } from "./TagList";

interface NoteEditorProps {
	note: Note;
	onUpdate: (id: number, update: NoteUpdate) => void;
	isSaving: boolean;
}

export function NoteEditor({ note, onUpdate, isSaving }: NoteEditorProps) {
	const [title, setTitle] = useState(note.title);
	const [content, setContent] = useState(note.content);

	// Sync state when note selection changes
	// biome-ignore lint/correctness/useExhaustiveDependencies: Reset form on note switch
	useEffect(() => {
		setTitle(note.title);
		setContent(note.content);
	}, [note.id]);

	// Debounced save
	useEffect(() => {
		// Avoid saving if values haven't changed (initial render or sync)
		if (title === note.title && content === note.content) {
			return;
		}

		const timer = setTimeout(() => {
			onUpdate(note.id, { title, content });
		}, 1000);

		return () => clearTimeout(timer);
	}, [title, content, note.id, note.title, note.content, onUpdate]);

	return (
		<div className="flex flex-col h-full space-y-4">
			<GlassCard className="p-6 bg-white/40 dark:bg-white/5 flex-1 flex flex-col">
				<input
					value={title}
					onChange={(e) => setTitle(e.target.value)}
					placeholder="Note Title"
					className="text-2xl font-bold bg-transparent border-none focus:outline-none mb-4 placeholder:text-muted-foreground/50 w-full"
				/>
				<div className="flex-1 relative">
					<textarea
						value={content}
						onChange={(e) => setContent(e.target.value)}
						placeholder="Start typing..."
						className="w-full h-full bg-transparent border-none resize-none focus:outline-none leading-relaxed text-base"
					/>
					{isSaving && (
						<div className="absolute bottom-2 right-2 text-xs text-muted-foreground animate-pulse bg-background/50 px-2 py-1 rounded">
							Saving...
						</div>
					)}
				</div>
			</GlassCard>

			<TagList tags={note.tags} />
		</div>
	);
}
