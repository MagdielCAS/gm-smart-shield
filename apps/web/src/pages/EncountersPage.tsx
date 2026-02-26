import { useMutation } from "@tanstack/react-query";
import {
	Activity,
	BrainCircuit,
	Copy,
	Dices,
	Heart,
	RefreshCw,
	Shield,
	Swords,
	Zap,
} from "lucide-react";
import { useState } from "react";
import { GlassButton } from "../components/ui/GlassButton";
import { GlassCard } from "../components/ui/GlassCard";
import { SFIcon } from "../components/ui/SFIcon";
import { API_BASE_URL } from "../config";

// ── Types ────────────────────────────────────────────────────────────────────

interface NPCStatBlock {
	name: string;
	creature_type: string;
	cr: string;
	hp: string;
	ac: string;
	speed: string;
	stats: string;
	actions: string[];
	special_abilities?: string[];
}

interface EncounterResponse {
	title: string;
	description: string;
	tactics: string;
	loot?: string;
	npcs: NPCStatBlock[];
}

interface GenerateParams {
	level: string;
	difficulty: string;
	theme: string;
}

// ── Component ────────────────────────────────────────────────────────────────

const EncountersPage = () => {
	const [level, setLevel] = useState("3");
	const [difficulty, setDifficulty] = useState("Medium");
	const [theme, setTheme] = useState("");

	const generateMutation = useMutation<
		EncounterResponse,
		Error,
		GenerateParams
	>({
		mutationFn: async (params) => {
			const res = await fetch(`${API_BASE_URL}/v1/encounters/generate`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(params),
			});
			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail || "Failed to generate encounter");
			}
			return res.json();
		},
	});

	const handleGenerate = (e: React.FormEvent) => {
		e.preventDefault();
		if (!theme) return;
		generateMutation.mutate({ level, difficulty, theme });
	};

	const copyToClipboard = (text: string) => {
		navigator.clipboard.writeText(text);
	};

	return (
		<div className="space-y-8 p-6 max-w-7xl mx-auto">
			{/* Header */}
			<div className="flex items-end justify-between">
				<div>
					<h2 className="text-3xl font-bold tracking-tight">
						Encounter Generator
					</h2>
					<p className="mt-2 text-muted-foreground max-w-lg">
						Create tactical combat encounters tailored to your party, powered by
						your knowledge base.
					</p>
				</div>
			</div>

			<div className="grid gap-8 lg:grid-cols-3">
				{/* Controls */}
				<GlassCard className="lg:col-span-1 h-fit space-y-6">
					<form onSubmit={handleGenerate} className="space-y-6">
						<div className="space-y-4">
							<div>
								<label
									htmlFor="party-level"
									className="text-sm font-medium mb-1.5 block"
								>
									Party Level
								</label>
								<input
									id="party-level"
									type="number"
									value={level}
									onChange={(e) => setLevel(e.target.value)}
									className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
									min="1"
									max="20"
								/>
							</div>

							<div>
								<label
									htmlFor="difficulty"
									className="text-sm font-medium mb-1.5 block"
								>
									Difficulty
								</label>
								<select
									id="difficulty"
									value={difficulty}
									onChange={(e) => setDifficulty(e.target.value)}
									className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none"
								>
									{["Easy", "Medium", "Hard", "Deadly"].map((d) => (
										<option key={d} value={d} className="bg-background">
											{d}
										</option>
									))}
								</select>
							</div>

							<div>
								<label
									htmlFor="theme"
									className="text-sm font-medium mb-1.5 block"
								>
									Theme / Setting
								</label>
								<textarea
									id="theme"
									value={theme}
									onChange={(e) => setTheme(e.target.value)}
									placeholder="e.g., Swamp ambush by lizardfolk, Haunted crypt, Goblin market gone wrong..."
									className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/50 outline-none min-h-[100px] resize-none"
									required
								/>
							</div>
						</div>

						<GlassButton
							type="submit"
							className="w-full relative overflow-hidden"
							size="lg"
							disabled={generateMutation.isPending || !theme}
						>
							{generateMutation.isPending ? (
								<>
									<RefreshCw className="mr-2 h-4 w-4 animate-spin" />
									Dreaming up chaos...
								</>
							) : (
								<>
									<SFIcon icon={Dices} className="mr-2 h-4 w-4" />
									Generate Encounter
								</>
							)}
							{/* Shine effect */}
							{!generateMutation.isPending && (
								<div className="absolute inset-0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
							)}
						</GlassButton>

						{generateMutation.isError && (
							<div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20">
								{generateMutation.error.message}
							</div>
						)}
					</form>
				</GlassCard>

				{/* Results Display */}
				<div className="lg:col-span-2 space-y-6">
					{!generateMutation.data && !generateMutation.isPending && (
						<div className="h-full min-h-[400px] flex flex-col items-center justify-center text-muted-foreground bg-white/5 rounded-3xl border border-dashed border-white/10">
							<Swords className="h-12 w-12 opacity-20 mb-4" />
							<p className="font-medium">Ready for battle?</p>
							<p className="text-sm opacity-70">
								Enter parameters to generate a unique encounter.
							</p>
						</div>
					)}

					{generateMutation.isPending && (
						<div className="h-full min-h-[400px] flex flex-col items-center justify-center space-y-4">
							<div className="relative">
								<div className="h-16 w-16 rounded-full border-4 border-primary/20 animate-spin border-t-primary" />
								<BrainCircuit className="absolute inset-0 m-auto h-8 w-8 text-primary/50 animate-pulse" />
							</div>
							<p className="text-sm text-muted-foreground animate-pulse">
								Consulting the archives...
							</p>
						</div>
					)}

					{generateMutation.data && (
						<div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
							{/* Encounter Overview */}
							<GlassCard className="relative overflow-hidden">
								<div className="absolute top-0 right-0 -mt-12 -mr-12 h-48 w-48 bg-primary/10 blur-3xl rounded-full pointer-events-none" />

								<div className="relative z-10">
									<h3 className="text-2xl font-bold mb-4 flex items-center gap-3">
										<Swords className="h-6 w-6 text-primary" />
										{generateMutation.data.title}
									</h3>

									<div className="prose prose-sm dark:prose-invert max-w-none mb-6 bg-black/5 dark:bg-white/5 p-4 rounded-xl italic border-l-4 border-primary/50">
										"{generateMutation.data.description}"
									</div>

									<div className="grid md:grid-cols-2 gap-6">
										<div>
											<h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-2">
												<BrainCircuit className="h-4 w-4" /> Tactics
											</h4>
											<p className="text-sm leading-relaxed">
												{generateMutation.data.tactics}
											</p>
										</div>
										{generateMutation.data.loot && (
											<div>
												<h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-2">
													<Zap className="h-4 w-4" /> Rewards
												</h4>
												<p className="text-sm leading-relaxed">
													{generateMutation.data.loot}
												</p>
											</div>
										)}
									</div>
								</div>
							</GlassCard>

							{/* Stat Blocks */}
							<div className="space-y-4">
								<h3 className="text-lg font-semibold px-1">Combatants</h3>
								<div className="grid gap-4">
									{generateMutation.data.npcs.map((npc, idx) => (
										<GlassCard
											key={`${npc.name}-${idx}`}
											className="border-l-4 border-l-red-500/50 hover:bg-white/40 dark:hover:bg-white/5 transition-colors"
										>
											<div className="flex justify-between items-start mb-2">
												<div>
													<h4 className="text-lg font-bold text-red-700 dark:text-red-400">
														{npc.name}
													</h4>
													<p className="text-xs text-muted-foreground italic">
														{npc.creature_type} • CR {npc.cr}
													</p>
												</div>
												<GlassButton
													size="icon"
													variant="ghost"
													onClick={() =>
														copyToClipboard(JSON.stringify(npc, null, 2))
													}
												>
													<Copy className="h-4 w-4" />
												</GlassButton>
											</div>

											<div className="grid grid-cols-3 gap-4 my-3 text-sm border-y border-white/10 py-2">
												<div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-medium">
													<Heart className="h-4 w-4" /> {npc.hp}
												</div>
												<div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium">
													<Shield className="h-4 w-4" /> AC {npc.ac}
												</div>
												<div className="flex items-center gap-2 text-green-600 dark:text-green-400 font-medium">
													<Activity className="h-4 w-4" /> {npc.speed}
												</div>
											</div>

											<div className="space-y-3 text-sm">
												<div>
													<span className="font-semibold text-xs uppercase tracking-wide opacity-70">
														Stats
													</span>
													<p className="font-mono text-xs mt-1 bg-black/5 dark:bg-white/5 p-1 rounded">
														{npc.stats}
													</p>
												</div>

												{npc.special_abilities &&
													npc.special_abilities.length > 0 && (
														<div>
															<span className="font-semibold text-xs uppercase tracking-wide opacity-70">
																Traits
															</span>
															<ul className="list-disc list-inside mt-1 space-y-1">
																{npc.special_abilities.map((ability, i) => (
																	<li
																		// biome-ignore lint/suspicious/noArrayIndexKey: Static list, order won't change
																		key={`${idx}-trait-${i}`}
																		className="text-muted-foreground"
																	>
																		{ability}
																	</li>
																))}
															</ul>
														</div>
													)}

												<div>
													<span className="font-semibold text-xs uppercase tracking-wide opacity-70">
														Actions
													</span>
													<ul className="mt-1 space-y-2">
														{npc.actions.map((action, i) => (
															<li
																// biome-ignore lint/suspicious/noArrayIndexKey: Static list, order won't change
																key={`${idx}-action-${i}`}
																className="pl-3 border-l-2 border-primary/20"
															>
																{action}
															</li>
														))}
													</ul>
												</div>
											</div>
										</GlassCard>
									))}
								</div>
							</div>
						</div>
					)}
				</div>
			</div>
		</div>
	);
};

export default EncountersPage;
