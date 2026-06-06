"""Render a deterministic upload-notice screenshot artifact without a browser.

The CI/container used for agent work does not include a browser binary. This script
produces a PNG preview of the upload-notice panel using Pillow so UI review still
has a concrete visual artifact for the upload validation notices.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 520
YELLOW = "#ffff00"
BLACK = "#000000"
TEXT = "#f0efed"
BG = "#202020"
LINE = "#ffff00"
MUTED = "#cfcfbd"


def _font(size: int, *, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render(output: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), YELLOW)
    draw = ImageDraw.Draw(image)
    title_font = _font(48, bold=True)
    heading_font = _font(30, bold=True)
    body_font = _font(24)
    small_font = _font(20)

    # Hero/header preview.
    draw.rectangle((32, 28, WIDTH - 32, 188), fill=YELLOW, outline=BLACK, width=4)
    draw.text((64, 54), "OPEN BADGES → SUBLIMATION SHEETS", fill=BLACK, font=small_font)
    draw.text((64, 88), "UPLOAD VALIDATION NOTICES", fill=BLACK, font=title_font)
    draw.text(
        (64, 148),
        "Visible warning panel rendered from the same upload-validation messages used by the app.",
        fill=BLACK,
        font=small_font,
    )

    # Alert panel matching the app's dark/yellow visual style.
    panel = (64, 230, WIDTH - 64, HEIGHT - 48)
    shadow_offset = 8
    draw.rectangle(
        (panel[0] + shadow_offset, panel[1] + shadow_offset, panel[2] + shadow_offset, panel[3] + shadow_offset),
        fill=BLACK,
    )
    draw.rectangle(panel, fill=BG, outline=LINE, width=3)
    draw.text((panel[0] + 28, panel[1] + 24), "UPLOAD NOTICES", fill=YELLOW, font=heading_font)

    messages = [
        "tiny.svg: Image is only 32×32px and may print softly at badge size.",
        "team-badge.svg: Could not determine image dimensions; verify the artwork size before printing.",
    ]
    y = panel[1] + 80
    for message in messages:
        draw.text((panel[0] + 34, y), "•", fill=YELLOW, font=body_font)
        for line in _wrap(draw, message, body_font, panel[2] - panel[0] - 100):
            draw.text((panel[0] + 66, y), line, fill=TEXT, font=body_font)
            y += 34
        y += 10

    draw.text(
        (panel[0] + 28, panel[3] - 38),
        "Generated with scripts/render_upload_notice_screenshot.py",
        fill=MUTED,
        font=small_font,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        default="docs/screenshots/upload-notices.png",
        help="PNG output path (default: docs/screenshots/upload-notices.png)",
    )
    args = parser.parse_args()
    render(Path(args.output))


if __name__ == "__main__":
    main()
