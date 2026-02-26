export type NoteLinkMetadata = {
	source_id: string | null;
	source_file: string | null;
	page_number: number | null;
	chunk_id: string | null;
};

export type Note = {
	id: number;
	title: string;
	content: string;
	frontmatter: Record<string, unknown> | null;
	metadata: Record<string, unknown>;
	folder_id: number | null;
	created_at: string;
	updated_at: string;
	tags: string[];
	links: NoteLinkMetadata[];
};

export type NotePayload = {
	title: string;
	content: string;
	tags?: string[];
	campaign_id?: string | null;
	session_id?: string | null;
	folder_id?: number | null;
	frontmatter?: Record<string, unknown> | null;
	sources?: NoteLinkMetadata[];
};

type NoteListResponse = { items: Note[] };

async function parseJsonOrThrow<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error = await response.json().catch(() => ({}));
		throw new Error(error.detail ?? "Request failed");
	}
	return response.json() as Promise<T>;
}

export async function listNotes(): Promise<Note[]> {
	const response = await fetch("/api/v1/notes");
	const data = await parseJsonOrThrow<NoteListResponse>(response);
	return data.items;
}

export async function getNote(noteId: number): Promise<Note> {
	const response = await fetch(`/api/v1/notes/${noteId}`);
	return parseJsonOrThrow<Note>(response);
}

export async function createNote(payload: NotePayload): Promise<Note> {
	const response = await fetch("/api/v1/notes", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	return parseJsonOrThrow<Note>(response);
}

export async function updateNote(
	noteId: number,
	payload: NotePayload,
): Promise<Note> {
	const response = await fetch(`/api/v1/notes/${noteId}`, {
		method: "PUT",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	return parseJsonOrThrow<Note>(response);
}

export async function deleteNote(noteId: number): Promise<void> {
	const response = await fetch(`/api/v1/notes/${noteId}`, { method: "DELETE" });
	if (!response.ok) {
		const error = await response.json().catch(() => ({}));
		throw new Error(error.detail ?? "Failed to delete note");
	}
}
