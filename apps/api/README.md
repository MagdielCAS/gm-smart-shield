# GM Smart Shield API

This is the Python/FastAPI backend for GM Smart Shield.

## Setup

```bash
make setup
```

## Running Locally

```bash
make run-api
```

The API will be available at `http://localhost:8000`.
Docs: `http://localhost:8000/api/v1/docs`

## Docker

You can run the entire stack (API, Prometheus, Grafana, Ollama) using Docker Compose:

```bash
make docker-up
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ENABLE_METRICS` | Enable OpenTelemetry metrics at `/metrics` | `False` |
| `OLLAMA_BASE_URL` | URL of the Ollama instance | `http://localhost:11434` |
| `OLLAMA_MODEL_GENERAL` | Model for general tasks (QA, tagging) | `llama3.2:3b` |
| `OLLAMA_MODEL_STRUCTURED` | Model for structured output | `granite4:latest` |
| `OLLAMA_MODEL_CREATIVE` | Model for creative generation | `gemma3:12b-it-qat` |
| `SQLITE_URL` | Database URL | `sqlite:///data/db/gm_shield.db` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | `data/chroma` |

## Health Check

- `/health`: Simple heartbeat.
- `/health/status`: Detailed check of DB, Chroma, and Ollama connections.

## Metrics

If `ENABLE_METRICS=true`, metrics are available at `/metrics` (Prometheus format).
