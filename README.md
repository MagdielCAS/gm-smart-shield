# GM Smart Shield 🛡️

> A locally-hosted, LLM-powered assistant for Tabletop RPG Game Masters.

GM Smart Shield turns your rulebooks, campaign supplements, and homebrew PDFs into an intelligent, interactive knowledge base — running entirely on your machine.

---

## What It Does

- **🧠 Knowledge Base** — Upload PDFs, Markdown, or text files; query them with natural language
- **⚔️ Encounter Generator** — Generate encounters with NPC stat blocks based on your uploaded rules
- **📒 GM Notes** — Markdown note editor with automatic tagging and knowledge source linking
- **📋 Quick References** — Auto-generated spell lists, class tables, race summaries, and more
- **🎭 Character Sheets** — Templates extracted from your rulebooks; players fill them in digitally
- **🤖 Local LLM Agents** — Everything runs on-device via Ollama (no cloud APIs required)

---

## Documentation

| Document | Description |
|---|---|
| [📦 Product Documentation](docs/PRODUCT.md) | Features, user stories, roadmap, design principles |
| [🏗️ Technical Documentation](docs/TECHNICAL.md) | Architecture, tech stack, data models, API design, Mermaid diagrams |

---

## Quick Start

> ⚠️ This project is in pre-alpha. Setup instructions will be finalized as the codebase is built.

### Prerequisites

- Node.js 22+
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- [pnpm](https://pnpm.io/)
- [Ollama](https://ollama.com) running locally with the following models:

```bash
ollama pull llama3.2:3b
ollama pull granite4:latest
ollama pull gemma3:12b-it-qat
```

### 1. Install dependencies

```bash
make setup
```

### 2. Run in development mode

```bash
make dev
```

This starts both the **FastAPI backend** and the **Electron app** concurrently. Press `Ctrl+C` to stop everything.

---

## Development Commands

All commands are exposed via the `Makefile`. Run `make help` to see the full list.

### Development

| Command | Description |
|---|---|
| `make dev` | **Run the full project** (API + Electron app) in dev mode |
| `make dev-api` | Run only the API server with hot-reload |
| `make dev-electron` | Run only the Electron + Vite frontend |
| `make run-api` | Run API server (alias, no explicit port) |
| `make web-dev` | Run Vite dev server only (no Electron) |

### Setup

| Command | Description |
|---|---|
| `make setup` | Install all dependencies (API + Web) |
| `make api-setup` | Install API dependencies via `uv` |
| `make web-setup` | Install Web dependencies via `pnpm` |

### Testing

| Command | Description |
|---|---|
| `make test` | Run all tests (API + Web unit) |
| `make api-test` | Run API tests (`pytest`) |
| `make web-test` | Run Web unit tests (`vitest`) |
| `make web-test-e2e` | Run E2E tests (`playwright`) |
| `make web-test-bdd` | Run BDD tests (`playwright-bdd`) |

### Lint & Format

| Command | Description |
|---|---|
| `make lint` | Run all linters |
| `make lint-fix` | Auto-fix all lint errors |
| `make format` | Format all code |

### Docker

| Command | Description |
|---|---|
| `make docker-up` | Start Docker services |
| `make docker-down` | Stop Docker services |
| `make docker-logs` | Tail Docker logs |
| `make docker-build` | Build Docker images |

---

## Debugging (VS Code)

A `.vscode/launch.json` is included with the following debug configurations:

| Configuration | Description |
|---|---|
| **API: Debug FastAPI (uvicorn)** | Attach Python debugger (`debugpy`) to the API |
| **Web: Debug Vite (browser)** | Debug the Vite dev server in Chrome |
| **Web: Debug Electron (main process)** | Debug the Electron Node.js main process |
| **Web: Debug Electron (renderer via Chrome)** | Attach Chrome DevTools to the Electron renderer |
| ⭐ **Full Stack: API + Electron** | Launch all debug sessions at once (compound) |

Open the **Run & Debug** panel (`Ctrl+Shift+D` / `Cmd+Shift+D`) and select the configuration you want.

---

## Architecture (TL;DR)

```
Electron App (React + Vite)  →  FastAPI Backend  →  LLM Agents (Ollama)
                                       ↓
                             ChromaDB (vector search)
                             SQLite (structured data)
```

See [Technical Documentation](docs/TECHNICAL.md) for full architecture diagrams.

---

## License

See [LICENSE](LICENSE).
