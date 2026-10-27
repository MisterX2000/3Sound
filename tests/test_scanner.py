from pathlib import Path
from unittest.mock import patch

from main import (
    find_folder_image,
    find_matching_image,
    get_cached_sounds,
    scan_sounds,
)


def test_find_matching_image(mock_sounds_env: Path):
    click_wav = mock_sounds_env / "General" / "click.wav"
    image_url = find_matching_image(click_wav)
    assert image_url == "/media/General/click.png"

    # Root sound has no matching image
    root_wav = mock_sounds_env / "root_sound.wav"
    assert find_matching_image(root_wav) is None


def test_find_folder_image(mock_sounds_env: Path):
    ui_dir = mock_sounds_env / "UI"
    folder_url = find_folder_image(ui_dir)
    assert folder_url == "/media/UI/folder.jpg"

    general_dir = mock_sounds_env / "General"
    assert find_folder_image(general_dir) is None


def test_scan_sounds_hierarchy(mock_sounds_env: Path):
    result = scan_sounds()

    assert "sounds" in result
    assert "folders" in result
    assert "categories" in result
    assert "version" in result

    sounds = result["sounds"]
    sound_ids = [s["id"] for s in sounds]

    assert "root_sound.wav" in sound_ids
    assert "General/click.wav" in sound_ids
    assert "UI/pop.wav" in sound_ids

    # Title cleanup check (e.g. root_sound -> root sound)
    root_sound_meta = next(s for s in sounds if s["id"] == "root_sound.wav")
    assert root_sound_meta["title"] == "root sound"

    folders = result["folders"]
    assert "" in folders  # Root folder
    assert "General" in folders
    assert "UI" in folders

    # Verify total sound count calculation
    assert folders[""]["total_sound_count"] == 3
    assert folders["General"]["total_sound_count"] == 1
    assert folders["UI"]["total_sound_count"] == 1


def test_scan_sounds_hide_empty_folders(mock_sounds_env: Path):
    # With HIDE_EMPTY_FOLDERS = True (default)
    with patch("main.HIDE_EMPTY_FOLDERS", True):
        result = scan_sounds()
        assert "EmptyCategory" not in result["folders"]

    # With HIDE_EMPTY_FOLDERS = False
    with patch("main.HIDE_EMPTY_FOLDERS", False):
        result = scan_sounds()
        assert "EmptyCategory" in result["folders"]


def test_get_cached_sounds(mock_sounds_env: Path, make_wav):
    # Initial scan
    data1 = get_cached_sounds(force_reload=True)
    initial_count = len(data1["sounds"])

    # Add a new sound file directly to disk without reloading cache
    new_sound = mock_sounds_env / "General" / "laser.wav"
    make_wav(new_sound, duration_sec=0.8)

    # Calling without force_reload should return cached data (no new sound)
    data2 = get_cached_sounds(force_reload=False)
    assert len(data2["sounds"]) == initial_count

    # Calling with force_reload=True should reflect the new sound
    data3 = get_cached_sounds(force_reload=True)
    assert len(data3["sounds"]) == initial_count + 1
    assert any(s["id"] == "General/laser.wav" for s in data3["sounds"])
