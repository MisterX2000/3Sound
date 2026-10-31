# Stage 1: Build Svelte 5 frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python production runner
FROM python:3.15-slim

# Install uv from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment configuration for uv & python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    SOUNDS_DIR=/app/sounds \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Ensure sounds directory exists
RUN mkdir -p /app/sounds

# Copy dependency specifications (including lockfile and python pin if present)
COPY pyproject.toml uv.lock* .python-version* ./

# Install dependencies using uv (creates .venv with bytecode compiled)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy application files and built frontend
COPY *.py ./
COPY --from=frontend-builder /build/dist ./frontend/dist

# Expose web server port
EXPOSE 8000

# Start server using FastAPI CLI
CMD ["fastapi", "run", "main.py", "--port", "8000", "--proxy-headers"]
