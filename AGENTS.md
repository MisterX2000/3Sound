# AGENTS.md

## Project Overview
3Sound is a lightweight, responsive audio soundboard web application built with **FastAPI**, **uv**, and **Tailwind CSS**. It supports dual views (flat categories and hierarchical folder tree), on-the-fly embedded ID3/FLAC/MP4 artwork extraction, polyphonic voice pooling (up to 8 voices per sound), LRU memory management, and installable PWA offline capability.

## Technology Stack & Architecture
- **Backend**: Python 3.15+, FastAPI, Uvicorn, Mutagen (metadata & artwork parser), Pydantic Settings.
- **Frontend**: Single-page application built with **Svelte 5** (Runes), **TypeScript**, **Vite**, **Tailwind CSS v4** (`@tailwindcss/vite`), **@lucide/svelte**, and **vite-plugin-pwa**. Located in `frontend/`.
- **Audio Engine**: `AudioState` ([`frontend/src/lib/audio.svelte.ts`](frontend/src/lib/audio.svelte.ts)) with polyphonic voice pooling, LRU memory cache, and GPU-composited progress bar animations.
- **Media Storage**: The `sounds/` directory is strictly read-only at runtime with zero disk writes.

## Commands & Routines

### Task Runner (Poe the Poet)
```bash
uv run poe check         # Run all quality checks (build-frontend, check-frontend, lint, format-check, types, test)
uv run poe fix           # Automatically fix lint violations and reformat code
uv run poe dev           # Launch FastAPI backend and Vite dev server concurrently
uv run poe start         # Build frontend with Vite and launch server at http://localhost:8000
uv run poe build-frontend# Build Svelte 5 SPA with Vite
uv run poe check-frontend# Type-check frontend with svelte-check
uv run poe test          # Run automated test suite
uv run poe coverage      # Run test suite with terminal coverage report
uv run poe outdated      # Check for outdated dependencies (uv tree --depth 1 --outdated)
uv run poe samples       # Generate test audio files & embedded ID3 artwork
uv run poe bump [patch|minor|major] # Bump version across pyproject.toml & sync
```

### Environment & Installation
```bash
uv sync --dev            # Install Python dependencies and development tools
cd frontend && npm install # Install frontend dependencies
```

### Development & Execution
```bash
uv run poe start         # Recommended: Build Svelte SPA and launch server at http://localhost:8000
uv run poe dev           # Launch FastAPI dev server and Vite dev server concurrently
```

### Testing & Code Quality
```bash
uv run poe check         # Run full frontend and backend verification gate
uv run pytest            # Execute full Python test suite
uv run ruff check .      # Run Python linter
uv run ruff format .     # Format Python code
uv run ty check .        # Run Python static type checker
cd frontend && npm run check # Run svelte-check
```

### Assets & Maintenance
```bash
uv run create_samples.py # Generate test audio files & embedded ID3 artwork
uv run bump-my-version bump [patch|minor|major] # Bump version across pyproject.toml & sync
```

### Docker
```bash
docker compose up -d                              # Run pre-built container image
docker compose -f docker-compose.dev.yml up --build # Build from local source
```

## Key Files & Structure
- `main.py`: FastAPI routes, media mounting with immutable caching headers, on-the-fly artwork extraction (`/api/cover/{id}`), runtime config (`/api/config`), and compiled SPA delivery.
- `config.py`: Pydantic `Settings` class, environment variable defaults, extension parsers, and client config exporter.
- `frontend/src/App.svelte`: Root Svelte 5 soundboard component, routing, global shortcuts, and view orchestration.
- `frontend/src/lib/audio.svelte.ts`: Svelte 5 Rune-based audio engine handling voice pooling, LRU cache eviction, loop control, and volume/mute.
- `frontend/src/lib/components/`: Modular UI components (`Header.svelte`, `SoundCard.svelte`, `FolderCard.svelte`, `FlatView.svelte`, `FolderView.svelte`, `EmptySearch.svelte`, `Toast.svelte`).
- `sounds/`: Audio library directory (gitignored; audio files and companion covers).

## Skills
Repository skills are located in [`.agents/skills/`](.agents/skills/). Agents must consult and follow them when performing applicable tasks:

| Skill | Reference | Description |
| :--- | :--- | :--- |
| **`conventional-commits`** | [`.agents/skills/conventional-commits/SKILL.md`](.agents/skills/conventional-commits/SKILL.md) | Strict Conventional Commits v1.0.0 guidelines (`<type>[scope]: <description>`). Mandatory for all git commit messages. |

## Guardrails & Non-Negotiables
- **Frontend Build Pipeline**: All frontend code lives in `frontend/` and compiles via Vite to `frontend/dist/`.
- **Read-Only Media**: Never write generated files or cached artwork into the `sounds/` directory.
- **Git Hygiene**: Never commit audio binaries or files inside `sounds/` (always ensure `sounds/` remains gitignored).
- **Mandatory Pre-Commit Verification**: Before committing any changes, agents MUST run all quality gates and resolve any open issues or diagnostics:
  ```bash
  uv run poe check       # Sequentially runs build-frontend, check-frontend, ruff check, ruff format --check, ty check, and pytest
  ```
  Fix all errors before proceeding with `git commit`.
