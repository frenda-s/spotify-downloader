#!/usr/bin/env python3
"""Render assets/banner.png used at the top of README.md.

Run with Pillow available:  .venv/bin/python tools/make_banner.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "banner.png"

BG = (11, 11, 13)
WINDOW = (18, 18, 22)
BORDER = (38, 38, 45)
GREEN = (30, 215, 96)
DIM = (150, 155, 164)
WHITE = (240, 242, 245)
RED = (255, 95, 87)
YELLOW = (254, 188, 46)

FONT_BOLD = "/home/frenda/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFont-ExtraBold.ttf"
FONT_MONO = "/home/frenda/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontMono-Regular.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def backdrop(img, draw, w, h):
    draw.rectangle([0, 0, w, h], fill=BG)
    for gx in range(0, w, 32):
        for gy in range(0, h, 32):
            draw.point((gx, gy), fill=(23, 23, 28))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-w // 4, h - h // 2, w // 2, h + h // 2], fill=(30, 215, 96, 42))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(110)))


def build():
    w, h = 1280, 400
    img = Image.new("RGBA", (w, h), BG)
    draw = ImageDraw.Draw(img)
    backdrop(img, draw, w, h)

    pad = 56
    draw.text((pad, 54), "CLI TOOL  //  PYTHON  //  MIT",
              font=font(FONT_MONO, 18), fill=DIM)

    head = font(FONT_BOLD, 54)
    draw.text((pad, 88), "SPOTIFY", font=head, fill=WHITE)
    draw.text((pad, 146), "& YOUTUBE", font=head, fill=WHITE)
    draw.text((pad, 204), "DOWNLOADER", font=head, fill=GREEN)

    sub = font(FONT_MONO, 19)
    draw.text((pad, 286), "Audio in. Artwork, tags and lyrics attached.",
              font=sub, fill=DIM)
    draw.text((pad, 316), "MP3 · M4A · FLAC · OPUS · OGG · WAV",
              font=sub, fill=(110, 115, 124))

    box = (720, 96, w - pad, 320)
    draw.rounded_rectangle(box, radius=18, fill=WINDOW, outline=BORDER, width=2)
    for i, color in enumerate((RED, YELLOW, GREEN)):
        cx, cy, r = 720 + 30 + i * 24, 126, 6
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.text((w - pad - 46, 114), "zsh", font=font(FONT_MONO, 13), fill=(90, 94, 102))

    term = font(FONT_MONO, 17)
    lines = [
        ('$ ./download.sh "spotify:album:..."', WHITE),
        ("[*] 12 tracks  ·  mp3 320 kbps", DIM),
        ("[+] cover art embedded per track", GREEN),
        ("[+] finished in 41s", GREEN),
    ]
    y = 164
    for text, color in lines:
        draw.text((744, y), text, font=term, fill=color)
        y += 32

    draw.text((w - pad - 176, 336), "frenda-s / spotify-downloader",
              font=font(FONT_MONO, 12), fill=(70, 74, 82))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT, optimize=True)
    print(f"{OUT}: {Image.open(OUT).size} {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build()
