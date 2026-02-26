# 0001. Use Vertical Slices Architecture

Date: 2026-02-24

## Status

Accepted

## Context

We are building a FastAPI backend for GM Smart Shield. The application will have several distinct features such as Knowledge Base management, Chat/Q&A, Note taking, Character Sheets, and Encounter Generation.

A traditional layered architecture (Controllers, Services, Repositories) often leads to scattering related code across multiple directories. When working on a specific feature, a developer has to jump between these layers, which increases cognitive load and coupling between unrelated features.

## Decision

We will organize the application using **Vertical Slices**.

Each feature (slice) will be self-contained in its own directory, including its API routes (controllers), business logic (services/models), and data access (repositories).

Proposed structure:
```
apps/api/gm_shield/
    core/           # Shared config, logging, etc.
    shared/         # Shared utils, repositories (e.g. generic DB access)
    features/
        knowledge/  # Routes, models, services for knowledge
        chat/       # Routes, models, services for chat
        notes/      # ...
        sheets/
        encounters/
```

Within each slice, we can use a mini-layered approach if the complexity warrants it, or keep it simple.

## Consequences

### Positive
- **High Cohesion:** Code related to a specific feature is grouped together.
- **Low Coupling:** Features are less likely to depend on internal details of other features.
- **Easier Navigation:** Developers can find all code related to a feature in one place.
- **Scalability:** It is easier to split a slice into a separate service later if needed.

### Negative
- **Code Duplication:** There might be some duplication of common logic if not carefully extracted to `shared`.
- **Inconsistency:** Different slices might evolve different internal structures depending on their specific needs (though this can also be a pro).

## Compliance

All new features should be added as a new directory under `features/`. Shared code should be placed in `shared/` or `core/` only if it is truly generic and used by multiple slices.
