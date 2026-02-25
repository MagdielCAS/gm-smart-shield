/// <reference types="vitest" />
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// https://vite.dev/config/
export default defineConfig({
	plugins: [react()],
	server: {
		proxy: {
			"/api": {
				target: "http://localhost:8000",
				changeOrigin: true,
			},
		},
	},
	resolve: {
		alias: [{ find: "@", replacement: path.resolve(__dirname, "src") }],
	},
	test: {
		globals: true,
		environment: "jsdom",
		setupFiles: "./vitest.setup.ts",
		// Exclude playwright-bdd generated specs — they use test.describe() from
		// @playwright/test which is incompatible with vitest. Run them with `pnpm test:bdd`.
		exclude: [".features-gen/**", "node_modules/**", "tests/**"],
	},
});
