import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { API_BASE_URL } from "../../config";
import { GlassButton } from "../ui/GlassButton";
import { Modal } from "../ui/Modal";

interface Template {
	id: number;
	name: string;
	system: string;
	template_schema: unknown;
	source_id: number;
}

interface NewSheetModalProps {
	isOpen: boolean;
	onClose: () => void;
}

export function NewSheetModal({ isOpen, onClose }: NewSheetModalProps) {
	const [playerName, setPlayerName] = useState("");
	const [characterName, setCharacterName] = useState("");
	const [selectedTemplate, setSelectedTemplate] = useState<number | "">("");

	const queryClient = useQueryClient();

	const { data: templates = [], isLoading: templatesLoading } = useQuery<
		Template[]
	>({
		queryKey: ["templates"],
		queryFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/sheets/templates`);
			if (!res.ok) throw new Error("Failed to fetch templates");
			return res.json();
		},
		enabled: isOpen,
	});

	const { mutate: createSheet, isPending } = useMutation({
		mutationFn: async () => {
			if (!selectedTemplate) throw new Error("Select a template");
			const res = await fetch(`${API_BASE_URL}/v1/sheets`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					template_id: selectedTemplate,
					player_name: playerName,
					character_name: characterName,
					content: {},
					is_public: true,
				}),
			});
			if (!res.ok) throw new Error("Failed to create sheet");
			return res.json();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["sheets"] });
			onClose();
			setPlayerName("");
			setCharacterName("");
			setSelectedTemplate("");
		},
	});

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (!playerName || !characterName || !selectedTemplate) return;
		createSheet();
	};

	return (
		<Modal isOpen={isOpen} onClose={onClose} title="Create Character Sheet">
			<form onSubmit={handleSubmit} className="space-y-4">
				<div>
					<label
						htmlFor="playerName"
						className="block text-sm font-medium text-muted-foreground mb-1"
					>
						Player Name
					</label>
					<input
						name="playerName"
						type="text"
						value={playerName}
						onChange={(e) => setPlayerName(e.target.value)}
						required
						className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
						placeholder="E.g., John Doe"
					/>
				</div>
				<div>
					<label
						htmlFor="characterName"
						className="block text-sm font-medium text-muted-foreground mb-1"
					>
						Character Name
					</label>
					<input
						name="characterName"
						type="text"
						value={characterName}
						onChange={(e) => setCharacterName(e.target.value)}
						required
						className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
						placeholder="E.g., Gandalf"
					/>
				</div>
				<div>
					<label
						htmlFor="templateId"
						className="block text-sm font-medium text-muted-foreground mb-1"
					>
						Rulebook Template
					</label>
					{templatesLoading ? (
						<div className="flex items-center gap-2 text-sm text-muted-foreground">
							<Loader2 className="w-4 h-4 animate-spin" /> Loading templates...
						</div>
					) : (
						<select
							name="templateId"
							value={selectedTemplate}
							onChange={(e) => setSelectedTemplate(Number(e.target.value))}
							required
							className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all text-white appearance-none"
						>
							<option value="" disabled className="text-black">
								Select a template...
							</option>
							{templates.map((t) => (
								<option key={t.id} value={t.id} className="text-black">
									{t.name} ({t.system})
								</option>
							))}
						</select>
					)}
					<p className="text-xs text-muted-foreground mt-1">
						Templates are automatically extracted from your uploaded rulebooks.
					</p>
				</div>
				<div className="flex justify-end gap-2 pt-4 border-t border-white/10">
					<GlassButton type="button" variant="secondary" onClick={onClose}>
						Cancel
					</GlassButton>
					<GlassButton
						type="submit"
						disabled={
							isPending || !selectedTemplate || !playerName || !characterName
						}
					>
						{isPending ? (
							<Loader2 className="w-4 h-4 animate-spin" />
						) : (
							"Create Sheet"
						)}
					</GlassButton>
				</div>
			</form>
		</Modal>
	);
}
