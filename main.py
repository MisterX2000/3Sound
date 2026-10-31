import asyncio
import base64
import json
import logging
import os
import re
import urllib.parse
import wave
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, TypedDict

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.flac import Picture
from mutagen.mp4 import MP4Cover

logger = logging.getLogger("soundboard")

from config import (
    APP_TITLE,
    APP_VERSION,
    AUDIO_EXTENSIONS,
    EXTRACT_EMBEDDED_ART,
    FAVICON_ICO,
    FAVICON_PNG,
    FAVICON_SVG,
    FOLDER_IMAGE_NAMES,
    FRONTEND_DIST,
    FRONTEND_PUBLIC,
    HIDE_EMPTY_FOLDERS,
    IMAGE_EXTENSIONS,
    MANIFEST_JSON,
    SOUNDS_DIR,
    SPA_INDEX_HTML,
    SW_JS,
    get_client_config,
    settings,
)

# Audio metadata cache: (path, mtime, size) -> (duration_float, has_embedded_cover_bool)
_audio_meta_cache: dict[tuple[str, float, int], tuple[float, bool]] = {}


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


def get_audio_info(file_path: Path) -> tuple[float, bool]:
    """Extract audio duration and check for embedded cover art using Mutagen or wave parser."""
    try:
        stat = file_path.stat()
        cache_key = (str(file_path), stat.st_mtime, stat.st_size)
        if cache_key in _audio_meta_cache:
            return _audio_meta_cache[cache_key]

        duration = 0.0
        has_cover = False

        # Try Mutagen first (supports mp3, m4a, ogg, flac, wav, etc.)
        try:
            audio = MutagenFile(file_path)
            if audio is not None:
                if getattr(audio, "info", None) is not None:
                    duration = float(getattr(audio.info, "length", 0.0) or 0.0)

                if EXTRACT_EMBEDDED_ART:
                    # Check for ID3 APIC frames or MP4 covr or Vorbis METADATA_BLOCK_PICTURE
                    if getattr(audio, "tags", None) is not None:
                        for tag in audio.tags.values():
                            if getattr(tag, "FrameID", "") == "APIC":
                                has_cover = True
                                break
                        if not has_cover and audio.tags.get("covr"):
                            has_cover = True
                        if not has_cover and audio.tags.get("METADATA_BLOCK_PICTURE"):
                            has_cover = True
                    # Check for native FLAC pictures
                    if not has_cover and getattr(audio, "pictures", None):
                        has_cover = True
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

        _audio_meta_cache[cache_key] = (duration, has_cover)
        return duration, has_cover
    except OSError:
        return 0.0, False


def extract_embedded_cover(sound_path: Path) -> tuple[str, bytes] | None:
    """Extract embedded cover image (MIME type and raw bytes) from audio metadata in-memory."""
    try:
        audio = MutagenFile(sound_path)
        if audio is None:
            return None

        # 1. ID3 tags (MP3, AIFF, etc.)
        if getattr(audio, "tags", None) is not None:
            for tag in audio.tags.values():
                if getattr(tag, "FrameID", "") == "APIC":
                    mime = getattr(tag, "mime", "image/jpeg") or "image/jpeg"
                    return mime, bytes(tag.data)

            # MP4 'covr' (M4A, MP4, ALAC)
            covr = audio.tags.get("covr")
            if covr and len(covr) > 0:
                cover = covr[0]
                imageformat = getattr(cover, "imageformat", None)
                mime = (
                    "image/png" if imageformat == MP4Cover.FORMAT_PNG else "image/jpeg"
                )
                return mime, bytes(cover)

            # Vorbis Comment METADATA_BLOCK_PICTURE (OGG, Opus, FLAC in OGG)
            mbp = audio.tags.get("METADATA_BLOCK_PICTURE")
            if mbp and len(mbp) > 0:
                pic_data = base64.b64decode(mbp[0])
                pic = Picture(pic_data)
                mime = getattr(pic, "mime", "image/jpeg") or "image/jpeg"
                return mime, pic.data

        # 2. Native FLAC pictures
        pictures = getattr(audio, "pictures", None)
        if pictures and len(pictures) > 0:
            pic = pictures[0]
            mime = getattr(pic, "mime", "image/jpeg") or "image/jpeg"
            return mime, pic.data

    except MutagenError, OSError, ValueError, KeyError:
        return None

    return None


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


