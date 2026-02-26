import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { initTheme } from "./lib/useTheme";

// Apply persisted theme before first render to avoid FOUC
initTheme();

// biome-ignore lint/style/noNonNullAssertion: safe default
createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<App />
	</StrictMode>,
);
