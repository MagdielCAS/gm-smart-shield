export type NoteLinkMetadata = {
	source_id: string | null;
	source_file: string | null;
	page_number: number | null;
	chunk_id: string | null;
};

export type NoteFolder = {
	id: number;
	name: string;
	parent_id: number | null;
};

export type NoteFolderPayload = {
	name: string;
	parent_id?: number | null;
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

export type InlineSuggestionPayload = {
	content: string;
	cursor_index: number;
};

export type InlineSuggestionResponse = {
	suggestion: string;
	reason: "punctuation" | "newline" | "idle" | "none";
};

export type TransformAction =
	| "rewrite"
	| "format"
	| "make_dramatic"
	| "generate_content"
	| "add_reference_link"
	| "search_reference_link";

export type TransformPayload = {
	action: TransformAction;
	content: string;
	selection_start: number;
	selection_end: number;
};

export type TransformPreview = {
	action: TransformAction;
	original_text: string;
	preview_text: string;
	selection_start: number;
	selection_end: number;
	mode: "replace" | "insert";
};

type NoteListResponse = { items: Note[] };
type NoteFolderListResponse = { items: NoteFolder[] };

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

export async function suggestInlineText(
	payload: InlineSuggestionPayload,
): Promise<InlineSuggestionResponse> {
	const response = await fetch("/api/v1/notes/inline-suggest", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	return parseJsonOrThrow<InlineSuggestionResponse>(response);
}

export async function previewNoteTransform(
	payload: TransformPayload,
): Promise<TransformPreview> {
	const response = await fetch("/api/v1/notes/transform/preview", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	return parseJsonOrThrow<TransformPreview>(response);
}

export async function listNoteFolders(): Promise<NoteFolder[]> {
	const response = await fetch("/api/v1/notes/folders");
	const data = await parseJsonOrThrow<NoteFolderListResponse>(response);
	return data.items;
}

export async function createNoteFolder(
	payload: NoteFolderPayload,
): Promise<NoteFolder> {
	const response = await fetch("/api/v1/notes/folders", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	return parseJsonOrThrow<NoteFolder>(response);
}
