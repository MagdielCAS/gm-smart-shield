import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

interface ThemeState {
	theme: Theme;
	setTheme: (theme: Theme) => void;
}

/** Apply or remove the `dark` class on the root element based on the resolved theme. */
function applyTheme(theme: Theme): void {
	const root = document.documentElement;
	const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
	const isDark = theme === "dark" || (theme === "system" && prefersDark);
	root.classList.toggle("dark", isDark);
}

export const useTheme = create<ThemeState>()(
	persist(
		(set) => ({
			theme: "system" as Theme,
			setTheme: (theme: Theme) => {
				applyTheme(theme);
				set({ theme });
			},
		}),
		{ name: "gm-shield-theme" },
	),
);

/** Call once on app boot to apply the persisted theme before first render. */
export function initTheme(): void {
	const stored = localStorage.getItem("gm-shield-theme");
	let theme: Theme = "system";
	try {
		const parsed = JSON.parse(stored ?? "{}");
		if (["light", "dark", "system"].includes(parsed?.state?.theme)) {
			theme = parsed.state.theme as Theme;
		}
	} catch {
		// ignore malformed storage
	}
	applyTheme(theme);

	// Keep "system" in sync with OS-level changes
	window
		.matchMedia("(prefers-color-scheme: dark)")
		.addEventListener("change", () => {
			const current = useTheme.getState().theme;
			if (current === "system") applyTheme("system");
		});
}
