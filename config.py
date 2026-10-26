from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


settings = get_settings()

# Path configurations
SOUNDS_DIR = settings.sounds_dir.resolve()
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = TEMPLATES_DIR / "index.html"
MANIFEST_JSON = STATIC_DIR / "manifest.json"
SW_JS = STATIC_DIR / "sw.js"
FAVICON_ICO = STATIC_DIR / "favicon.ico"
FAVICON_SVG = STATIC_DIR / "favicon.svg"
FAVICON_PNG = STATIC_DIR / "favicon.png"

# Ensure directories exist
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
