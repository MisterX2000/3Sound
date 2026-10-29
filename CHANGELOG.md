# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-10-29

### Added
- **Unified Global Search**: Search bar now searches across the entire audio library (title, name, category, filename, folder path) in both Flat and Folder views.
- **URL Query Synchronization**: Search query is synced into the URL hash (`#category=All&q=...`, `#folder=...&q=...`) using `replaceState` on typing and `pushState` on navigation, fully supporting browser Back/Forward navigation.
- **Folder View Search Results**: Matching subfolders display with directory paths and matching sound cards feature quick-jump buttons to open the sound's parent folder.
- **Infinite Scrolling for Folders**: Added IntersectionObserver sentinel (`#infinite-scroll-sentinel-folder`) to Folder View search results.
- **Non-blocking Library Scan**: Instant skeleton loading UI while the server scans audio files asynchronously on startup.
- **Python-Native Tailwind CSS v4**: Migrated to `pytailwindcss` with parallel `poe dev` watcher and eliminated all Node.js / npm dependencies.
- **Vendor Integrity Detection**: Added SHA-256 hash comparison in `update_vendor.py` to prevent unnecessary file writes to Alpine.js vendor files.

### Changed
- Navigating to any category pill, folder tile, breadcrumb, or folder jump link automatically clears the active search query.
- Recommended run commands updated to `uv run poe start` (production) and `uv run poe dev` (development) across documentation.

### Fixed
- Inconsistent search outputs between Flat View, Folder View root, and subfolders.

## [0.6.0] - 2026-10-28

### Added
- **Audio Cache Size Management**: Added `AUDIO_CACHE_SIZE` environment variable and LRU cache eviction in `AudioManager` to bound browser memory usage.
- **Poe the Poet Task Runner**: Configured tasks (`poe check`, `poe dev`, `poe start`, `poe build-css`, `poe test`, etc.) in `pyproject.toml`.
- **Synthetic Sample Generator**: Added `create_samples.py` (`poe samples`) to generate test audio files with embedded ID3 artwork.
- **Assistant Guidelines**: Added `AGENTS.md` and repository skills overview table for AI pair programming.

### Changed
- Updated project dependencies to latest versions.

## [0.5.0] - 2026-10-27

### Added
- **Comprehensive Configuration**: Added Pydantic Settings and environment variable support for `SOUNDS_DIR`, `HIDE_EMPTY_FOLDERS`, `EXTRACT_EMBEDDED_ART`, audio extensions, and folder covers.
- **Automated Test Suite**: Added pytest tests with coverage reporting in GitHub Actions CI workflow.
- **Open Source License**: Added MIT License.

## [0.4.0] - 2026-10-26

### Added
- **Polyphonic Audio Engine**: Rapid trigger voice pooling (up to 8 voices per sound) with individual stop controls in `AudioManager`.
- **Footer Version Badge**: Display current app version in the footer with direct link to GitHub releases.
- **Sample Generation Scripts**: Added generators for 10s and 30s test audio files.
- **Conventional Commits**: Added conventional commits skill specification.

### Performance
- Implemented GPU-accelerated CSS progress animations with smooth 250ms opacity fade-out on stop and completion.

## [0.3.0] - 2026-10-26

### Performance
- Optimized client rendering by reducing DOM node count and tuning Alpine.js reactivity.
- Improved Tailwind CSS compilation.

### Fixed
- Fixed Ruff formatting and updated initial loading indicator text.

## [0.2.0] - 2026-10-26

### Added
- Added global search fallback in Flat and Folder views.
- Integrated `bump-my-version` for automated SemVer version bumping.
- Added Dependabot configuration (`dependabot.yml`).

### Fixed
- Fixed header badge and stop button wrapping on smaller screens.
- Fixed active border ring and pause icon persisting after "Stop All" or solo mode switches.
- Incremented Service Worker cache to v9.

## [0.1.0] - 2026-10-26

### Added
- Initial release of 3Sound web soundboard.
- FastAPI backend with in-memory metadata scanning and on-the-fly artwork extraction.
- Dual view interface: Flat category view and hierarchical folder tree view.
- PWA support with service worker offline shell caching and web manifest.
- Multi-arch Docker container images published to GitHub Container Registry (GHCR).
- GitHub Actions CI workflow for linting and type checking.

[Unreleased]: https://github.com/MisterX2000/3Sound/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/MisterX2000/3Sound/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/MisterX2000/3Sound/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/MisterX2000/3Sound/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/MisterX2000/3Sound/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/MisterX2000/3Sound/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/MisterX2000/3Sound/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/MisterX2000/3Sound/releases/tag/v0.1.0
