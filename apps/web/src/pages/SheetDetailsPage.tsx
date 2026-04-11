import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
	ArrowLeft,
	ExternalLink,
	Loader2,
	PlusCircle,
	Save,
	Search,
	Trash2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { GlassButton } from "../components/ui/GlassButton";
import { GlassCard } from "../components/ui/GlassCard";
import { API_BASE_URL } from "../config";

interface CharacterSheet {
	id: string;
	player_name: string;
	character_name: string;
	template_id: number;
	content: Record<string, unknown>;
	is_public: boolean;
}

interface QuickReference {
	id: number;
	name: string;
	category: string;
	description: string;
	tags?: string[];
	source_page?: number;
	source_section?: string;
}

const SheetDetailsPage = () => {
	const { id } = useParams();
	const navigate = useNavigate();
	const queryClient = useQueryClient();

	const [sheetContent, setSheetContent] = useState<string>("");
	const [referenceCategory, setReferenceCategory] = useState("Spell");
	const [referenceSearch, setReferenceSearch] = useState("");

	const { data: sheet, isLoading: sheetLoading } = useQuery<CharacterSheet>({
		queryKey: ["sheet", id],
		queryFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/sheets/${id}`);
			if (!res.ok) throw new Error("Failed to fetch sheet");
			return res.json();
		},
	});

	const { data: references = [], isLoading: referencesLoading } = useQuery<
		QuickReference[]
	>({
		queryKey: ["references", referenceCategory],
		queryFn: async () => {
			const url = new URL(`${API_BASE_URL}/v1/knowledge/references`);
			if (referenceCategory) {
				url.searchParams.append("category", referenceCategory);
			}
			const res = await fetch(url.toString());
			if (!res.ok) throw new Error("Failed to fetch references");
			return res.json();
		},
	});

	useEffect(() => {
		if (sheet && !sheetContent) {
			setSheetContent(JSON.stringify(sheet.content, null, 2));
		}
	}, [sheet, sheetContent]);

	const { mutate: saveSheet, isPending: saving } = useMutation({
		mutationFn: async () => {
			let parsedContent = {};
			try {
				parsedContent = JSON.parse(sheetContent);
			} catch (_e) {
				throw new Error("Invalid JSON content");
			}

			const res = await fetch(`${API_BASE_URL}/v1/sheets/${id}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					content: parsedContent,
				}),
			});
			if (!res.ok) throw new Error("Failed to save sheet");
			return res.json();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["sheet", id] });
			alert("Sheet saved successfully!");
		},
		onError: (err) => {
			if (err instanceof Error) {
				alert(err.message);
			} else {
				alert(String(err));
			}
		},
	});

	const { mutate: deleteSheet, isPending: deleting } = useMutation({
		mutationFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/sheets/${id}`, {
				method: "DELETE",
			});
			if (!res.ok) throw new Error("Failed to delete sheet");
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["sheets"] });
			navigate("/sheets");
		},
	});

	const handleAddReference = (ref: QuickReference) => {
		try {
			const currentContent = JSON.parse(sheetContent);
			// Simple heuristics to attach it to an existing array or create a generic 'inventory'
			const targetKey = ref.category.toLowerCase().includes("spell")
				? "spells"
				: "inventory";

			if (!currentContent[targetKey]) {
				currentContent[targetKey] = [];
			}
			currentContent[targetKey].push({
				name: ref.name,
				description: ref.description,
				source: ref.source_page ? `Page ${ref.source_page}` : "Rulebook",
			});

			setSheetContent(JSON.stringify(currentContent, null, 2));
		} catch (_e) {
			alert("Fix JSON syntax before adding references automatically.");
		}
	};

	if (sheetLoading) {
		return (
			<div className="flex items-center justify-center p-12">
				<Loader2 className="h-8 w-8 animate-spin text-primary" />
			</div>
		);
	}

	if (!sheet) {
		return <div className="p-12 text-center text-red-500">Sheet not found</div>;
	}

	const filteredReferences = references.filter(
		(r) =>
			r.name.toLowerCase().includes(referenceSearch.toLowerCase()) ||
			r.description.toLowerCase().includes(referenceSearch.toLowerCase()),
	);

	return (
		<div className="space-y-6 p-6 max-w-7xl mx-auto flex flex-col h-[calc(100vh-6rem)]">
			<div className="flex items-center justify-between shrink-0">
				<div className="flex items-center gap-4">
					<button
						type="button"
						onClick={() => navigate("/sheets")}
						className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors text-muted-foreground hover:text-white"
						aria-label="Back to sheets"
						title="Go back"
					>
						<ArrowLeft className="h-5 w-5" />
					</button>
					<div>
						<h2 className="text-2xl font-bold">{sheet.character_name}</h2>
						<p className="text-sm text-muted-foreground">
							Player: {sheet.player_name}
						</p>
					</div>
				</div>
				<div className="flex items-center gap-2">
					<GlassButton
						variant="secondary"
						size="sm"
						className="gap-2"
						onClick={() => window.open(`/#/public/sheet/${sheet.id}`, "_blank")}
					>
						<ExternalLink className="h-4 w-4" /> Player View
					</GlassButton>
					<GlassButton
						variant="secondary"
						size="sm"
						className="gap-2 text-red-400 hover:text-red-300 hover:bg-red-900/20"
						onClick={() => {
							if (confirm("Are you sure you want to delete this sheet?")) {
								deleteSheet();
							}
						}}
						disabled={deleting}
					>
						<Trash2 className="h-4 w-4" /> Delete
					</GlassButton>
					<GlassButton
						size="sm"
						className="gap-2"
						onClick={() => saveSheet()}
						disabled={saving}
					>
						{saving ? (
							<Loader2 className="h-4 w-4 animate-spin" />
						) : (
							<Save className="h-4 w-4" />
						)}{" "}
						Save Changes
					</GlassButton>
				</div>
			</div>

			<div className="flex gap-6 flex-1 min-h-0">
				{/* Editor Pane */}
				<GlassCard className="flex-1 flex flex-col p-4 overflow-hidden">
					<h3 className="font-semibold mb-2 shrink-0">Sheet Content (JSON)</h3>
					<textarea
						value={sheetContent}
						onChange={(e) => setSheetContent(e.target.value)}
						className="flex-1 w-full bg-black/40 border border-white/5 rounded-xl p-4 font-mono text-sm resize-none focus:ring-1 focus:ring-primary/50 outline-none text-[#d4d4d4]"
						spellCheck={false}
						aria-label="Sheet content editor"
					/>
				</GlassCard>

				{/* References Pane */}
				<GlassCard className="w-[400px] flex flex-col p-4 overflow-hidden bg-black/20 border-white/5">
					<h3 className="font-semibold mb-4 shrink-0">Quick References</h3>

					<div className="space-y-3 shrink-0 mb-4">
						<select
							className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:ring-1 focus:ring-primary/50 outline-none"
							value={referenceCategory}
							onChange={(e) => setReferenceCategory(e.target.value)}
							aria-label="Reference category selector"
						>
							<option value="Spell" className="text-black">
								Spells
							</option>
							<option value="Weapon" className="text-black">
								Weapons
							</option>
							<option value="Item" className="text-black">
								Equipment / Items
							</option>
							<option value="Ability" className="text-black">
								Abilities / Feats
							</option>
							<option value="" className="text-black">
								All Categories
							</option>
						</select>

						<div className="relative">
							<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
							<input
								type="text"
								placeholder="Search references..."
								value={referenceSearch}
								onChange={(e) => setReferenceSearch(e.target.value)}
								className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-sm focus:ring-1 focus:ring-primary/50 outline-none"
								aria-label="Search references"
							/>
						</div>
					</div>

					<div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
						{referencesLoading ? (
							<div className="flex justify-center p-4">
								<Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
							</div>
						) : filteredReferences.length === 0 ? (
							<p className="text-sm text-muted-foreground text-center p-4">
								No references found in this category.
							</p>
						) : (
							filteredReferences.map((ref) => (
								<div
									key={ref.id}
									className="bg-white/5 border border-white/10 rounded-xl p-3 hover:bg-white/10 transition-colors group"
								>
									<div className="flex justify-between items-start gap-2">
										<h4 className="font-medium text-sm text-white/90">
											{ref.name}
										</h4>
										<button
											type="button"
											onClick={() => handleAddReference(ref)}
											className="opacity-0 group-hover:opacity-100 p-1 bg-primary/20 hover:bg-primary/40 text-primary rounded-md transition-all"
											title="Add to sheet"
										>
											<PlusCircle className="h-3 w-3" />
										</button>
									</div>
									<p className="text-xs text-muted-foreground mt-1 line-clamp-3 leading-relaxed">
										{ref.description}
									</p>
									<div className="flex flex-wrap gap-1 mt-2">
										{ref.tags?.map((t) => (
											<span
												key={t}
												className="text-[10px] px-1.5 py-0.5 bg-white/10 rounded-md text-white/70"
											>
												{t}
											</span>
										))}
										{ref.source_page && (
											<span className="text-[10px] px-1.5 py-0.5 bg-primary/20 text-primary rounded-md">
												Pg. {ref.source_page}
											</span>
										)}
									</div>
								</div>
							))
						)}
					</div>
				</GlassCard>
			</div>
		</div>
	);
};

export default SheetDetailsPage;
