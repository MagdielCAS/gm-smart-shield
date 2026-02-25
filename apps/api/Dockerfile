# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy configuration files
COPY pyproject.toml uv.lock README.md ./

# Copy source code
COPY gm_shield ./gm_shield

# Install dependencies
# --frozen ensures we use the exact versions in uv.lock
# --no-dev excludes development dependencies
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN uv sync --frozen --no-dev

# Stage 2: Runner
FROM python:3.12-slim

WORKDIR /app

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/gm_shield /app/gm_shield

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "gm_shield.main:app", "--host", "0.0.0.0", "--port", "8000"]
