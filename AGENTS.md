# AGENTS.md

## Project Overview
3Sound is a lightweight, responsive audio soundboard web application built with **FastAPI**, **uv**, and **Tailwind CSS**. It supports dual views (flat categories and hierarchical folder tree), on-the-fly embedded ID3/FLAC/MP4 artwork extraction, polyphonic voice pooling (up to 8 voices per sound), LRU memory management, and installable PWA offline capability.

## Technology Stack & Architecture
- **Backend**: Python 3.15+, FastAPI, Uvicorn, Mutagen (metadata & artwork parser), Pydantic Settings.
- **Frontend**: Single-page application, zero build tools. Uses precompiled static Tailwind CSS and vendored Alpine.js.
- **Audio Engine**: `AudioManager` ([`static/js/audio.js`](static/js/audio.js)) with voice pooling, LRU memory cache, and GPU-composited progress bar animations.
- **Media Storage**: The `sounds/` directory is strictly read-only at runtime with zero disk writes.

## Commands & Routines

### Task Runner (Poe the Poet)
```bash
uv run poe check         # Run all quality checks (lint, format-check, types, test)
uv run poe fix           # Automatically fix lint violations and reformat code
uv run poe dev           # Launch development server with hot-reload
uv run poe start         # Launch local server at http://localhost:8000
uv run poe test          # Run automated test suite
uv run poe coverage      # Run test suite with terminal coverage report
uv run poe outdated      # Check for outdated dependencies (uv tree --depth 1 --outdated)
uv run poe samples       # Generate test audio files & embedded ID3 artwork
uv run poe vendor        # Download latest Alpine.js & Tailwind CSS vendor files
uv run poe bump [patch|minor|major] # Bump version across pyproject.toml & sync
```

### Environment & Installation
```bash
uv sync --dev            # Install dependencies and development tools
```

### Development & Execution
```bash
uv run main.py           # Launch local server at http://localhost:8000
uv run fastapi dev main.py # Launch server with hot-reload & debug diagnostics
```

### Testing & Code Quality
```bash
uv run pytest            # Execute full test suite (or .venv/bin/pytest)
uv run ruff check .      # Run linter
uv run ruff format .     # Format code
uv run ty check .        # Run static type checker
```

### Assets & Maintenance
```bash
uv run create_samples.py # Generate test audio files & embedded ID3 artwork
uv run update_vendor.py  # Download latest Alpine.js & Tailwind CSS vendor files
uv run bump-my-version bump [patch|minor|major] # Bump version across pyproject.toml & sync
```

### Docker
```bash
docker compose up -d                              # Run pre-built container image
docker compose -f docker-compose.dev.yml up --build # Build from local source
```

## Key Files & Structure
- `main.py`: FastAPI routes, media mounting with immutable caching headers, and on-the-fly artwork extraction (`/api/cover/{id}`).
- `config.py`: Pydantic `Settings` class, environment variable defaults, extension parsers, and client config exporter.
- `templates/index.html`: Jinja2 template rendering the single-page UI, meta tags, and inline runtime config injection.
- `static/js/audio.js`: `AudioManager` handling audio element voice pooling, LRU cache eviction, loop control, and volume/mute.
- `static/js/app.js`: Alpine.js soundboard component, search, filtering, and localStorage hydration.
- `sounds/`: Audio library directory (gitignored; audio files and companion covers).

## Skills
Repository skills are located in [`.agents/skills/`](.agents/skills/). Agents must consult and follow them when performing applicable tasks:

| Skill | Reference | Description |
| :--- | :--- | :--- |
| **`conventional-commits`** | [`.agents/skills/conventional-commits/SKILL.md`](.agents/skills/conventional-commits/SKILL.md) | Strict Conventional Commits v1.0.0 guidelines (`<type>[scope]: <description>`). Mandatory for all git commit messages. |

## Guardrails & Non-Negotiables
- **Zero Frontend Build Step**: Never introduce Node.js build pipelines, Webpack, Vite, or npm scripts for frontend delivery. Use static vendored assets.
- **Read-Only Media**: Never write generated files or cached artwork into the `sounds/` directory.
- **Git Hygiene**: Never commit audio binaries or files inside `sounds/` (always ensure `sounds/` remains gitignored).
- **Mandatory Pre-Commit Verification**: Before committing any changes, agents MUST run all quality gates and resolve any open issues or diagnostics:
  ```bash
  uv run poe check       # Sequentially runs ruff check, ruff format --check, ty check, and pytest
  ```
  Fix all errors before proceeding with `git commit`.
