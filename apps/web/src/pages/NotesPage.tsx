import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FilePlus, Loader2 } from "lucide-react";
import { useState } from "react";
import { NoteEditor } from "../components/notes/NoteEditor";
import { NoteList } from "../components/notes/NoteList";
import {
	createNote,
	deleteNote,
	listNotes,
	type NoteUpdate,
	updateNote,
} from "../lib/api/notes";

const NotesPage = () => {
	const queryClient = useQueryClient();
	const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);

	const { data: notes = [], isLoading } = useQuery({
		queryKey: ["notes"],
		queryFn: listNotes,
		// Poll for tags updates
		refetchInterval: 3000,
	});

	const createMutation = useMutation({
		mutationFn: () => createNote({ title: "New Note", content: "" }),
		onSuccess: (newNote) => {
			queryClient.invalidateQueries({ queryKey: ["notes"] });
			setSelectedNoteId(newNote.id);
		},
	});

	const updateMutation = useMutation({
		mutationFn: ({ id, update }: { id: number; update: NoteUpdate }) =>
			updateNote(id, update),
		onSuccess: () => {
			// Invalidate to get new tags
			queryClient.invalidateQueries({ queryKey: ["notes"] });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: deleteNote,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["notes"] });
			// If deleted note was selected, deselect it
			// Note: logic is imperfect if deleting non-selected, but fine for now
			// Ideally check if deleted ID == selectedNoteId
		},
	});

	const selectedNote = notes.find((n) => n.id === selectedNoteId);

	const handleCreate = () => createMutation.mutate();
	const handleDelete = (id: number) => {
		if (window.confirm("Are you sure you want to delete this note?")) {
			deleteMutation.mutate(id);
			if (selectedNoteId === id) setSelectedNoteId(null);
		}
	};
	const handleUpdate = (id: number, update: NoteUpdate) => {
		updateMutation.mutate({ id, update });
	};

	if (isLoading && notes.length === 0) {
		return (
			<div className="flex h-full items-center justify-center">
				<Loader2 className="animate-spin text-muted-foreground" />
			</div>
		);
	}

	return (
		<div className="flex h-[calc(100vh-8rem)] gap-6">
			<div className="w-1/3 min-w-[250px] max-w-[350px]">
				<NoteList
					notes={notes}
					selectedId={selectedNoteId}
					onSelect={setSelectedNoteId}
					onCreate={handleCreate}
					onDelete={handleDelete}
				/>
			</div>
			<div className="flex-1 h-full min-w-0">
				{selectedNote ? (
					<NoteEditor
						note={selectedNote}
						onUpdate={handleUpdate}
						isSaving={updateMutation.isPending}
					/>
				) : (
					<div className="flex flex-col h-full items-center justify-center text-muted-foreground bg-white/10 dark:bg-white/5 rounded-2xl border border-white/10">
						<FilePlus className="h-12 w-12 mb-4 opacity-50" />
						<p>Select a note or create a new one.</p>
					</div>
				)}
			</div>
		</div>
	);
};

export default NotesPage;
