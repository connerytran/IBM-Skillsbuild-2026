# syntax=docker/dockerfile:1.6

# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build deps that some wheels (e.g. grpcio from supabase) occasionally need
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY agent/ ./agent/
COPY setup/ ./setup/

# Create an unprivileged user and drop root
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# `config.py` and `mcp_server.py` use bare imports (e.g. `import config`),
# so run from inside the agent/ directory.
WORKDIR /app/agent

# Expose the WebSocket port used by the frontend
EXPOSE 8765

# Default command runs main.py, which starts both the WebSocket server and the agent loop.
# Override with e.g. `python mcp_server.py` to run the MCP server,
# or `python /app/setup/seed_database.py` to seed the DB.
CMD ["python", "main.py"]
