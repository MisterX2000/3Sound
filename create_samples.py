import math
import struct
import wave
from pathlib import Path

from config import SOUNDS_DIR


def generate_wav(filepath: Path, duration_sec: float, generator_fn, sample_rate=44100):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)

    with wave.open(str(filepath), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            sample_val = generator_fn(t, duration_sec)
            # Clamp between -1.0 and 1.0
            sample_val = max(-1.0, min(1.0, sample_val))
            # 16-bit signed integer (-32767 to 32767)
            int_sample = int(sample_val * 32767)
            frames.extend(struct.pack("<h", int_sample))

        wav_file.writeframes(frames)


def create_svg(filepath: Path, bg_color: str, icon_svg: str, label: str):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_color}" stop-opacity="0.9" />
      <stop offset="100%" stop-color="#090d16" stop-opacity="1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad)" />
  <g transform="translate(160, 90) scale(3.5)" stroke="#ffffff" fill="none" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    {icon_svg}
  </g>
  <text x="200" y="240" font-family="system-ui, -apple-system, sans-serif" font-size="20" font-weight="600" fill="#f8fafc" text-anchor="middle">
    {label}
  </text>
</svg>"""
    filepath.write_text(svg_content, encoding="utf-8")


def main():
    print(f"Generating sample sounds in {SOUNDS_DIR}...")

    # 1. General - Welcome Chime
    def chime_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur))
        freq = 523.25 if t < 0.3 else (659.25 if t < 0.6 else 783.99)
        return 0.5 * math.sin(2 * math.pi * freq * t) * env

    generate_wav(SOUNDS_DIR / "General" / "welcome_chime.wav", 1.2, chime_fn)
    create_svg(
        SOUNDS_DIR / "General" / "welcome_chime.svg",
        "#4f46e5",
        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path>',
        "Welcome Chime",
    )

    # 2. General - Synth Beep (no image to test fallback image handling)
    def beep_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur))
        return 0.4 * math.sin(2 * math.pi * 880 * t) * env

    generate_wav(SOUNDS_DIR / "General" / "synth_beep.wav", 0.4, beep_fn)

    # 3. Game SFX - Coin
    def coin_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur) ** 0.5)
        freq = 987.77 if t < 0.08 else 1318.51
        return 0.4 * math.sin(2 * math.pi * freq * t) * env

    generate_wav(SOUNDS_DIR / "Game SFX" / "retro_coin.wav", 0.5, coin_fn)
    create_svg(
        SOUNDS_DIR / "Game SFX" / "retro_coin.svg",
        "#eab308",
        '<circle cx="12" cy="12" r="9"></circle><path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"></path><path d="M12 6v2m0 8v2"></path>',
        "Retro Coin",
    )

    # 4. Game SFX - Laser
    def laser_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur))
        freq = 1200 - (1000 * (t / dur))
        return 0.4 * math.sin(2 * math.pi * freq * t) * env

    generate_wav(SOUNDS_DIR / "Game SFX" / "laser_blast.wav", 0.35, laser_fn)
    create_svg(
        SOUNDS_DIR / "Game SFX" / "laser_blast.svg",
        "#ef4444",
        '<line x1="4" y1="12" x2="20" y2="12"></line><line x1="14" y1="6" x2="20" y2="12"></line><line x1="14" y1="18" x2="20" y2="12"></line>',
        "Laser Blast",
    )

    # 5. Game SFX - Jump
    def jump_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur))
        freq = 200 + (600 * (t / dur))
        return 0.4 * math.sin(2 * math.pi * freq * t) * env

    generate_wav(SOUNDS_DIR / "Game SFX" / "jump_chirp.wav", 0.3, jump_fn)
    create_svg(
        SOUNDS_DIR / "Game SFX" / "jump_chirp.svg",
        "#10b981",
        '<path d="M12 19V5M5 12l7-7 7 7"></path>',
        "Jump",
    )

    # 6. Alerts - Airhorn Blast
    def airhorn_fn(t, dur):
        env = min(1.0, t * 20) * max(0.0, 1.0 - (t / dur) ** 2)
        freq = 466.16  # Bb4
        # Add harmonics for brassy horn buzz
        val = (
            0.5 * math.sin(2 * math.pi * freq * t)
            + 0.3 * math.sin(2 * math.pi * (freq * 2) * t)
            + 0.2 * math.sin(2 * math.pi * (freq * 3) * t)
        )
        return val * env

    generate_wav(SOUNDS_DIR / "Alerts" / "airhorn_blast.wav", 0.9, airhorn_fn)
    create_svg(
        SOUNDS_DIR / "Alerts" / "airhorn_blast.svg",
        "#f97316",
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>',
        "Airhorn Blast",
    )

    # 7. Alerts - Success Chime
    def success_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur))
        freq = 587.33 if t < 0.2 else (739.99 if t < 0.4 else 880.00)
        return 0.4 * math.sin(2 * math.pi * freq * t) * env

    generate_wav(SOUNDS_DIR / "Alerts" / "success_chord.wav", 1.0, success_fn)
    create_svg(
        SOUNDS_DIR / "Alerts" / "success_chord.svg",
        "#06b6d4",
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
        "Success Chord",
    )

    # Folder Covers for Folder View
    create_svg(
        SOUNDS_DIR / "Alerts" / "cover.svg",
        "#ea580c",
        '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path>',
        "ALERTS",
    )
    create_svg(
        SOUNDS_DIR / "Game SFX" / "cover.svg",
        "#7c3aed",
        '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 12h4m-2-2v4m7-3h.01m3 2h.01"></path>',
        "GAME SFX",
    )
    create_svg(
        SOUNDS_DIR / "Game SFX" / "test" / "cover.svg",
        "#059669",
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>',
        "TEST SFX",
    )
    create_svg(
        SOUNDS_DIR / "General" / "cover.svg",
        "#2563eb",
        '<path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"></path>',
        "GENERAL",
    )

    print("Sample sounds & artwork created successfully!")


if __name__ == "__main__":
    main()
