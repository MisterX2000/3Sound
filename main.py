import logging
import os
import urllib.parse
import wave
from pathlib import Path
from typing import Any, TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mutagen import File as MutagenFile
from mutagen import MutagenError

logger = logging.getLogger("soundboard")

from config import (
    FAVICON_ICO,
    FAVICON_PNG,
    FAVICON_SVG,
    INDEX_HTML,
    MANIFEST_JSON,
    SOUNDS_DIR,
    STATIC_DIR,
    SW_JS,
    settings,
)

# Supported file formats
AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".ogg",
    ".wav",
    ".flac",
    ".aac",
    ".wma",
    ".webm",
    ".opus",
    ".aiff",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"}

# Audio duration cache: (path, mtime, size) -> duration_float
_duration_cache: dict[tuple[str, float, int], float] = {}


class FolderInfo(TypedDict):
    path: str
    name: str
    parent: str | None
    image_url: str | None
    subfolders: list[str]
    sound_ids: list[str]
    sound_count: int
    total_sound_count: int


def format_duration(seconds: float) -> str:
    """Format duration in seconds to M:SS or H:MM:SS."""
    if not seconds or seconds <= 0:
        return "0:00"
    total_seconds = round(seconds)
    if total_seconds == 0 and seconds > 0:
        total_seconds = 1
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def get_audio_duration(file_path: Path) -> float:
    """Extract audio duration using Mutagen or standard library wave parser."""
    try:
        stat = file_path.stat()
        cache_key = (str(file_path), stat.st_mtime, stat.st_size)
        if cache_key in _duration_cache:
            return _duration_cache[cache_key]

        duration = 0.0

        # Try Mutagen first (supports mp3, m4a, ogg, flac, wav, etc.)
        try:
            audio = MutagenFile(file_path)
            if audio is not None and getattr(audio, "info", None) is not None:
                duration = float(getattr(audio.info, "length", 0.0) or 0.0)
        except MutagenError, OSError, ValueError:
            duration = 0.0

        # Fallback to standard library wave module for WAV files
        if duration <= 0 and file_path.suffix.lower() == ".wav":
            try:
                with wave.open(str(file_path), "rb") as w:
                    frames = w.getnframes()
                    rate = w.getframerate()
                    if rate > 0:
                        duration = float(frames) / float(rate)
            except wave.Error, OSError:
                pass

        _duration_cache[cache_key] = duration
        return duration
    except OSError:
        return 0.0


def find_matching_image(sound_path: Path) -> str | None:
    """Find image with the same base name as the sound file in the same directory."""
    stem = sound_path.stem
    parent = sound_path.parent
    for ext in IMAGE_EXTENSIONS:
        img_candidate = parent / f"{stem}{ext}"
        if img_candidate.is_file():
            rel_path = img_candidate.relative_to(SOUNDS_DIR)
            encoded_parts = [urllib.parse.quote(part) for part in rel_path.parts]
            return f"/media/{'/'.join(encoded_parts)}"
    return None


FOLDER_COVER_NAMES = ["folder", "cover", "icon", "thumb", "thumbnail", "album"]


def find_folder_image(folder_path: Path) -> str | None:
    """Find folder cover image (e.g. folder.png, cover.jpg, icon.svg, etc.)."""
    for base in FOLDER_COVER_NAMES:
        for ext in IMAGE_EXTENSIONS:
            candidate = folder_path / f"{base}{ext}"
            if candidate.is_file():
                rel_path = candidate.relative_to(SOUNDS_DIR)
                encoded_parts = [urllib.parse.quote(part) for part in rel_path.parts]
                return f"/media/{'/'.join(encoded_parts)}"
    return None


