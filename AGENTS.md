# AGENTS.md

## Project Overview
3Sound is a lightweight, responsive audio soundboard web application built with **FastAPI**, **uv**, and **Tailwind CSS**. It supports dual views (flat categories and hierarchical folder tree), on-the-fly embedded ID3/FLAC/MP4 artwork extraction, polyphonic voice pooling (up to 8 voices per sound), LRU memory management, and installable PWA offline capability.

## Technology Stack & Architecture
- **Backend**: Python 3.15+, FastAPI, Uvicorn, Mutagen (metadata & artwork parser), Pydantic Settings.
- **Frontend**: Single-page application, zero build tools. Uses precompiled static Tailwind CSS and vendored Alpine.js.
- **Audio Engine**: `AudioManager` ([`static/js/audio.js`](static/js/audio.js)) with voice pooling, LRU memory cache, and GPU-composited progress bar animations.
- **Media Storage**: The `sounds/` directory is strictly read-only at runtime with zero disk writes.

## Commands & Routines

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

## Commit Conventions
All commits must strictly follow the **Conventional Commits v1.0.0** specification. For detailed guidelines and workflow, refer to [`.agents/skills/conventional-commits/SKILL.md`](.agents/skills/conventional-commits/SKILL.md).

### Format
```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Allowed Types
| Type | Purpose | SemVer |
| :--- | :--- | :--- |
| `feat` | New feature or capability | MINOR |
| `fix` | Bug fix or patch | PATCH |
| `perf` | Performance or memory optimization | PATCH |
| `refactor` | Code restructuring without behavior change | None / PATCH |
| `style` | Formatting, whitespace, linting fixes | None |
| `docs` | Documentation updates only | None |
| `test` | Adding or updating tests | None |
| `build` | Build system, packaging, or dependency changes | None / PATCH |
| `ci` | CI/CD configuration and GitHub workflows | None |
| `chore` | Housekeeping, vendor updates, sample generation | None |

### Rules
- Use imperative, present tense in the description (e.g. `add`, `fix`, not `added`, `fixes`).
- Keep subject line ≤ 72 characters, all lowercase type/scope, no trailing period.

## Guardrails & Non-Negotiables
- **Zero Frontend Build Step**: Never introduce Node.js build pipelines, Webpack, Vite, or npm scripts for frontend delivery. Use static vendored assets.
- **Read-Only Media**: Never write generated files or cached artwork into the `sounds/` directory.
- **Git Hygiene**: Never commit audio binaries or files inside `sounds/` (always ensure `sounds/` remains gitignored).
- **Mandatory Pre-Commit Verification**: Before committing any changes, agents MUST run all quality gates and resolve any open issues or diagnostics:
  1. `uv run ruff check .` (linting)
  2. `uv run ruff format --check .` (formatting)
  3. `uv run ty check .` (type checking)
  4. `uv run pytest` (test suite & coverage)
  Fix all errors before proceeding with `git commit`.
