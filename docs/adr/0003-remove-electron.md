# 3. Remove Electron - Keep Vite SPA + Docker

Date: 2026-04-11

## Status

Accepted

## Context

Initially, ADR-0002 decided on an Electron shell to allow the frontend to bypass browser upload restrictions and provide the backend with direct filesystem paths. However, this introduced unnecessary build complexity, large bundle sizes, and required building executables for distribution. Upon review, migrating from Vite to a heavier SSR framework like Next.js purely for file uploads was also determined to be overengineering.

## Decision

We will remove Electron entirely and return to a plain Client-Server architecture using the existing React + Vite SPA and FastAPI backend.

- The application will be deployed and distributed via Docker Compose (making local setup minimal and platform-independent).
- The web app will be served by Nginx within a Docker container.
- File uploads will use standard HTTP `multipart/form-data` instead of absolute filesystem paths.
- The Python API will save uploaded files to a shared local `data/uploads/` directory, from which the existing ingestion pipeline can read them.

This supersedes ADR-0002.

## Consequences

### Positive
- **Simplicity:** No need to manage Electron builder configurations, codesigning, native modules, or Next.js migrations.
- **Portability:** Docker Compose provides a consistent environment across OSes.
- **Maintainability:** Standard web patterns (HTTP uploads) apply across the board.

### Negative
- **Network Overhead:** Instead of telling the backend "read from path X", the client must transfer the file over HTTP. (In a local environment via Docker, this overhead is negligible, but it's fundamentally different).
- **Storage:** Uploaded files must be stored (and potentially cleaned up) in the Server's `data/uploads/` folder rather than directly referencing the user's local disk location indefinitely.
