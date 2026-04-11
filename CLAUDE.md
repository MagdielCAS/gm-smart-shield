# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GM Smart Shield is a locally-hosted, LLM-powered assistant for Tabletop RPG Game Masters. It turns rulebooks, campaign supplements, and homebrew PDFs into an intelligent, interactive knowledge base running entirely on the GM's machine.

## Architecture

The project is a full-stack web application with:

- **Frontend**: React + Vite + TypeScript served at `http://localhost:5173`
- **Backend**: Python FastAPI server at `http://localhost:8000`
- **LLM Runtime**: Ollama serving local models (llama3.2:3b, granite4:latest, gemma3:12b-it-qat)
- **Vector Database**: ChromaDB for semantic search
- **Structured Database**: SQLite for notes, character sheets, and metadata

## Development Commands

### Core Development
- `make dev` - Run full project (API + Web) in development mode
- `make dev-api` - Run only the API server with hot-reload
- `make dev-web` - Run only the Vite frontend

### Setup
- `make setup` - Install all dependencies (API + Web)
- `make api-setup` - Install API dependencies via `uv`
- `make web-setup` - Install Web dependencies via `pnpm`

### Testing
- `make test` - Run all tests (API + Web unit)
- `make api-test` - Run API tests (`pytest`)
- `make web-test` - Run Web unit tests (`vitest`)
- `make web-test-e2e` - Run E2E tests (`playwright`)
- `make web-test-bdd` - Run BDD tests (`playwright-bdd`)

### Code Quality
- `make lint` - Run all linters
- `make lint-fix` - Auto-fix all lint errors
- `make format` - Format all code
- `make api-lint` - Run API linter (ruff)
- `make web-lint` - Run Web linter (Biome)

### Docker
- `make docker-up` - Start Docker services
- `make docker-down` - Stop Docker services
- `make docker-build` - Build Docker images

## Project Structure

```
apps/
├── web/                    # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/     # UI components organized by feature
│   │   ├── hooks/         # Custom React hooks
│   │   ├── store/          # Zustand state management
│   │   └── api/           # API client layer
│   └── prisma/            # Prisma schema for SQLite
│
└── api/                  # Python FastAPI backend
    ├── gm_shield/
    │   ├── routers/       # FastAPI route handlers
    │   ├── agents/       # LLM agent implementations
    │   ├── ingestion/    # Document parsing and chunking
    │   ├── db/           # SQLAlchemy models + migrations
    │   ├── tasks/        # ARQ background tasks
    │   └── core/         # Config, settings, dependencies
    └── tests/            # Test files
```

## Key Design Patterns

### Frontend
- Uses Zustand for state management (lightweight alternative to Redux)
- Components are organized by feature (chat, notes, sheets, etc.)
- API calls use TanStack Query for caching and loading states
- Markdown editing with CodeMirror 6, preview with remark/rehype

### Backend
- FastAPI with automatic OpenAPI documentation
- SQLAlchemy 2.x with async support
- Background processing using ARQ (async Redis-based queue)
- Document processing pipeline: Upload → Parse → Chunk → Embed → Store
- Specialized LLM agents for different tasks (Query, Sheet, Reference, Encounter, Tagging)

### Data Flow
1. **Document Upload**: PDF/MD files are parsed and chunked into semantic units
2. **Vector Embedding**: Text chunks are embedded using sentence-transformers
3. **Storage**: Vectors stored in ChromaDB, metadata in SQLite
4. **Background Tasks**: Agents process documents for character sheets, quick references, and knowledge linking
5. **Query**: RAG-based Q&A using vector similarity search

## Debugging (VS Code)

The `.vscode/launch.json` provides three configurations:
- **API: Debug FastAPI** - Attach Python debugger to the API server
- **Web: Debug Vite** - Debug the Vite dev server in Chrome
- **Full Stack: API + Web** - Launch all debug sessions simultaneously

## Prerequisites

- Node.js 22+
- Python 3.12+ and `uv` package manager
- `pnpm` package manager
- Ollama running locally with models:
  ```bash
  ollama pull llama3.2:3b
  ollama pull granite4:latest
  ollama pull gemma3:12b-it-qat
  ```

## Important Notes

- All components run locally - no external cloud dependencies
- Files are stored in `data/` directory (gitignored)
- The app binds to `127.0.0.1` for security (local-only by default)
- Use the Makefile for all development tasks - it ensures proper setup and coordination between services