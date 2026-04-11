import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Save, UserCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { API_BASE_URL } from "../config";

interface CharacterSheet {
	id: string;
	player_name: string;
	character_name: string;
	content: Record<string, unknown>;
}

const PlayerSheetPage = () => {
	const { id } = useParams();
	const queryClient = useQueryClient();

	const [isEditMode, setIsEditMode] = useState(false);
	const [sheetContent, setSheetContent] = useState("");

	const { data: sheet, isLoading } = useQuery<CharacterSheet>({
		queryKey: ["publicSheet", id],
		queryFn: async () => {
			const res = await fetch(`${API_BASE_URL}/v1/sheets/public/${id}`);
			if (!res.ok) throw new Error("Failed to fetch public sheet");
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
			const parsedContent = JSON.parse(sheetContent);
			const res = await fetch(`${API_BASE_URL}/v1/sheets/${id}`, {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ content: parsedContent }),
			});
			if (!res.ok) throw new Error("Failed to save sheet");
			return res.json();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["publicSheet", id] });
			setIsEditMode(false);
		},
		onError: (err) => {
			if (err instanceof Error) {
				alert(err.message);
			} else {
				alert(String(err));
			}
		},
	});

	if (isLoading) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-[#111317]">
				<Loader2 className="h-8 w-8 animate-spin text-primary" />
			</div>
		);
	}

	if (!sheet) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-[#111317] text-white">
				<p>Character sheet not found or is private.</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-[#111317] text-white/90 p-4 sm:p-6 pb-24 font-sans selection:bg-primary/30">
			<div className="max-w-md mx-auto relative">
				<header className="flex items-center gap-4 mb-8 bg-white/5 p-4 rounded-2xl border border-white/10 backdrop-blur-md">
					<div className="h-14 w-14 rounded-full bg-gradient-to-br from-primary/40 to-primary/10 flex items-center justify-center border border-white/10 shrink-0">
						<UserCircle2 className="h-8 w-8 text-white/80" />
					</div>
					<div>
						<h1 className="text-2xl font-bold font-serif tracking-tight">
							{sheet.character_name}
						</h1>
						<p className="text-sm text-primary/80 font-medium">
							Player: {sheet.player_name}
						</p>
					</div>
				</header>

				<main>
					{isEditMode ? (
						<div className="space-y-4 animate-in slide-in-from-bottom-2 fade-in">
							<div className="bg-black/30 border border-white/10 p-4 rounded-2xl">
								<h3 className="font-semibold mb-2 text-sm text-white/60 uppercase tracking-wider">
									Raw Editor
								</h3>
								<textarea
									value={sheetContent}
									onChange={(e) => setSheetContent(e.target.value)}
									className="w-full h-96 bg-transparent font-mono text-sm resize-none focus:outline-none text-[#d4d4d4]"
									spellCheck={false}
									aria-label="Raw sheet content"
								/>
							</div>
						</div>
					) : (
						<div className="space-y-4 animate-in slide-in-from-bottom-2 fade-in">
							{Object.entries(sheet.content).map(([key, value]) => (
								<div
									key={key}
									className="bg-white/5 border border-white/10 p-4 rounded-2xl"
								>
									<h3 className="font-semibold text-sm text-white/60 uppercase tracking-wider mb-3">
										{key.replace(/_/g, " ")}
									</h3>
									{Array.isArray(value) ? (
										<div className="space-y-2">
											{value.map((item, i) => (
												<div
													key={`item-${i}-${typeof item === "object" && item !== null ? JSON.stringify(item) : String(item)}`}
													className="bg-black/20 p-3 rounded-xl text-sm border border-white/5"
												>
													{typeof item === "object" && item !== null ? (
														<div className="space-y-1">
															{Object.entries(item).map(([k, v]) => (
																<div key={k}>
																	<span className="font-medium text-white/70 capitalize">
																		{k}:{" "}
																	</span>
																	<span>
																		{typeof v === "object" && v !== null
																			? JSON.stringify(v)
																			: String(v)}
																	</span>
																</div>
															))}
														</div>
													) : (
														<span>{String(item)}</span>
													)}
												</div>
											))}
										</div>
									) : typeof value === "object" && value !== null ? (
										<div className="grid grid-cols-2 gap-2 text-sm">
											{Object.entries(value).map(([subK, subV]) => (
												<div
													key={subK}
													className="bg-black/20 p-2 rounded-xl text-center border border-white/5"
												>
													<div className="font-bold text-lg">
														{String(subV)}
													</div>
													<div className="text-[10px] text-white/50 uppercase tracking-wider truncate">
														{subK}
													</div>
												</div>
											))}
										</div>
									) : (
										<div className="text-lg font-medium">{String(value)}</div>
									)}
								</div>
							))}

							{Object.keys(sheet.content).length === 0 && (
								<p className="text-center text-muted-foreground pt-12">
									This sheet is blank. Switch to Edit Mode to add properties.
								</p>
							)}
						</div>
					)}
				</main>

				{/* Floating Action Bar */}
				<div className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[#1a1c23] border border-white/10 p-2 rounded-full shadow-2xl backdrop-blur-xl z-50">
					{isEditMode ? (
						<>
							<button
								type="button"
								onClick={() => {
									setIsEditMode(false);
									setSheetContent(JSON.stringify(sheet.content, null, 2));
								}}
								className="px-6 py-2.5 rounded-full text-sm font-medium text-white/70 hover:text-white hover:bg-white/10 transition-colors"
							>
								Cancel
							</button>
							<button
								type="button"
								onClick={() => saveSheet()}
								disabled={saving}
								className="flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
							>
								{saving ? (
									<Loader2 className="w-4 h-4 animate-spin" />
								) : (
									<Save className="w-4 h-4" />
								)}
								Save
							</button>
						</>
					) : (
						<button
							type="button"
							onClick={() => setIsEditMode(true)}
							className="px-8 py-2.5 rounded-full text-sm font-medium bg-white/10 text-white hover:bg-white/20 transition-colors"
						>
							Edit Mode
						</button>
					)}
				</div>
			</div>
		</div>
	);
};

export default PlayerSheetPage;
