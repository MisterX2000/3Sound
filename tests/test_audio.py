import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from mutagen import MutagenError
from mutagen.mp4 import MP4Cover

from main import (
    _audio_meta_cache,
    extract_embedded_cover,
    format_duration,
    get_audio_info,
)


def test_format_duration_zero_and_negative():
    assert format_duration(0.0) == "0:00"
    assert format_duration(-5.0) == "0:00"
    assert format_duration(0) == "0:00"


def test_format_duration_subsecond():
    # Any duration > 0 rounded to 0 should display as 0:01
    assert format_duration(0.3) == "0:01"


def test_format_duration_minutes_and_seconds():
    assert format_duration(5.0) == "0:05"
    assert format_duration(65.0) == "1:05"
    assert format_duration(599.0) == "9:59"


def test_format_duration_hours():
    assert format_duration(3600.0) == "1:00:00"
    assert format_duration(3665.0) == "1:01:05"
    assert format_duration(7325.0) == "2:02:05"


def test_get_audio_info_wav(tmp_path: Path, make_wav):
    wav_file = make_wav(tmp_path / "sample.wav", duration_sec=1.5, sample_rate=44100)
    _audio_meta_cache.clear()

    duration, has_cover = get_audio_info(wav_file)
    assert 1.4 <= duration <= 1.6
    assert has_cover is False

    # Second call should retrieve from cache
    cache_key = (str(wav_file), wav_file.stat().st_mtime, wav_file.stat().st_size)
    assert cache_key in _audio_meta_cache
    cached_duration, cached_cover = get_audio_info(wav_file)
    assert cached_duration == duration
    assert cached_cover == has_cover


def test_get_audio_info_nonexistent(tmp_path: Path):
    nonexistent = tmp_path / "ghost.wav"
    duration, has_cover = get_audio_info(nonexistent)
    assert duration == 0.0
    assert has_cover is False


def test_get_audio_info_mutagen_error(tmp_path: Path, make_wav):
    wav_file = make_wav(tmp_path / "error.wav", duration_sec=0.5)
    with patch("main.MutagenFile", side_effect=MutagenError("Corrupted file")):
        _audio_meta_cache.clear()
        # Should fall back to wave parser for .wav
        duration, has_cover = get_audio_info(wav_file)
        assert 0.4 <= duration <= 0.6
        assert has_cover is False


def test_extract_embedded_cover_id3_apic(tmp_path: Path):
    fake_audio = tmp_path / "track.mp3"
    fake_audio.write_bytes(b"dummy mp3 data")

    tag_mock = MagicMock()
    tag_mock.FrameID = "APIC"
    tag_mock.mime = "image/jpeg"
    tag_mock.data = b"\xff\xd8\xfffake-image-bytes"

    audio_mock = MagicMock()
    audio_mock.tags = {"APIC": tag_mock}

    with patch("main.MutagenFile", return_value=audio_mock):
        result = extract_embedded_cover(fake_audio)
        assert result is not None
        mime, data = result
        assert mime == "image/jpeg"
        assert data == b"\xff\xd8\xfffake-image-bytes"


def test_extract_embedded_cover_mp4_covr(tmp_path: Path):
    fake_audio = tmp_path / "track.m4a"
    fake_audio.write_bytes(b"dummy m4a data")

    class FakeCover(bytes):
        imageformat = MP4Cover.FORMAT_PNG

    covr_item = FakeCover(b"\x89PNGfake-data")
    audio_mock = MagicMock()
    audio_mock.tags = {"covr": [covr_item]}

    with patch("main.MutagenFile", return_value=audio_mock):
        result = extract_embedded_cover(fake_audio)
        assert result is not None
        mime, data = result
        assert mime == "image/png"
        assert data == b"\x89PNGfake-data"


def test_extract_embedded_cover_flac(tmp_path: Path):
    fake_audio = tmp_path / "track.flac"
    fake_audio.write_bytes(b"dummy flac data")

    pic_mock = MagicMock()
    pic_mock.mime = "image/png"
    pic_mock.data = b"\x89PNGflac-picture"

    audio_mock = MagicMock()
    audio_mock.tags = {}
    audio_mock.pictures = [pic_mock]

    with patch("main.MutagenFile", return_value=audio_mock):
        result = extract_embedded_cover(fake_audio)
        assert result is not None
        mime, data = result
        assert mime == "image/png"
        assert data == b"\x89PNGflac-picture"


def test_extract_embedded_cover_vorbis_comment(tmp_path: Path):
    fake_audio = tmp_path / "track.ogg"
    fake_audio.write_bytes(b"dummy ogg data")

    # Mock Picture and base64 decoding
    fake_b64 = base64.b64encode(b"raw_picture_data").decode("ascii")
    audio_mock = MagicMock()
    audio_mock.tags = {"METADATA_BLOCK_PICTURE": [fake_b64]}
    audio_mock.pictures = None

    pic_obj = MagicMock()
    pic_obj.mime = "image/jpeg"
    pic_obj.data = b"unpacked_jpeg_bytes"

    with (
        patch("main.MutagenFile", return_value=audio_mock),
        patch("main.Picture", return_value=pic_obj),
    ):
        result = extract_embedded_cover(fake_audio)
        assert result is not None
        mime, data = result
        assert mime == "image/jpeg"
        assert data == b"unpacked_jpeg_bytes"


def test_extract_embedded_cover_none(tmp_path: Path):
    fake_audio = tmp_path / "empty.wav"
    fake_audio.write_bytes(b"dummy wav data")

    with patch("main.MutagenFile", return_value=None):
        assert extract_embedded_cover(fake_audio) is None
