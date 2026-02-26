import { Tag } from "lucide-react";
import { type NoteTag } from "../../lib/api/notes";
import { GlassCard } from "../ui/GlassCard";

interface TagListProps {
	tags: NoteTag[];
}

export function TagList({ tags }: TagListProps) {
	if (tags.length === 0) {
		return (
			<GlassCard className="p-3 bg-white/20 dark:bg-white/5 flex items-center gap-2 text-muted-foreground text-xs italic">
				<Tag className="h-3 w-3" />
				Auto-tags will appear here...
			</GlassCard>
		);
	}

	return (
		<GlassCard className="p-3 bg-white/30 dark:bg-white/5 flex items-center gap-3 overflow-x-auto no-scrollbar">
			<Tag className="h-4 w-4 text-muted-foreground shrink-0" />
			<div className="flex gap-2">
				{tags.map((tag) => (
					<span
						key={tag.id}
						className="text-xs font-medium bg-primary/10 text-primary px-2.5 py-1 rounded-md whitespace-nowrap border border-primary/10"
						title={tag.source_link ? `Source: ${tag.source_link}` : undefined}
					>
						{tag.tag}
					</span>
				))}
			</div>
		</GlassCard>
	);
}
