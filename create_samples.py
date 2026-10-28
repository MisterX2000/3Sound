import math
import struct
import wave
import zlib
from pathlib import Path

from mutagen.id3 import APIC
from mutagen.wave import WAVE

from config import SOUNDS_DIR


def create_styled_png(
    width: int = 160, height: int = 160, theme: str = "vinyl"
) -> bytes:
    """Generate a themed, high-quality PNG image in pure Python without third-party imaging dependencies."""
    raw = bytearray()
    cx, cy = width / 2.0, height / 2.0
    r_max = width / 2.2

    for y in range(height):
        raw.append(0)  # Filter byte 0 (None)
        ny = y / height
        for x in range(width):
            nx = x / width
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if theme == "vinyl":
                # Vinyl record with groove rings and center label
                if dist < 16:
                    r, g, b = 244, 63, 94  # Bright rose label
                elif dist < 24:
                    r, g, b = 251, 146, 60  # Warm orange ring
                elif dist < r_max:
                    angle = math.atan2(dy, dx)
                    reflection = math.sin(angle * 2) ** 4 * 0.25
                    groove = (int(dist) % 4 == 0) * 0.15
                    base = 0.08 + reflection + groove
                    r = int(min(255, 30 + base * 220))
                    g = int(min(255, 30 + base * 220))
                    b = int(min(255, 45 + base * 220))
                else:
                    r, g, b = (
                        int(15 + nx * 20),
                        int(15 + ny * 20),
                        int(30 + (nx + ny) * 20),
                    )
            elif theme == "lofi":
                # Sunset gradient with segmented sun disc
                sky_r = int(147 * (1 - ny) + 249 * ny)
                sky_g = int(51 * (1 - ny) + 115 * ny)
                sky_b = int(234 * (1 - ny) + 22 * ny)
                if dist < 42:
                    if y > cy and (y % 6) in (0, 1):
                        r, g, b = sky_r, sky_g, sky_b
                    else:
                        r, g, b = 254, 240, 138  # Warm sun yellow
                else:
                    r, g, b = sky_r, sky_g, sky_b
            elif theme == "arcade":
                # Emerald tech badge / diamond
                manhattan = abs(dx) + abs(dy)
                if manhattan < 48:
                    r, g, b = (240, 253, 244) if manhattan < 20 else (52, 211, 153)
                else:
                    r = int(15 + nx * 25)
                    g = int(23 + (1 - ny) * 80)
                    b = int(42 + ny * 60)
            elif theme == "cassette":
                # Retro tape body with spool holes
                if abs(dx) < 50 and abs(dy) < 32:
                    if (abs(dx - 22) < 12 and abs(dy) < 12) or (
                        abs(dx + 22) < 12 and abs(dy) < 12
                    ):
                        r, g, b = 226, 232, 240  # Reel holes
                    else:
                        r, g, b = 30, 41, 59  # Body slate
                else:
                    r = int(99 * nx + 236 * (1 - nx))
                    g = int(102 * ny + 72 * (1 - ny))
                    b = int(241 * (1 - ny) + 153 * ny)
            else:
                r, g, b = 99, 102, 241

            raw.extend([r, g, b])

    compressed = zlib.compress(bytes(raw), 9)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def embed_artwork(
    filepath: Path, image_bytes: bytes, mime: str = "image/png", desc: str = "Cover"
):
    """Embed ID3 APIC cover art chunk directly into an audio file using Mutagen."""
    audio = WAVE(str(filepath))
    if audio.tags is None:
        audio.add_tags()
    if audio.tags is not None:
        audio.tags.add(
            APIC(
                encoding=3,  # UTF-8
                mime=mime,
                type=3,  # Cover (front)
                desc=desc,
                data=image_bytes,
            )
        )
    audio.save()


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

    # 8. Ambient - 10s Ambient Drone
    def drone_10s_fn(t, dur):
        fade_in = min(1.0, t / 1.0)
        fade_out = min(1.0, max(0.0, (dur - t) / 1.5))
        env = fade_in * fade_out
        lfo = 1.0 + 0.12 * math.sin(2 * math.pi * 0.4 * t)
        val = (
            0.35 * math.sin(2 * math.pi * 220.00 * t)  # A3
            + 0.25 * math.sin(2 * math.pi * 277.18 * t)  # C#4
            + 0.25 * math.sin(2 * math.pi * 329.63 * t)  # E4
            + 0.15 * math.sin(2 * math.pi * 440.00 * t)  # A4
        )
        return val * env * lfo

    generate_wav(SOUNDS_DIR / "Ambient" / "ambient_drone_10s.wav", 10.0, drone_10s_fn)
    create_svg(
        SOUNDS_DIR / "Ambient" / "ambient_drone_10s.svg",
        "#6366f1",
        '<path d="M2 12h3l2-6 4 12 4-8 2 5 2-3h3"></path>',
        "Ambient Drone (10s)",
    )

    # 9. General - 10s Metronome / Clock Ticks
    def metronome_10s_fn(t, dur):
        frac = t % 1.0
        if frac < 0.04:
            is_final = t >= 9.0
            freq = 1760.0 if is_final else 880.0
            click_env = math.exp(-frac * 90)
            return 0.45 * math.sin(2 * math.pi * freq * frac) * click_env
        return 0.0

    generate_wav(SOUNDS_DIR / "General" / "metronome_10s.wav", 10.0, metronome_10s_fn)
    create_svg(
        SOUNDS_DIR / "General" / "metronome_10s.svg",
        "#8b5cf6",
        '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
        "Metronome (10s)",
    )

    # 10. Ambient - 30s Ocean Waves
    def ocean_30s_fn(t, dur):
        fade_in = min(1.0, t / 2.0)
        fade_out = min(1.0, max(0.0, (dur - t) / 2.5))
        env = fade_in * fade_out
        swell = (math.sin(2 * math.pi * (t / 7.0)) + 1.0) * 0.5
        noise = (
            math.sin(1237 * t)
            + math.sin(2351 * t)
            + math.sin(3499 * t)
            + math.sin(4721 * t)
            + math.sin(5867 * t)
            + math.sin(7109 * t)
        ) / 6.0
        rumble = 0.25 * math.sin(2 * math.pi * 55.0 * t) + 0.15 * math.sin(
            2 * math.pi * 82.4 * t
        )
        return ((noise * (0.15 + 0.35 * swell)) + (rumble * swell)) * env

    generate_wav(SOUNDS_DIR / "Ambient" / "ocean_waves_30s.wav", 30.0, ocean_30s_fn)
    create_svg(
        SOUNDS_DIR / "Ambient" / "ocean_waves_30s.svg",
        "#0284c7",
        '<path d="M2 13c2.5-3 5-3 7.5 0s5 3 7.5 0 5-3 7 0"></path><path d="M2 17c2.5-3 5-3 7.5 0s5 3 7.5 0 5-3 7 0"></path>',
        "Ocean Waves (30s)",
    )

    # 11. Ambient - 30s Space Melody
    chords = [
        [261.63, 329.63, 392.00, 523.25],  # Cmaj
        [220.00, 261.63, 329.63, 440.00],  # Am
        [174.61, 220.00, 261.63, 349.23],  # Fmaj
        [196.00, 246.94, 293.66, 392.00],  # Gmaj
        [164.81, 196.00, 246.94, 329.63],  # Em
        [130.81, 196.00, 261.63, 392.00],  # Cmaj resolve
    ]

    def space_30s_fn(t, dur):
        fade_in = min(1.0, t / 1.5)
        fade_out = min(1.0, max(0.0, (dur - t) / 2.0))
        master_env = fade_in * fade_out

        chord_idx = min(len(chords) - 1, int(t / 5.0))
        current_chord = chords[chord_idx]

        sub_t = t % 5.0
        note_idx = int(sub_t / 0.625) % len(current_chord)
        note_freq = current_chord[note_idx]
        note_phase = sub_t % 0.625
        note_env = math.exp(-note_phase * 4.5)

        bell = 0.35 * math.sin(2 * math.pi * note_freq * t) * note_env
        bass = 0.18 * math.sin(2 * math.pi * (current_chord[0] * 0.5) * t)

        return (bell + bass) * master_env

    generate_wav(SOUNDS_DIR / "Ambient" / "space_melody_30s.wav", 30.0, space_30s_fn)
    create_svg(
        SOUNDS_DIR / "Ambient" / "space_melody_30s.svg",
        "#ec4899",
        '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>',
        "Space Melody (30s)",
    )

    # 12. General - Vinyl Scratch (Embedded ID3 Artwork)
    # Notice: No separate .svg or .png file is created on disk to test on-the-fly artwork extraction!
    def vinyl_scratch_fn(t, dur):
        env = max(0.0, 1.0 - (t / dur) ** 1.5)
        mod = math.sin(2 * math.pi * 3.5 * t)
        carrier_freq = 600 + 400 * mod
        tone = math.sin(2 * math.pi * carrier_freq * t)
        crackle = (
            math.sin(9431 * t)
            * math.sin(3821 * t)
            * (0.2 if (int(t * 80) % 3 == 0) else 0.05)
        )
        return (0.4 * tone + 0.25 * crackle) * env

    vinyl_path = SOUNDS_DIR / "General" / "vinyl_scratch.wav"
    generate_wav(vinyl_path, 1.2, vinyl_scratch_fn)
    embed_artwork(
        vinyl_path, create_styled_png(160, 160, theme="vinyl"), desc="Vinyl Record"
    )

    # 13. General - Cassette Rewind (Embedded ID3 Artwork)
    def cassette_rewind_fn(t, dur):
        if t > dur - 0.08:
            click_t = t - (dur - 0.08)
            return 0.5 * math.sin(2 * math.pi * 300 * click_t) * math.exp(-click_t * 80)
        whir_freq = 1400 - 300 * (t / dur)
        whir = math.sin(2 * math.pi * whir_freq * t) + 0.3 * math.sin(
            2 * math.pi * (whir_freq * 2) * t
        )
        flutter = 1.0 + 0.15 * math.sin(2 * math.pi * 18 * t)
        return 0.35 * whir * flutter

    cassette_path = SOUNDS_DIR / "General" / "cassette_rewind.wav"
    generate_wav(cassette_path, 1.0, cassette_rewind_fn)
    embed_artwork(
        cassette_path,
        create_styled_png(160, 160, theme="cassette"),
        desc="Cassette Tape",
    )

    # 14. Game SFX - Arcade Fanfare (Embedded ID3 Artwork)
    def arcade_fanfare_fn(t, dur):
        notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
        note_dur = dur / len(notes)
        idx = min(len(notes) - 1, int(t / note_dur))
        freq = notes[idx]
        phase = t % note_dur
        env = (
            math.exp(-phase * 5.0)
            if idx < len(notes) - 1
            else max(0.0, 1.0 - phase / note_dur)
        )
        val = 0.35 if math.sin(2 * math.pi * freq * t) > 0 else -0.35
        return val * env

    fanfare_path = SOUNDS_DIR / "Game SFX" / "arcade_fanfare.wav"
    generate_wav(fanfare_path, 1.2, arcade_fanfare_fn)
    embed_artwork(
        fanfare_path, create_styled_png(160, 160, theme="arcade"), desc="Arcade Fanfare"
    )

    # 15. Ambient - Lofi Chill (Embedded ID3 Artwork)
    def lofi_chill_fn(t, dur):
        env = min(1.0, t * 8.0) * max(0.0, 1.0 - (t / dur) ** 0.8)
        vibrato = 1.0 + 0.02 * math.sin(2 * math.pi * 4.5 * t)
        chord = (
            0.30 * math.sin(2 * math.pi * 261.63 * vibrato * t)
            + 0.25 * math.sin(2 * math.pi * 329.63 * vibrato * t)
            + 0.20 * math.sin(2 * math.pi * 392.00 * vibrato * t)
            + 0.15 * math.sin(2 * math.pi * 493.88 * vibrato * t)
        )
        return chord * env

    lofi_path = SOUNDS_DIR / "Ambient" / "lofi_chill.wav"
    generate_wav(lofi_path, 2.5, lofi_chill_fn)
    embed_artwork(
        lofi_path, create_styled_png(160, 160, theme="lofi"), desc="Lofi Chill"
    )

    # Folder Covers for Folder View
    create_svg(
        SOUNDS_DIR / "Ambient" / "cover.svg",
        "#0f766e",
        '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>',
        "AMBIENT",
    )
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