def scan_sounds() -> dict[str, Any]:
    """Scan SOUNDS_DIR recursively and categorize sounds by subfolder, building folder hierarchy."""
    sounds: list[dict[str, Any]] = []
    categories_set: set[str] = set()
    folders: dict[str, FolderInfo] = {}
    sounds_by_folder: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(SOUNDS_DIR):
        root_path = Path(root)
        try:
            rel_dir = root_path.relative_to(SOUNDS_DIR)
        except ValueError:
            continue

        rel_str = "" if str(rel_dir) == "." else str(rel_dir).replace("\\", "/")
        category = "General" if not rel_str else " / ".join(rel_dir.parts)
        dirs.sort()
        files.sort()

        dir_sound_ids: list[str] = []

        for file_name in files:
            file_path = root_path / file_name
            ext = file_path.suffix.lower()

            if ext in AUDIO_EXTENSIONS:
                categories_set.add(category)
                rel_sound_path = file_path.relative_to(SOUNDS_DIR)
                sound_id = str(rel_sound_path).replace("\\", "/")
                encoded_sound_parts = [
                    urllib.parse.quote(part) for part in rel_sound_path.parts
                ]
                sound_url = f"/media/{'/'.join(encoded_sound_parts)}"
                image_url = find_matching_image(file_path)

                duration_sec = get_audio_duration(file_path)
                clean_title = file_path.stem.replace("_", " ").replace("-", " ").strip()

                sounds.append(
                    {
                        "id": sound_id,
                        "name": file_path.stem,
                        "title": clean_title,
                        "filename": file_name,
                        "folder": rel_str,
                        "category": category,
                        "format": ext.lstrip("."),
                        "duration": duration_sec,
                        "duration_formatted": format_duration(duration_sec),
                        "sound_url": sound_url,
                        "image_url": image_url,
                    }
                )
                dir_sound_ids.append(sound_id)

        sounds_by_folder[rel_str] = dir_sound_ids
        sub_paths = [f"{rel_str}/{d}" if rel_str else d for d in dirs]

        folders[rel_str] = {
            "path": rel_str,
            "name": root_path.name if rel_str else "All Sounds",
            "parent": str(rel_dir.parent).replace("\\", "/")
            if rel_str and str(rel_dir.parent) != "."
            else ("" if rel_str else None),
            "image_url": find_folder_image(root_path),
            "subfolders": sub_paths,
            "sound_ids": dir_sound_ids,
            "sound_count": len(dir_sound_ids),
            "total_sound_count": len(dir_sound_ids),
        }

    # Calculate recursive total sound counts for each folder
    for path, fld in folders.items():
        total = len(fld["sound_ids"])
        prefix = f"{path}/" if path else ""
        for other_path, other_sound_ids in sounds_by_folder.items():
            if other_path != path and (not path or other_path.startswith(prefix)):
                total += len(other_sound_ids)
        fld["total_sound_count"] = total

    sorted_categories = sorted(
        categories_set, key=lambda c: (c != "General", c.lower())
    )
    return {
        "categories": sorted_categories,
        "sounds": sounds,
        "folders": folders,
    }


# In-memory metadata cache: stores strictly paths and lightweight descriptors (NOT audio/image bytes)
_metadata_cache: dict[str, Any] | None = None


def get_cached_sounds(force_reload: bool = False) -> dict[str, Any]:
    """Retrieve sounds metadata from cache, rescanning filesystem only when force_reload is True or cache is empty."""
    global _metadata_cache
    if _metadata_cache is None or force_reload:
        print(
            f"[{'RELOAD' if force_reload else 'INIT'}] Scanning sounds directory from disk: {SOUNDS_DIR}"
        )
        _metadata_cache = scan_sounds()
    return _metadata_cache


# Pre-warm metadata cache on startup so the very first request is instantaneous
try:
    get_cached_sounds(force_reload=False)
except (OSError, RuntimeError) as exc:
    logger.warning("Failed to pre-warm metadata cache: %s", exc)


# ==========================================
# FastAPI Application
# ==========================================
app = FastAPI(title="Soundboard")
app.mount("/media", StaticFiles(directory=SOUNDS_DIR), name="media")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=FileResponse)
async def index():
    if not INDEX_HTML.is_file():
        raise HTTPException(status_code=404, detail="index.html template not found")
    return FileResponse(INDEX_HTML)


@app.get("/manifest.json")
async def manifest():
    if MANIFEST_JSON.is_file():
        return FileResponse(MANIFEST_JSON, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="manifest.json not found")


@app.get("/sw.js")
async def service_worker():
    if SW_JS.is_file():
        return FileResponse(
            SW_JS,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
    raise HTTPException(status_code=404, detail="sw.js not found")


@app.get("/favicon.ico")
async def favicon():
    if FAVICON_ICO.is_file():
        return FileResponse(FAVICON_ICO, media_type="image/x-icon")
    if FAVICON_PNG.is_file():
        return FileResponse(FAVICON_PNG, media_type="image/png")
    if FAVICON_SVG.is_file():
        return FileResponse(FAVICON_SVG, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="favicon not found")


@app.get("/api/sounds")
async def api_get_sounds(reload: bool = False):
    """Return cached sounds metadata. If reload=True, rescans filesystem."""
    return get_cached_sounds(force_reload=reload)


@app.api_route("/api/reload", methods=["GET", "POST"])
async def api_reload():
    """Force rescan of sounds from filesystem and refresh cache."""
    return get_cached_sounds(force_reload=True)


if __name__ == "__main__":
    import uvicorn

    print("Running with FastAPI & Uvicorn engine...")
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
