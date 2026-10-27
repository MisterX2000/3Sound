from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_api_sounds(client: TestClient):
    response = client.get("/api/sounds")
    assert response.status_code == 200
    data = response.json()
    assert "sounds" in data
    assert "folders" in data
    assert "categories" in data
    assert "version" in data
    assert len(data["sounds"]) >= 3


def test_api_sounds_force_reload(client: TestClient):
    response = client.get("/api/sounds?reload=true")
    assert response.status_code == 200
    data = response.json()
    assert "sounds" in data


def test_api_reload_endpoint(client: TestClient):
    # Test GET
    response_get = client.get("/api/reload")
    assert response_get.status_code == 200
    assert "sounds" in response_get.json()

    # Test POST
    response_post = client.post("/api/reload")
    assert response_post.status_code == 200
    assert "sounds" in response_post.json()


def test_api_cover_disabled(client: TestClient):
    with patch("main.EXTRACT_EMBEDDED_ART", False):
        response = client.get("/api/cover/General/click.wav")
        assert response.status_code == 404
        assert "disabled" in response.json()["detail"].lower()


def test_api_cover_path_traversal(client: TestClient):
    # Attempting to access files outside SOUNDS_DIR
    response = client.get("/api/cover/../../etc/passwd")
    assert response.status_code in (403, 404)


def test_api_cover_not_found(client: TestClient):
    response = client.get("/api/cover/nonexistent_sound.wav")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_cover_no_embedded_art(client: TestClient):
    # click.wav is a synthetic wav with no cover art
    response = client.get("/api/cover/General/click.wav")
    assert response.status_code == 404
    assert "no embedded cover" in response.json()["detail"].lower()


def test_api_cover_success(client: TestClient):
    # Mock extract_embedded_cover to simulate finding art
    with patch(
        "main.extract_embedded_cover", return_value=("image/png", b"\x89PNGfake")
    ):
        response = client.get("/api/cover/General/click.wav")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"\x89PNGfake"
        assert "public, max-age=" in response.headers.get("cache-control", "")


def test_static_routes(client: TestClient):
    # Root index
    response = client.get("/")
    assert response.status_code == 200

    # Manifest
    response_manifest = client.get("/manifest.json")
    assert response_manifest.status_code in (200, 404)

    # Service worker
    response_sw = client.get("/sw.js")
    assert response_sw.status_code in (200, 404)
    if response_sw.status_code == 200:
        assert "Service-Worker-Allowed" in response_sw.headers

    # Favicon
    response_fav = client.get("/favicon.ico")
    assert response_fav.status_code in (200, 404)


def test_index_missing_404(client: TestClient, tmp_path: Path):
    with patch("main.INDEX_HTML", tmp_path / "missing_index.html"):
        response = client.get("/")
        assert response.status_code == 404


def test_manifest_missing_404(client: TestClient, tmp_path: Path):
    with patch("main.MANIFEST_JSON", tmp_path / "missing_manifest.json"):
        response = client.get("/manifest.json")
        assert response.status_code == 404


def test_sw_missing_404(client: TestClient, tmp_path: Path):
    with patch("main.SW_JS", tmp_path / "missing_sw.js"):
        response = client.get("/sw.js")
        assert response.status_code == 404


def test_favicon_missing_404(client: TestClient, tmp_path: Path):
    with (
        patch("main.FAVICON_ICO", tmp_path / "missing.ico"),
        patch("main.FAVICON_PNG", tmp_path / "missing.png"),
        patch("main.FAVICON_SVG", tmp_path / "missing.svg"),
    ):
        response = client.get("/favicon.ico")
        assert response.status_code == 404
