import { API_BASE_URL } from "../../config";

export interface Note {
	id: number;
	title: string;
	content: string;
	created_at: string;
	updated_at: string;
	tags: NoteTag[];
}

export interface NoteTag {
	id: number;
	tag: string;
	source_link?: string;
}

export interface NoteCreate {
	title: string;
	content: string;
}

export interface NoteUpdate {
	title?: string;
	content?: string;
}

export async function listNotes(): Promise<Note[]> {
	const response = await fetch(`${API_BASE_URL}/v1/notes/`);
	if (!response.ok) throw new Error("Failed to fetch notes");
	return response.json();
}

export async function getNote(id: number): Promise<Note> {
	const response = await fetch(`${API_BASE_URL}/v1/notes/${id}`);
	if (!response.ok) throw new Error("Failed to fetch note");
	return response.json();
}

export async function createNote(note: NoteCreate): Promise<Note> {
	const response = await fetch(`${API_BASE_URL}/v1/notes/`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(note),
	});
	if (!response.ok) throw new Error("Failed to create note");
	return response.json();
}

export async function updateNote(id: number, note: NoteUpdate): Promise<Note> {
	const response = await fetch(`${API_BASE_URL}/v1/notes/${id}`, {
		method: "PUT",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(note),
	});
	if (!response.ok) throw new Error("Failed to update note");
	return response.json();
}

export async function deleteNote(id: number): Promise<void> {
	const response = await fetch(`${API_BASE_URL}/v1/notes/${id}`, {
		method: "DELETE",
	});
	if (!response.ok) throw new Error("Failed to delete note");
}
