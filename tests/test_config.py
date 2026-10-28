from pathlib import Path
from unittest.mock import patch

from config import (
    Settings,
    _load_app_version,
    get_settings,
    parse_extensions,
    parse_names,
)


def test_parse_extensions_normal():
    result = parse_extensions(".mp3, WAV,  ogg , .FLAC ")
    assert result == {".mp3", ".wav", ".ogg", ".flac"}


def test_parse_extensions_missing_dots():
    result = parse_extensions("mp3, wav, flac")
    assert result == {".mp3", ".wav", ".flac"}


def test_parse_extensions_empty_and_whitespace():
    assert parse_extensions("") == set()
    assert parse_extensions("  , ,   ") == set()


def test_parse_names():
    result = parse_names("Folder, COVER,  icon , thumb ")
    assert result == ["folder", "cover", "icon", "thumb"]
    assert parse_names("") == []
    assert parse_names("  , ,  ") == []


def test_load_app_version_valid(tmp_path: Path):
    fake_pyproject = tmp_path / "pyproject.toml"
    fake_pyproject.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    with patch("config.BASE_DIR", tmp_path):
        assert _load_app_version() == "1.2.3"


def test_load_app_version_missing_file(tmp_path: Path):
    with patch("config.BASE_DIR", tmp_path):
        assert _load_app_version() == "0.0.0"


def test_load_app_version_corrupt_toml(tmp_path: Path):
    fake_pyproject = tmp_path / "pyproject.toml"
    fake_pyproject.write_text("corrupted toml [[ [", encoding="utf-8")
    with patch("config.BASE_DIR", tmp_path):
        assert _load_app_version() == "0.0.0"


def test_settings_defaults():
    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.hide_empty_folders is True
    assert s.extract_embedded_art is True
    assert s.app_title == "Soundboard"
    assert s.default_view_mode == "flat"
    assert s.default_volume == 80
    assert s.default_allow_overlap is True
    assert s.default_muted is False
    assert ".mp3" in s.audio_extensions
    assert "folder" in s.folder_image_names


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("PORT", "9999")
    monkeypatch.setenv("HIDE_EMPTY_FOLDERS", "false")
    monkeypatch.setenv("APP_TITLE", "Custom Audio Hub")
    monkeypatch.setenv("DEFAULT_VIEW_MODE", "folder")
    monkeypatch.setenv("DEFAULT_VOLUME", "65")
    monkeypatch.setenv("DEFAULT_ALLOW_OVERLAP", "false")
    monkeypatch.setenv("DEFAULT_MUTED", "true")
    s = Settings()
    assert s.port == 9999
    assert s.hide_empty_folders is False
    assert s.app_title == "Custom Audio Hub"
    assert s.default_view_mode == "folder"
    assert s.default_volume == 65
    assert s.default_allow_overlap is False
    assert s.default_muted is True


def test_settings_validation():
    # Case-insensitive valid view mode
    s1 = Settings(default_view_mode="FOLDER")
    assert s1.default_view_mode == "folder"

    # Invalid view mode falls back to flat
    s2 = Settings(default_view_mode="invalid_view")
    assert s2.default_view_mode == "flat"

    # Clamping volume under 0
    s3 = Settings(default_volume=-10)
    assert s3.default_volume == 0

    # Clamping volume over 100
    s4 = Settings(default_volume=150)
    assert s4.default_volume == 100


def test_get_client_config():
    from config import get_client_config

    s = Settings(
        app_title="Test Board",
        default_view_mode="folder",
        default_volume=50,
        default_allow_overlap=False,
        default_muted=True,
    )
    cfg = get_client_config(s)
    assert cfg == {
        "app_title": "Test Board",
        "default_view_mode": "folder",
        "default_volume": 50,
        "default_allow_overlap": False,
        "default_muted": True,
    }


def test_get_settings_cached():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
