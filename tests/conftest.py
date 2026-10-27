import wave
from collections.abc import Generator
from pathlib import Path
from typing import Protocol

import pytest
from fastapi.testclient import TestClient
from starlette.staticfiles import StaticFiles

import config
import main
from main import app


class MakeWavFn(Protocol):
    def __call__(
        self, path: Path, duration_sec: float = 1.0, sample_rate: int = 44100
    ) -> Path: ...


@pytest.fixture
def make_wav() -> MakeWavFn:
    """Helper fixture to create a valid synthetic WAV audio file."""

    def _make(path: Path, duration_sec: float = 1.0, sample_rate: int = 44100) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        num_samples = int(duration_sec * sample_rate)
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * num_samples)
        return path

    return _make


@pytest.fixture
def mock_sounds_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    make_wav: MakeWavFn,
) -> Generator[Path]:
    """Set up an isolated temporary sounds directory structure with sample audio & images."""
    sounds_root = tmp_path / "sounds"
    sounds_root.mkdir(parents=True, exist_ok=True)

    # 1. Root-level sound
    make_wav(sounds_root / "root_sound.wav", duration_sec=0.5)

    # 2. General category with sound and matching image
    general_dir = sounds_root / "General"
    general_dir.mkdir(parents=True, exist_ok=True)
    make_wav(general_dir / "click.wav", duration_sec=1.2)
    (general_dir / "click.png").write_bytes(b"\x89PNG\r\n\x1a\nfake-png-data")

    # 3. UI category with folder image and sound
    ui_dir = sounds_root / "UI"
    ui_dir.mkdir(parents=True, exist_ok=True)
    make_wav(ui_dir / "pop.wav", duration_sec=2.5)
    (ui_dir / "folder.jpg").write_bytes(b"\xff\xd8\xfffake-jpg-data")

    # 4. Empty category (to verify HIDE_EMPTY_FOLDERS behavior)
    empty_dir = sounds_root / "EmptyCategory"
    empty_dir.mkdir(parents=True, exist_ok=True)

    # Patch SOUNDS_DIR in both config and main
    monkeypatch.setattr(config, "SOUNDS_DIR", sounds_root)
    monkeypatch.setattr(main, "SOUNDS_DIR", sounds_root)

    # Re-target mounted static files for /media to the isolated sounds_root
    for route in app.routes:
        if getattr(route, "name", None) == "media":
            sub_app = getattr(route, "app", None)
            if isinstance(sub_app, StaticFiles):
                sub_app.directory = str(sounds_root)

    # Reset in-memory caches
    main._metadata_cache = None
    main._audio_meta_cache.clear()

    yield sounds_root

    # Clean up caches after test
    main._metadata_cache = None
    main._audio_meta_cache.clear()


@pytest.fixture
def client(mock_sounds_env: Path) -> Generator[TestClient]:
    """FastAPI TestClient with isolated sounds directory mounted."""
    # Mount the mocked sounds directory to the test client app
    with TestClient(app) as test_client:
        yield test_client
