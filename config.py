import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


def _load_app_version() -> str:
    """Read the application version from pyproject.toml."""
    pyproject_file = BASE_DIR / "pyproject.toml"
    if pyproject_file.is_file():
        try:
            with open(pyproject_file, "rb") as f:
                data = tomllib.load(f)
                return str(data.get("project", {}).get("version", "0.0.0"))
        except OSError, tomllib.TOMLDecodeError:
            return "0.0.0"
    return "0.0.0"


APP_VERSION = _load_app_version()


class Settings(BaseSettings):
    """Application runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sounds_dir: Path = BASE_DIR / "sounds"
    host: str = "0.0.0.0"
    port: int = 8000
    audio_extensions: str = ".mp3,.m4a,.ogg,.wav,.flac,.aac,.wma,.webm,.opus,.aiff"
    folder_image_names: str = "folder,cover,icon,thumb,thumbnail,album"
    hide_empty_folders: bool = True
    extract_embedded_art: bool = True
    app_title: str = "Soundboard"
    default_view_mode: str = "flat"
    default_volume: int = 80
    default_allow_overlap: bool = True
    default_muted: bool = False
    audio_cache_size: int = 30

    @field_validator("default_view_mode")
    @classmethod
    def validate_view_mode(cls, v: str) -> str:
        clean = (v or "").strip().lower()
        return clean if clean in {"flat", "folder"} else "flat"

    @field_validator("default_volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        return max(0, min(100, int(v)))

    @field_validator("audio_cache_size")
    @classmethod
    def validate_audio_cache_size(cls, v: int) -> int:
        return max(1, min(500, int(v)))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


settings = get_settings()

# Path configurations
SOUNDS_DIR = settings.sounds_dir.resolve()
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_PUBLIC = FRONTEND_DIR / "public"
FRONTEND_DIST = FRONTEND_DIR / "dist"
SPA_INDEX_HTML = FRONTEND_DIST / "index.html"
STATIC_DIR = FRONTEND_DIST / "static"
MANIFEST_JSON = FRONTEND_DIST / "manifest.webmanifest"
SW_JS = FRONTEND_DIST / "sw.js"
FAVICON_ICO = FRONTEND_DIST / "favicon.ico"
FAVICON_SVG = FRONTEND_DIST / "favicon.svg"
FAVICON_PNG = FRONTEND_DIST / "favicon.png"


# File format & scanner configurations
def parse_extensions(ext_str: str) -> set[str]:
    """Parse comma-separated audio extensions, ensuring leading dot and lowercase."""
    extensions: set[str] = set()
    for item in ext_str.split(","):
        cleaned = item.strip().lower()
        if not cleaned:
            continue
        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"
        extensions.add(cleaned)
    return extensions


def parse_names(names_str: str) -> list[str]:
    """Parse comma-separated names, lowercased and stripped."""
    return [name.strip().lower() for name in names_str.split(",") if name.strip()]


AUDIO_EXTENSIONS = parse_extensions(settings.audio_extensions)
FOLDER_IMAGE_NAMES = parse_names(settings.folder_image_names)
HIDE_EMPTY_FOLDERS = settings.hide_empty_folders
EXTRACT_EMBEDDED_ART = settings.extract_embedded_art
APP_TITLE = settings.app_title
DEFAULT_VIEW_MODE = settings.default_view_mode
DEFAULT_VOLUME = settings.default_volume
DEFAULT_ALLOW_OVERLAP = settings.default_allow_overlap
DEFAULT_MUTED = settings.default_muted
AUDIO_CACHE_SIZE = settings.audio_cache_size
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"}


def get_client_config(current_settings: Settings | None = None) -> dict[str, Any]:
    """Return dictionary of frontend client configuration."""
    s = current_settings or get_settings()
    return {
        "app_title": s.app_title,
        "default_view_mode": s.default_view_mode,
        "default_volume": s.default_volume,
        "default_allow_overlap": s.default_allow_overlap,
        "default_muted": s.default_muted,
        "audio_cache_size": s.audio_cache_size,
    }


# Ensure directories exist
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)
FRONTEND_DIST.mkdir(parents=True, exist_ok=True)
