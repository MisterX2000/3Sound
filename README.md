# 🎵 Web Soundboard (Powered by FastAPI & Svelte 5)

A modern, fast, and responsive web soundboard built with **Python (FastAPI)**, **uv**, **Svelte 5** (Runes), **TypeScript**, and **Tailwind CSS v4**.

---

## ✨ Features

- 🗂️ **Dual Views (Flat & Folder Tree)**:
  - **Flat View**: All categories and sounds accessible at a glance with quick filter pills.
  - **Folder View**: Navigate through folders and subfolders hierarchically with breadcrumbs (`Home / Game SFX / test`) and a one-click "Up" button.
  - **Saved Preference**: Your view mode choice (Flat vs. Folders) is automatically saved in `localStorage` across browser sessions.
- 🖼️ **Matching Audio Artwork & Folder Covers**:
  - Individual sounds display matching images (`sound_name.png`, `sound_name.jpg`, etc.) or embedded ID3/FLAC/MP4 album artwork extracted on-the-fly.
  - Folders display folder cover artwork if present (e.g. `cover.png`, `cover.jpg`, `folder.png`, `folder.svg`, `icon.png`).
- ⏱️ **Audio Length Display**: Calculates and displays the duration of each sound (`0:05`, `1:32`).
- 🔊 **Wide Audio Format Support**: Plays `.mp3`, `.m4a`, `.ogg`, `.opus`, `.wav`, `.flac`, `.aac`, `.webm`, and `.aiff`.
- 🎛️ **Full Soundboard Controls**:
  - **Stop All Button** (with <kbd>Esc</kbd> shortcut) to instantly silence all playing sounds without navbar layout shift.
  - **Master Volume Slider** with percentage readout and Mute toggle.
  - **Overlap Mode Toggle**: Choose between overlapping sounds or single-play (solo) mode.
  - **Live Search**: Instant real-time search by sound name, filename, or category (press <kbd>/</kbd> to focus).
  - **Category Pills**: Filter by category or view all grouped together.
  - **Active Audio Indicator**: Real-time progress bar and state indicators on playing buttons. Click a playing sound to pause/stop it.
- ⚡ **Instant In-Memory Metadata Caching**: File paths and metadata are cached in memory on startup for instant page rendering without disk I/O. The filesystem is only scanned when you click the reload button on the web. Audio/image file bytes are never stored in memory and are streamed on-demand.
- 📱 **PWA Compatible (Installable)**: Complete Progressive Web App with service worker offline shell caching and standalone home screen installability on iOS, Android, macOS, and Windows.
- 🐳 **Docker & Docker Compose Ready**: Automated multi-stage build using `uv` and Node.js.

---

## 🚀 How to Run

### Option 1: Docker Compose (Pre-built Image)

Run immediately using the pre-built multi-arch image from GitHub Container Registry:

1. Start the container:
   ```bash
   docker compose up -d
   ```
2. Open **[http://localhost:8000](http://localhost:8000)** in your browser.

> Any files you add, remove, or modify inside `./sounds/` on your computer are reflected live in the container! Click the refresh icon in the web app to rescan anytime.

---

### Option 2: Docker Compose (Build from Source)

If you are modifying the code or Dockerfile locally:

```bash
docker compose -f docker-compose.dev.yml up --build
```

---

### Option 3: Running Locally with `uv`

1. **Install dependencies**:
   ```bash
   uv sync --dev
   cd frontend && npm install && cd ..
   ```

2. **Run the soundboard (production build)**:
   ```bash
   uv run poe start
   ```
   > **Recommended**: `uv run poe start` builds the Svelte 5 frontend with Vite into `frontend/dist/` before launching the server at http://localhost:8000.
   >
   > Alternatively, if the frontend is already built, run directly:
   > ```bash
   > uv run main.py
   > ```

3. **Run with hot-reloading (development mode)**:
   ```bash
   uv run poe dev
   ```
   > Powered by Poe the Poet running the FastAPI dev server (with hot-reload) and the Vite development server concurrently in parallel.

4. **(Optional) Generate sample sounds**:
   ```bash
   uv run poe samples
   ```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` to customize settings locally or configure them as environment variables in Docker:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SOUNDS_DIR` | `Path` | `./sounds` | Directory where audio files and folder artwork are stored |
| `HOST` | `str` | `0.0.0.0` | Development server host |
| `PORT` | `int` | `8000` | Development server port |
| `APP_TITLE` | `str` | `Soundboard` | Branding title in header, browser tab, and PWA manifest |
| `DEFAULT_VIEW_MODE` | `str` | `flat` | Default view on first open (`flat` or `folder`) |
| `DEFAULT_VOLUME` | `int` | `80` | Default master playback volume percentage on first open (`0`-`100`) |
| `DEFAULT_ALLOW_OVERLAP`| `bool` | `true` | Allow concurrent sound playback by default |
| `DEFAULT_MUTED` | `bool` | `false` | Start soundboard muted by default |
| `AUDIO_CACHE_SIZE` | `int` | `30` | Maximum number of unique sound audio element pools retained in browser memory |
| `HIDE_EMPTY_FOLDERS` | `bool` | `true` | Hide directories containing zero playable audio files |
| `EXTRACT_EMBEDDED_ART` | `bool` | `true` | Extract embedded ID3/FLAC/MP4 cover art on-the-fly |

User changes made in the web UI (view mode, volume, mute, overlap) continue to persist in the browser's `localStorage` across visits.

---

## 🎧 Adding Your Sounds & Images

1. Create a subfolder inside `sounds/` for your category, e.g. `sounds/Memes/`.
2. Add your sound file: `sounds/Memes/airhorn.mp3`.
3. (Optional) Add a picture with the same base name: `sounds/Memes/airhorn.jpg` or `airhorn.png`.
4. Click the **Rescan** button in the soundboard header!

---

## 🛠️ Task Runner (Poe the Poet)

The project includes preconfigured tasks via [Poe the Poet](https://poethepoet.natn.io/):

| Task | Command | Description |
| :--- | :--- | :--- |
| `check` | `uv run poe check` | Run all quality checks (`build-frontend`, `check-frontend`, `lint`, `format-check`, `types`, `test`) |
| `fix` | `uv run poe fix` | Automatically fix linting issues and reformat code |
| `dev` | `uv run poe dev` | Start FastAPI dev server and Vite dev server in parallel |
| `start` / `serve` | `uv run poe start` | Build frontend with Vite and start server at http://localhost:8000 |
| `build-frontend` | `uv run poe build-frontend` | Build Svelte 5 SPA with Vite into `frontend/dist/` |
| `check-frontend` | `uv run poe check-frontend` | Type-check frontend with `svelte-check` |
| `test` | `uv run poe test` | Run pytest test suite |
| `coverage` | `uv run poe coverage` | Run pytest with terminal coverage report |
| `outdated` | `uv run poe outdated` | Check for outdated dependencies (`uv tree --depth 1 --outdated`) |
| `samples` | `uv run poe samples` | Generate synthetic sample sounds & embedded artwork |
| `bump` | `uv run poe bump` | Bump version across `pyproject.toml` |

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release notes and version history.

---

## ⌨️ Keyboard Shortcuts

- <kbd>Esc</kbd> — Stop all playing sounds immediately
- <kbd>/</kbd> — Quick focus search bar
