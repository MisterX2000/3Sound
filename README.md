# 🎵 Web Soundboard (Powered by uv & FastAPI)

A modern, fast, and responsive web soundboard built with **Python (FastAPI)**, **uv**, and **Tailwind CSS**.

---

## ✨ Features

- 🗂️ **Dual Views (Flat & Folder Tree)**:
  - **Flat View**: All categories and sounds accessible at a glance with quick filter pills.
  - **Folder View**: Navigate through folders and subfolders hierarchically with breadcrumbs (`Home / Game SFX / test`) and a one-click "Up" button.
  - **Saved Preference**: Your view mode choice (Flat vs. Folders) is automatically saved in `localStorage` across browser sessions.
- 🖼️ **Matching Audio Artwork & Folder Covers**:
  - Individual sounds display matching images (`sound_name.png`, `sound_name.jpg`, etc.).
  - Folders display folder cover artwork if present (e.g. `cover.png`, `cover.jpg`, `folder.png`, `folder.svg`, `icon.png`).
- ⏱️ **Audio Length Display**: Calculates and displays the duration of each sound (`0:05`, `1:32`).
- 🔊 **Wide Audio Format Support**: Plays `.mp3`, `.m4a`, `.ogg`, `.opus`, `.wav`, `.flac`, `.aac`, `.webm`, and `.aiff`.
- 🎛️ **Full Soundboard Controls**:
  - **Stop All Button** (with <kbd>Esc</kbd> shortcut) to instantly silence all playing sounds.
  - **Master Volume Slider** and Mute toggle.
  - **Overlap Mode Toggle**: Choose between overlapping sounds or single-play (solo) mode.
  - **Live Search**: Instant real-time search by sound name, filename, or category (press <kbd>/</kbd> to focus).
  - **Category Pills**: Filter by category or view all grouped together.
  - **Active Audio Indicator**: Glowing pulse and real-time progress bar on playing buttons. Click a playing sound to pause/stop it.
- ⚡ **Instant In-Memory Metadata Caching**: File paths and metadata are cached in memory on startup for instant page rendering without disk I/O. The filesystem is only scanned when you click the reload button on the web. Audio/image file bytes are never stored in memory and are streamed on-demand.
- 📱 **PWA Compatible (Installable)**: Complete Progressive Web App with a custom high-resolution favicon, web app manifest (`manifest.json`), service worker (`sw.js`) for offline shell caching, and standalone home screen installability on iOS, Android, macOS, and Windows.
- 🐳 **Docker & Docker Compose Ready**: Automated multi-stage build using `uv`.

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

If you are modifying the backend code or Dockerfile locally:

```bash
docker compose -f docker-compose.dev.yml up --build
```

---

### Option 3: Running Locally with `uv`

1. **Run the soundboard**:
   ```bash
   uv run main.py
   ```
   > `uv` will automatically create the virtual environment, install FastAPI, Uvicorn, Mutagen, and launch the server. No manual `pip install` or `source .venv/bin/activate` needed!

2. **(Optional) Run with hot-reloading (development mode)**:
   ```bash
   uv run fastapi dev main.py
   ```
   > Powered by the modern FastAPI CLI with auto-reload, interactive docs, and diagnostics.

3. **(Optional) Generate sample sounds**:
   ```bash
   uv run create_samples.py
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

## 🔄 Updating Vendor Libraries

The application has zero build steps and runs 100% locally/offline with vendored Alpine.js and Tailwind CSS. To refresh or update these libraries from upstream:

```bash
uv run update_vendor.py
```

---

## 🛠️ Task Runner (Poe the Poet)

The project includes preconfigured tasks via [Poe the Poet](https://poethepoet.natn.io/):

| Task | Command | Description |
| :--- | :--- | :--- |
| `check` | `uv run poe check` | Run all quality checks (`lint`, `format-check`, `types`, `test`) |
| `fix` | `uv run poe fix` | Automatically fix linting issues and reformat code |
| `dev` | `uv run poe dev` | Start development server with auto-reload |
| `start` / `serve` | `uv run poe start` | Start server at http://localhost:8000 |
| `test` | `uv run poe test` | Run pytest test suite |
| `coverage` | `uv run poe coverage` | Run pytest with terminal coverage report |
| `outdated` | `uv run poe outdated` | Check for outdated dependencies (`uv tree --depth 1 --outdated`) |
| `samples` | `uv run poe samples` | Generate synthetic sample sounds & embedded artwork |
| `vendor` | `uv run poe vendor` | Download latest Alpine.js & Tailwind vendor assets |
| `bump` | `uv run poe bump` | Bump version across `pyproject.toml` |

---

## ⌨️ Keyboard Shortcuts

- <kbd>Esc</kbd> — Stop all playing sounds immediately
- <kbd>/</kbd> — Quick focus search bar