def find_folder_image(folder_path: Path) -> str | None:
    """Find folder cover image (e.g. folder.png, cover.jpg, icon.svg, etc.)."""
    for base in FOLDER_IMAGE_NAMES:
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
                duration_sec, has_cover = get_audio_info(file_path)
                try:
                    sound_mtime = int(file_path.stat().st_mtime)
                except OSError:
                    sound_mtime = 0

                sound_url = f"/media/{'/'.join(encoded_sound_parts)}?v={sound_mtime}"
                image_url = find_matching_image(file_path)

                if not image_url and EXTRACT_EMBEDDED_ART and has_cover:
                    image_url = f"/api/cover/{'/'.join(encoded_sound_parts)}"

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

    # Hide empty folders if configured
    if HIDE_EMPTY_FOLDERS:
        valid_paths = {
            p for p, fld in folders.items() if not p or fld["total_sound_count"] > 0
        }
        folders = {p: fld for p, fld in folders.items() if p in valid_paths}
        for fld in folders.values():
            fld["subfolders"] = [sub for sub in fld["subfolders"] if sub in valid_paths]

    sorted_categories = sorted(
        categories_set, key=lambda c: (c != "General", c.lower())
    )
    return {
        "categories": sorted_categories,
        "sounds": sounds,
        "folders": folders,
        "version": APP_VERSION,
    }


# In-memory metadata cache: stores strictly paths and lightweight descriptors (NOT audio/image bytes)
_metadata_cache: dict[str, Any] | None = None
_scan_task: asyncio.Task[dict[str, Any]] | None = None
_scan_lock: asyncio.Lock | None = None


def get_cached_sounds(force_reload: bool = False) -> dict[str, Any]:
    """Retrieve sounds metadata synchronously from cache, rescanning filesystem if empty or force_reload is True."""
    global _metadata_cache
    if _metadata_cache is None or force_reload:
        if force_reload:
            _audio_meta_cache.clear()
        logger.info(
            "[%s] Scanning sounds directory from disk: %s",
            "RELOAD" if force_reload else "INIT",
            SOUNDS_DIR,
        )
        _metadata_cache = scan_sounds()
    return _metadata_cache


def _get_scan_lock() -> asyncio.Lock:
    global _scan_lock
    if _scan_lock is None:
        _scan_lock = asyncio.Lock()
    return _scan_lock


async def _run_scan_worker(force_reload: bool) -> dict[str, Any]:
    global _metadata_cache, _scan_task
    try:
        if force_reload:
            _audio_meta_cache.clear()
        logger.info(
            "[%s] Scanning sounds directory in background: %s",
            "RELOAD" if force_reload else "INIT",
            SOUNDS_DIR,
        )
        result = await asyncio.to_thread(scan_sounds)
        _metadata_cache = result
        return result
    except Exception:
        logger.exception("Error scanning sounds directory")
        if _metadata_cache is None:
            _metadata_cache = {
                "categories": [],
                "sounds": [],
                "folders": {},
                "version": APP_VERSION,
            }
        return _metadata_cache
    finally:
        _scan_task = None


