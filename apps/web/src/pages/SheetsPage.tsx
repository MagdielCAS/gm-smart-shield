import { useQuery } from "@tanstack/react-query";
import { FileBadge, Loader2, Plus, Search } from "lucide-react";
import { useState } from "react";
import { GlassButton } from "../components/ui/GlassButton";
import { GlassCard } from "../components/ui/GlassCard";
import { API_BASE_URL } from "../config";

interface CharacterSheet {
	id: string;
	playerName: string;
	characterName: string;
	templateId: string;
}

const SheetsPage = () => {
	const [searchTerm, setSearchTerm] = useState("");

	const {
		data: sheets = [],
		isLoading,
		isError,
	} = useQuery<CharacterSheet[]>({
		queryKey: ["sheets"],
		queryFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/sheets`);
			if (!res.ok) {
				if (res.status === 404) return [];
				throw new Error("Failed to fetch sheets");
			}
			return res.json();
		},
	});

	const filteredSheets = sheets.filter(
		(sheet) =>
			sheet.characterName.toLowerCase().includes(searchTerm.toLowerCase()) ||
			sheet.playerName.toLowerCase().includes(searchTerm.toLowerCase()),
	);

	return (
		<div className="space-y-8 p-6 max-w-7xl mx-auto">
			<div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
				<div>
					<h2 className="text-3xl font-bold tracking-tight">
						Character Sheets
					</h2>
					<p className="mt-2 text-muted-foreground max-w-lg">
						Manage player character sheets extracted from your uploaded modules.
					</p>
				</div>
				<div className="flex items-center gap-4 w-full md:w-auto">
					<div className="relative flex-1 md:w-64">
						<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
						<input
							type="text"
							placeholder="Find a character..."
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
							className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
						/>
					</div>
					<GlassButton size="sm" className="shrink-0 gap-2">
						<Plus className="h-4 w-4" /> New Sheet
					</GlassButton>
				</div>
			</div>

			{isLoading ? (
				<div className="h-[400px] flex flex-col items-center justify-center space-y-4">
					<Loader2 className="h-8 w-8 text-primary animate-spin" />
					<p className="text-sm text-muted-foreground">Loading sheets...</p>
				</div>
			) : isError ? (
				<div className="p-4 text-sm text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
					Failed to load character sheets. Please try again later.
				</div>
			) : filteredSheets.length === 0 ? (
				<div className="h-[400px] flex flex-col items-center justify-center text-muted-foreground bg-white/5 rounded-3xl border border-dashed border-white/10 p-6 text-center">
					<FileBadge className="h-12 w-12 opacity-20 mb-4" />
					<p className="font-medium text-lg text-foreground">No sheets found</p>
					<p className="text-sm opacity-70 mt-1 max-w-md">
						{searchTerm
							? "No characters match your search."
							: "Upload rulebooks to extract character sheet templates, or create one manually."}
					</p>
					{!searchTerm && (
						<GlassButton className="mt-6 gap-2" variant="secondary">
							<Plus className="h-4 w-4" /> Create First Sheet
						</GlassButton>
					)}
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
					{filteredSheets.map((sheet) => (
						<GlassCard
							key={sheet.id}
							className="flex flex-col relative group cursor-pointer hover:bg-white/10 transition-colors"
						>
							<div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
								<div className="h-2 w-2 rounded-full bg-primary" />
							</div>
							<div className="flex items-center gap-4 mb-4">
								<div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary/40 to-primary/10 flex items-center justify-center text-lg font-bold border border-white/10">
									{sheet.characterName.charAt(0)}
								</div>
								<div>
									<h3 className="font-bold text-foreground truncate max-w-[150px]">
										{sheet.characterName}
									</h3>
									<p className="text-xs text-muted-foreground">
										Player: {sheet.playerName}
									</p>
								</div>
							</div>
							<p className="text-xs text-muted-foreground mt-auto pt-4 border-t border-white/5">
								Template ID:{" "}
								<span className="font-mono">{sheet.templateId}</span>
							</p>
						</GlassCard>
					))}
				</div>
			)}
		</div>
	);
};

export default SheetsPage;
