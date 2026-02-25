# AGENTS.md (Frontend)

## Context
- **Project:** GM Smart Shield (Frontend).
- **Location:** `apps/web`.
- **Stack:** React 19, Vite, TypeScript, Tailwind CSS (v3), shadcn/ui.

## Architecture
- **State Management:**
  - `zustand` for global client state (e.g., UI theme, session).
  - `@tanstack/react-query` for server state (data fetching, caching).
- **Routing:** `react-router-dom` (v7).
- **Styling:** Tailwind CSS + shadcn/ui components in `src/components/ui`.
- **Linting/Formatting:** Biome (`biome.json`).

## Directory Structure
- `src/api`: API client functions (fetch wrappers).
- `src/components`: Shared components.
  - `ui`: Reusable UI components (shadcn).
- `src/hooks`: Custom React hooks.
- `src/pages`: Page components (route targets).
- `src/lib`: Utility functions (`utils.ts`, etc.).
- `src/store`: Zustand stores.

## Testing Guidelines
- **Unit Tests (`vitest`):**
  - Locate next to source file (e.g., `App.test.tsx`).
  - Focus on component logic and rendering.
  - Run with `pnpm test`.
- **E2E/BDD Tests (`playwright` + `playwright-bdd`):**
  - Locate in `tests/features` (Gherkin) and `tests/steps` (TypeScript).
  - Focus on user flows and integration.
  - Run with `pnpm test:bdd` (generates tests) or `pnpm test:e2e`.

## Development
- Run dev server: `pnpm dev` (or `make web-dev` from root).
- Lint/Format: `pnpm lint`, `pnpm format`.
- Build: `pnpm build`.
