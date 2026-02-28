import { useQuery } from "@tanstack/react-query";
import { BookMarked, Loader2, Search } from "lucide-react";
import { useState } from "react";
import { GlassCard } from "../components/ui/GlassCard";
import { API_BASE_URL } from "../config";

interface QuickReference {
	id: string;
	title: string;
	category: string;
	content: string;
	knowledgeSourceId: string;
}

const ReferencesPage = () => {
	const [searchTerm, setSearchTerm] = useState("");

	const {
		data: references = [],
		isLoading,
		isError,
	} = useQuery<QuickReference[]>({
		queryKey: ["references"],
		queryFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/references`);
			if (!res.ok) {
				// Return empty for now if the endpoint is not yet implemented in backend
				if (res.status === 404) return [];
				throw new Error("Failed to fetch references");
			}
			return res.json();
		},
	});

	const filteredRefs = references.filter(
		(ref) =>
			ref.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
			ref.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
			ref.content.toLowerCase().includes(searchTerm.toLowerCase()),
	);

	return (
		<div className="space-y-8 p-6 max-w-7xl mx-auto">
			<div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
				<div>
					<h2 className="text-3xl font-bold tracking-tight">
						Quick References
					</h2>
					<p className="mt-2 text-muted-foreground max-w-lg">
						Browse auto-generated reference cards for spells, items, rules, and
						more.
					</p>
				</div>
				<div className="relative w-full md:w-72">
					<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<input
						type="text"
						placeholder="Search references..."
						value={searchTerm}
						onChange={(e) => setSearchTerm(e.target.value)}
						className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
					/>
				</div>
			</div>

			{isLoading ? (
				<div className="h-[400px] flex flex-col items-center justify-center space-y-4">
					<Loader2 className="h-8 w-8 text-primary animate-spin" />
					<p className="text-sm text-muted-foreground">
						Gathering references...
					</p>
				</div>
			) : isError ? (
				<div className="p-4 text-sm text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
					Failed to load references. Please try again later.
				</div>
			) : filteredRefs.length === 0 ? (
				<div className="h-[400px] flex flex-col items-center justify-center text-muted-foreground bg-white/5 rounded-3xl border border-dashed border-white/10 p-6 text-center">
					<BookMarked className="h-12 w-12 opacity-20 mb-4" />
					<p className="font-medium text-lg text-foreground">
						No references found
					</p>
					<p className="text-sm opacity-70 mt-1">
						{searchTerm
							? "Try adjusting your search query."
							: "Upload documents to auto-generate reference cards."}
					</p>
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{filteredRefs.map((ref) => (
						<GlassCard
							key={ref.id}
							className="flex flex-col h-full hover:bg-white/10 transition-colors"
						>
							<div className="mb-4">
								<span className="inline-block px-2 py-1 bg-primary/20 text-primary text-xs font-semibold rounded-md uppercase tracking-wider mb-2">
									{ref.category}
								</span>
								<h3 className="text-xl font-bold text-foreground leading-tight">
									{ref.title}
								</h3>
							</div>
							<div className="flex-1">
								<p className="text-sm text-muted-foreground/90 whitespace-pre-wrap leading-relaxed">
									{ref.content}
								</p>
							</div>
						</GlassCard>
					))}
				</div>
			)}
		</div>
	);
};

export default ReferencesPage;
