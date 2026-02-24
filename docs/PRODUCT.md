# GM Smart Shield — Product Documentation

> **Version:** 0.1.0 — Pre-Alpha  
> **Last Updated:** 2026-02-24  
> **Status:** In Design

---

## 1. Overview

**GM Smart Shield** is a locally-hosted AI-powered assistant platform designed specifically for **Tabletop RPG Game Masters (GMs)**. It transforms raw rulebooks, campaign materials, and homebrew content into an intelligent, interactive knowledge base that the GM can query, create with, and reference at the table — all without sending sensitive campaign data to external servers.

The platform is built around a core philosophy:

> *"Every rule, every world, every story — right at your fingertips."*

---

## 2. Problem Statement

Running a tabletop RPG session demands an enormous amount of mental overhead from the GM:

- Constantly cross-referencing multiple rulebooks and supplements
- Improvising NPC stats and encounters on the fly
- Tracking campaign notes, lore, and world-building details
- Managing player character sheets and their rule compliance
- Keeping spell lists, class features, and race traits readily accessible

Traditional solutions (physical books, PDFs, wikis) are fragmented, not context-aware, and require the GM to do all of the synthesis manually. **GM Smart Shield** solves this by bringing AI-driven context to the entire GM workflow.

---

## 3. Target Users

| User | Role | Core Need |
|---|---|---|
| **Game Master (GM)** | Primary user | Knowledge retrieval, encounter building, note-taking, rules reference |
| **Players** | Secondary users | Access to their own character sheets |

---

## 4. Core Features

### 4.1 Knowledge Base from Uploaded Content

The GM uploads PDFs, Markdown, or plain-text files (e.g., rulebooks, campaign settings, adventure modules). The platform:

- Parses and chunks the documents
- Generates vector embeddings for semantic search
- Stores everything in a local vector database (ChromaDB)
- Allows free-text queries backed by the knowledge source

### 4.2 AI Agents

Multiple LLM-powered agents collaborate to answer questions and generate content:

| Agent | Model | Responsibility |
|---|---|---|
| **Query Agent** | `llama3.2:3b` / `granite4:latest` | Quick Q&A against the knowledge base |
| **Sheet Agent** | `llama3.2:3b` | Character sheet template extraction and management |
| **Reference Agent** | `llama3.2:3b` | Auto-generating quick references (spells, classes, races, etc.) |
| **Encounter Agent** | `gemma3:12b-it-qat` | Creative encounter generation with NPC sheets |
| **Tagging Agent** | `llama3.2:3b` | Automatic keyword/tag extraction from notes |

### 4.3 Encounter Generator

Using the rules and lore from the uploaded knowledge sources, the Encounter Agent can generate:

- Full encounter setups (location, enemies, tactics)
- NPC character sheets in Markdown format with frontmatter
- Encounter difficulty ratings based on party composition
- Loot tables and story hooks

### 4.4 GM Note-Taking (Markdown Workspace)

A built-in note editor inspired by **Obsidian / Notion**:

- Full Markdown support with a rich preview
- Frontmatter properties for metadata (e.g., `tags`, `session`, `location`, `npcs`)
- Automatic tag extraction by the Tagging Agent after each save
- Bidirectional linking between notes and knowledge sources (with PDF page references)
- Folder/notebook organization

### 4.5 Quick References

After a knowledge source is uploaded, the platform auto-generates structured quick reference cards for:

- Spells
- Character classes and subclasses
- Races / lineages / ancestries
- Professions and backgrounds
- Combat rules and conditions
- Equipment and items

### 4.6 Player Character Sheets

- The GM uploads rulebook PDFs → the Sheet Agent extracts the character sheet template
- Templates are saved as **Markdown files with frontmatter** properties
- Players can fill in and update their sheets through the web UI
- Sheets are stored in SQLite and linked to the relevant knowledge source

### 4.7 Background Processing Pipeline

When a knowledge source is uploaded, a pipeline of background tasks is triggered automatically:

1. **Document ingestion** — parse, chunk, embed
2. **Character sheet template extraction**
3. **Quick reference generation** (spells, classes, races, etc.)
4. **Knowledge graph linking** — connect concepts ↔ documents ↔ notes

---

## 5. User Stories

### GM — Knowledge Base

- *As a GM, I want to upload my rulebook PDFs so that I can query specific rules without flipping through hundreds of pages.*
- *As a GM, I want to ask "What are the movement rules for difficult terrain?" and get an accurate, sourced answer.*

### GM — Notes

- *As a GM, I want to write session notes in Markdown so that I can keep my campaign organized.*
- *As a GM, I want my notes to be automatically tagged with relevant keywords from my session so I don't have to do it manually.*
- *As a GM, I want note links to reference specific pages in my uploaded PDFs so I can verify rules quickly.*

### GM — Encounter Generation

- *As a GM, I want to generate an encounter appropriate for a level 5 party in a dungeon setting, using the monsters from my uploaded bestiary.*
- *As a GM, I want NPC stat blocks generated for encounters so I can run combat without pre-preparing everything.*

### GM — Quick References

- *As a GM, I want a quick reference card for all spells available to a Wizard at level 7, based on my uploaded PHB.*

### GM — Character Sheets

- *As a GM, I want to provide my players with a character sheet template appropriate for my game system.*
- *As a player, I want to fill in my character sheet digitally so I don't have to manage paper sheets.*

---

## 6. Product Roadmap (High Level)

```
Phase 1 — Foundation (MVP)
  ├── Project setup & local dev environment
  ├── Document upload & ingestion pipeline
  ├── Basic Q&A chat interface
  └── Markdown note editor

Phase 2 — Intelligence Layer
  ├── Multi-agent architecture (Query, Sheet, Reference, Encounter, Tagging)
  ├── Background task processing pipeline
  ├── Quick reference auto-generation
  └── Auto-tagging & note ↔ source linking

Phase 3 — GM Tooling
  ├── Encounter generator with NPC sheets
  ├── Player character sheets
  └── Campaign / session management

Phase 4 — Polish & UX
  ├── Advanced search & filtering
  ├── Rich note editor (WYSIWYG + Markdown)
  └── UI themes & customization
```

---

## 7. Non-Goals (v0.1)

- Multi-user collaboration (beyond the GM + players model)
- Cloud hosting or external data synchronization
- Support for games not represented in uploaded documents
- Voice interface

---

## 8. Design Principles

1. **Local-first**: All data stays on the GM's machine. No external API calls for sensitive content.
2. **Document-grounded**: Every AI answer is anchored to uploaded content and cites its source.
3. **Markdown-native**: Notes, sheets, and references are all plain Markdown with frontmatter — portable and version-control friendly.
4. **Fast at the table**: Response times are optimized for real-time use during play sessions.
5. **Modular agents**: Each agent is independently replaceable as better local models become available.
