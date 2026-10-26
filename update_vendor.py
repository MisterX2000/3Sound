#!/usr/bin/env python3
"""Update vendor JavaScript libraries (Alpine.js and Tailwind CSS) in static/vendor/.

Zero-dependency script using standard library urllib.
Usage:
    python update_vendor.py
    uv run update_vendor.py
"""

import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / "static" / "vendor"

VENDOR_SOURCES = {
    "alpine.min.js": {
        "url": "https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js",
        "description": "Alpine.js (Declarative reactive UI framework)",
    },
    "tailwindcss.js": {
        "url": "https://cdn.tailwindcss.com",
        "description": "Tailwind CSS (Standalone browser runtime)",
    },
}

USER_AGENT = "Mozilla/5.0 (compatible; SoundboardVendorUpdater/1.0)"


def download_vendor_file(filename: str, info: dict) -> bool:
    """Download vendor file from URL and save to static/vendor/."""
    url = info["url"]
    desc = info["description"]
    dest_path = VENDOR_DIR / filename

    print(f"📦 Fetching {filename} ({desc})...")
    print(f"   URL: {url}")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                print(f"   ❌ HTTP Error: Received status code {response.status}")
                return False

            content = response.read()
            if not content:
                print("   ❌ Error: Downloaded content is empty")
                return False

            dest_path.write_bytes(content)
            size_kb = len(content) / 1024
            print(f"   ✅ Saved {dest_path.name} ({size_kb:.1f} KB)")
            return True

    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"   ❌ Download failed: {exc}")
        return False


def main():
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Updating vendor files in: {VENDOR_DIR}\n")

    success_count = 0
    for filename, info in VENDOR_SOURCES.items():
        if download_vendor_file(filename, info):
            success_count += 1
        print()

    total = len(VENDOR_SOURCES)
    if success_count == total:
        print(f"🎉 All {total} vendor files updated successfully!")
        return 0
    else:
        print(
            f"⚠️  Updated {success_count}/{total} vendor files. Some downloads failed."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
