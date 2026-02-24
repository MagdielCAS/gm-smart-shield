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
- Python 3.12+
- [Ollama](https://ollama.com) with the following models:

```bash
ollama pull llama3.2:3b
ollama pull granite4:latest
ollama pull gemma3:12b-it-qat
```

---

## Architecture (TL;DR)

```
React Frontend  →  FastAPI Backend  →  LLM Agents (Ollama)
                         ↓
              ChromaDB (vector search)
              SQLite (structured data)
```

See [Technical Documentation](docs/TECHNICAL.md) for full architecture diagrams.

---

## License

See [LICENSE](LICENSE).
