#!/usr/bin/env python3
"""Update vendor JavaScript libraries (Alpine.js) and recompile Tailwind CSS.

Zero-dependency script using standard library urllib.
Usage:
    python update_vendor.py
    uv run update_vendor.py
"""

import hashlib
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENDOR_DIR = BASE_DIR / "static" / "vendor"
CSS_DIR = BASE_DIR / "static" / "css"

VENDOR_SOURCES = {
    "alpine.min.js": {
        "url": "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
        "description": "Alpine.js (Declarative reactive UI framework)",
    },
}

USER_AGENT = "Mozilla/5.0 (compatible; SoundboardVendorUpdater/1.0)"


def download_vendor_file(filename: str, info: dict) -> bool:
    """Download vendor file from URL and save to static/vendor/ if hash changed."""
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

            final_url = response.geturl()
            if final_url != url:
                print(f"   Resolved URL: {final_url}")

            content = response.read()
            if not content:
                print("   ❌ Error: Downloaded content is empty")
                return False

            new_hash = hashlib.sha256(content).hexdigest()
            size_kb = len(content) / 1024

            if dest_path.is_file():
                old_hash = hashlib.sha256(dest_path.read_bytes()).hexdigest()
                if old_hash == new_hash:
                    print(
                        f"   ℹ️  {filename} is already up to date (SHA-256: {new_hash[:12]}..., {size_kb:.1f} KB)"
                    )
                    return True
                print(f"   🔄 Hash changed: {old_hash[:12]}... → {new_hash[:12]}...")

            dest_path.write_bytes(content)
            print(
                f"   ✅ Saved {dest_path.name} ({size_kb:.1f} KB, SHA-256: {new_hash[:12]}...)"
            )
            return True

    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"   ❌ Download failed: {exc}")
        return False


def compile_tailwind() -> bool:
    """Recompile static/css/tailwind.min.css using pytailwindcss."""
    input_css = CSS_DIR / "input.css"
    output_css = CSS_DIR / "tailwind.min.css"
    if not input_css.is_file():
        print(f"ℹ️  {input_css} not found: skipping Tailwind CSS compilation.")
        return True

    print("🎨 Compiling static/css/tailwind.min.css with Tailwind CSS...")
    try:
        import pytailwindcss
        from pytailwindcss.exceptions import PyTailwindCssException

        pytailwindcss.run(
            ["-i", str(input_css), "-o", str(output_css), "--minify"],
            cwd=BASE_DIR,
            auto_install=True,
        )
        size_kb = output_css.stat().st_size / 1024
        print(f"   ✅ Compiled {output_css.name} ({size_kb:.1f} KB)")
        return True
    except ImportError:
        print("ℹ️  pytailwindcss not installed: skipping Tailwind CSS compilation.")
        return True
    except (subprocess.CalledProcessError, PyTailwindCssException, OSError) as exc:
        print(f"   ❌ Tailwind compilation failed: {exc}")
        return False


def main():
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Updating vendor files in: {VENDOR_DIR}\n")

    success_count = 0
    for filename, info in VENDOR_SOURCES.items():
        if download_vendor_file(filename, info):
            success_count += 1
        print()

    print()
    tailwind_ok = compile_tailwind()

    total = len(VENDOR_SOURCES)
    if success_count == total and tailwind_ok:
        print("\n🎉 All vendor files & styles updated successfully!")
        return 0
    else:
        print(f"\n⚠️  Updated {success_count}/{total} vendor files. Some steps failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
