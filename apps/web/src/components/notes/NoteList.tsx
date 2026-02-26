import { Plus, Trash2 } from "lucide-react";
import type { Note } from "../../lib/api/notes";
import { cn } from "../../lib/utils";
import { GlassButton } from "../ui/GlassButton";
import { GlassCard } from "../ui/GlassCard";

interface NoteListProps {
	notes: Note[];
	selectedId: number | null;
	onSelect: (id: number) => void;
	onCreate: () => void;
	onDelete: (id: number) => void;
}

export function NoteList({
	notes,
	selectedId,
	onSelect,
	onCreate,
	onDelete,
}: NoteListProps) {
	return (
		<div className="flex flex-col h-full bg-white/20 dark:bg-white/5 rounded-2xl overflow-hidden border border-white/10">
			<div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/30 dark:bg-white/5 backdrop-blur-md">
				<h3 className="font-semibold">Notes</h3>
				<GlassButton size="sm" onClick={onCreate}>
					<Plus className="h-4 w-4 mr-1" /> New
				</GlassButton>
			</div>
			<div className="flex-1 overflow-y-auto p-2 space-y-2">
				{notes.map((note) => (
					<GlassCard
						key={note.id}
						onClick={() => onSelect(note.id)}
						className={cn(
							"p-3 cursor-pointer transition-all hover:bg-white/40 dark:hover:bg-white/10 flex justify-between items-start group",
							selectedId === note.id
								? "bg-white/60 dark:bg-white/20 border-primary/50 ring-1 ring-primary/20"
								: "bg-transparent border-transparent",
						)}
					>
						<div className="flex-1 min-w-0">
							<h4
								className={cn(
									"font-medium truncate",
									!note.title && "text-muted-foreground italic",
								)}
							>
								{note.title || "Untitled"}
							</h4>
							<p className="text-xs text-muted-foreground truncate mt-1">
								{note.content || "No content"}
							</p>
							{note.tags.length > 0 && (
								<div className="flex gap-1 mt-2 flex-wrap">
									{note.tags.slice(0, 3).map((tag) => (
										<span
											key={tag.id}
											className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full truncate max-w-[100px]"
										>
											{tag.tag}
										</span>
									))}
									{note.tags.length > 3 && (
										<span className="text-[10px] text-muted-foreground">
											+{note.tags.length - 3}
										</span>
									)}
								</div>
							)}
						</div>
						<button
							type="button"
							onClick={(e) => {
								e.stopPropagation();
								onDelete(note.id);
							}}
							className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-destructive/10 text-destructive rounded-lg transition-all"
						>
							<Trash2 className="h-4 w-4" />
						</button>
					</GlassCard>
				))}
				{notes.length === 0 && (
					<div className="text-center p-8 text-muted-foreground text-sm">
						No notes found. Create one!
					</div>
				)}
			</div>
		</div>
	);
}