async def get_sounds_async(force_reload: bool = False) -> dict[str, Any]:
    """Retrieve sounds metadata asynchronously.

    If a scan is already running, concurrent callers await that active scan (deduplication).
    If cache is empty or force_reload is True, an asynchronous scan task is started in a worker thread.
    """
    global _scan_task

    if _metadata_cache is not None and not force_reload:
        return _metadata_cache

    lock = _get_scan_lock()
    async with lock:
        if _metadata_cache is not None and not force_reload:
            return _metadata_cache

        if _scan_task is not None and not _scan_task.done():
            task = _scan_task
        else:
            task = asyncio.create_task(_run_scan_worker(force_reload=force_reload))
            _scan_task = task

    return await task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager kicking off asynchronous library scan on startup without blocking server bind."""
    asyncio.create_task(get_sounds_async(force_reload=False))
    yield


# ==========================================
# FastAPI Application
# ==========================================
class CachedStaticFiles(StaticFiles):
    """StaticFiles subclass that injects immutable caching headers for audio media."""

    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp


app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.mount("/media", CachedStaticFiles(directory=SOUNDS_DIR), name="media")

if (FRONTEND_DIST / "static").is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST / "static"), name="static")
elif (FRONTEND_PUBLIC / "static").is_dir():
    app.mount(
        "/static", StaticFiles(directory=FRONTEND_PUBLIC / "static"), name="static"
    )
elif FRONTEND_DIST.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="static")
elif FRONTEND_PUBLIC.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_PUBLIC), name="static")

if (FRONTEND_DIST / "assets").is_dir():
    app.mount(
        "/assets",
        CachedStaticFiles(directory=FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )


@app.get("/api/config")
async def config_endpoint():
    """Return runtime soundboard settings for the frontend client."""
    return get_client_config()


@app.get("/", response_class=HTMLResponse)
async def index():
    if SPA_INDEX_HTML.is_file():
        return FileResponse(SPA_INDEX_HTML, media_type="text/html")
    raise HTTPException(
        status_code=404,
        detail="Compiled frontend not found. Build it with 'uv run poe build-frontend'.",
    )


@app.get("/manifest.webmanifest")
async def webmanifest():
    pwa_manifest = FRONTEND_DIST / "manifest.webmanifest"
    if pwa_manifest.is_file():
        return FileResponse(pwa_manifest, media_type="application/manifest+json")
    return await manifest()


@app.get("/registerSW.js")
async def register_sw():
    reg_file = FRONTEND_DIST / "registerSW.js"
    if reg_file.is_file():
        return FileResponse(reg_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="registerSW.js not found")


WORKBOX_HASH_RE = re.compile(r"^[a-zA-Z0-9]+$")


@app.get("/workbox-{wb_hash}.js")
async def workbox_script(wb_hash: str):
    if not WORKBOX_HASH_RE.fullmatch(wb_hash):
        raise HTTPException(status_code=404, detail="Workbox script not found")

    dist_dir = FRONTEND_DIST.resolve()
    target_name = f"workbox-{wb_hash}.js"

    for file_path in dist_dir.glob("workbox-*.js"):
        if file_path.name == target_name and file_path.is_file():
            return FileResponse(
                file_path,
                media_type="application/javascript",
                headers={"Cache-Control": "public, max-age=31536000, immutable"},
            )

    raise HTTPException(status_code=404, detail="Workbox script not found")


@app.get("/manifest.json")
async def manifest():
    pwa_manifest = FRONTEND_DIST / "manifest.webmanifest"
    if pwa_manifest.is_file():
        return FileResponse(pwa_manifest, media_type="application/manifest+json")
    if not MANIFEST_JSON.is_file():
        raise HTTPException(status_code=404, detail="manifest.json not found")
    try:
        data = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        data["name"] = settings.app_title
        data["short_name"] = settings.app_title
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/manifest+json",
        )
    except json.JSONDecodeError, OSError:
        return FileResponse(MANIFEST_JSON, media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker():
    pwa_sw = FRONTEND_DIST / "sw.js"
    if pwa_sw.is_file():
        return FileResponse(
            pwa_sw,
            media_type="application/javascript",
            headers={
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
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


@app.get("/favicon.svg")
async def favicon_svg():
    if FAVICON_SVG.is_file():
        return FileResponse(FAVICON_SVG, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="favicon.svg not found")


@app.get("/favicon.png")
async def favicon_png():
    if FAVICON_PNG.is_file():
        return FileResponse(FAVICON_PNG, media_type="image/png")
    raise HTTPException(status_code=404, detail="favicon.png not found")


@app.get("/apple-touch-icon.png")
async def apple_touch_icon():
    f = FRONTEND_DIST / "apple-touch-icon.png"
    if not f.is_file():
        f = FRONTEND_PUBLIC / "apple-touch-icon.png"
    if f.is_file():
        return FileResponse(f, media_type="image/png")
    raise HTTPException(status_code=404, detail="apple-touch-icon.png not found")


@app.get("/icon-192.png")
async def icon_192():
    f = FRONTEND_DIST / "icon-192.png"
    if not f.is_file():
        f = FRONTEND_PUBLIC / "icon-192.png"
    if f.is_file():
        return FileResponse(f, media_type="image/png")
    raise HTTPException(status_code=404, detail="icon-192.png not found")


@app.get("/icon-512.png")
async def icon_512():
    f = FRONTEND_DIST / "icon-512.png"
    if not f.is_file():
        f = FRONTEND_PUBLIC / "icon-512.png"
    if f.is_file():
        return FileResponse(f, media_type="image/png")
    raise HTTPException(status_code=404, detail="icon-512.png not found")


@app.get("/api/cover/{sound_id:path}")
async def api_get_cover(sound_id: str):
    """Stream embedded cover art extracted on-the-fly from audio metadata without writing to disk."""
    if not EXTRACT_EMBEDDED_ART:
        raise HTTPException(
            status_code=404, detail="Embedded artwork extraction is disabled"
        )

    base_dir = SOUNDS_DIR.resolve()
    sound_path = (base_dir / sound_id).resolve()
    try:
        sound_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not sound_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    cover = extract_embedded_cover(sound_path)
    if not cover:
        raise HTTPException(status_code=404, detail="No embedded cover art found")

    mime, data = cover
    return Response(
        content=data,
        media_type=mime,
        headers={
            "Cache-Control": "public, max-age=604800, immutable",
        },
    )


@app.get("/api/sounds")
async def api_get_sounds(reload: bool = False):
    """Return cached sounds metadata. If reload=True or scan in progress, awaits background scan."""
    data = dict(await get_sounds_async(force_reload=reload))
    data["config"] = get_client_config()
    return data


@app.api_route("/api/reload", methods=["GET", "POST"])
async def api_reload():
    """Force rescan of sounds from filesystem and refresh cache."""
    data = dict(await get_sounds_async(force_reload=True))
    data["config"] = get_client_config()
    return data


if __name__ == "__main__":
    import uvicorn

    print("Running with FastAPI & Uvicorn engine...")
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
