"""Render a deterministic preview-tools screenshot artifact without a browser."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 680
YELLOW = "#ffff00"
BLACK = "#000000"
TEXT = "#f0efed"
BG = "#202020"
SURFACE = "#111111"
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


def _checkbox(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, font) -> None:
    draw.rectangle((x, y + 2, x + 24, y + 26), outline=YELLOW, width=3, fill=SURFACE)
    draw.line((x + 5, y + 14, x + 11, y + 21, x + 21, y + 6), fill=YELLOW, width=3)
    draw.text((x + 36, y), label, fill=TEXT, font=font)


def _input(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, suffix: str, font) -> None:
    draw.rectangle((x, y, x + 92, y + 44), outline=YELLOW, width=2, fill=SURFACE)
    draw.text((x + 18, y + 8), value, fill=TEXT, font=font)
    draw.text((x + 104, y + 8), suffix, fill=TEXT, font=font)


def render(output: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), YELLOW)
    draw = ImageDraw.Draw(image)
    title_font = _font(46, bold=True)
    heading_font = _font(30, bold=True)
    body_font = _font(24)
    small_font = _font(20)

    draw.rectangle((32, 28, WIDTH - 32, 178), fill=YELLOW, outline=BLACK, width=4)
    draw.text((64, 54), "PREVIEW MANUAL PLACEMENT TOOLS", fill=BLACK, font=small_font)
    draw.text((64, 88), "SNAP CONTROLS", fill=BLACK, font=title_font)
    draw.text((64, 144), "Deterministic artifact for grid and panel-edge snapping controls.", fill=BLACK, font=small_font)

    panel = (64, 218, WIDTH - 64, HEIGHT - 54)
    draw.rectangle((panel[0] + 8, panel[1] + 8, panel[2] + 8, panel[3] + 8), fill=BLACK)
    draw.rectangle(panel, fill=BG, outline=YELLOW, width=3)
    draw.text((panel[0] + 28, panel[1] + 24), "PREVIEW TOOLS", fill=YELLOW, font=heading_font)

    y = panel[1] + 86
    draw.text((panel[0] + 30, y + 8), "Zoom", fill=TEXT, font=body_font)
    draw.rectangle((panel[0] + 112, y + 20, panel[0] + 360, y + 28), fill=MUTED)
    draw.ellipse((panel[0] + 232, y + 10, panel[0] + 252, y + 38), fill=YELLOW)
    draw.text((panel[0] + 385, y + 8), "100%", fill=TEXT, font=body_font)

    y += 68
    _checkbox(draw, panel[0] + 30, y, "Snap to grid", body_font)
    draw.text((panel[0] + 300, y), "Grid step", fill=TEXT, font=body_font)
    _input(draw, panel[0] + 435, y - 4, "0.5", "cm", body_font)

    y += 74
    _checkbox(draw, panel[0] + 30, y, "Snap to panel edges", body_font)
    draw.text((panel[0] + 390, y), "Edge tolerance", fill=TEXT, font=body_font)
    _input(draw, panel[0] + 610, y - 4, "0.25", "cm", body_font)

    y += 74
    _checkbox(draw, panel[0] + 30, y, "High-contrast outlines", body_font)

    draw.text(
        (panel[0] + 28, panel[3] - 46),
        "Generated with scripts/render_preview_controls_screenshot.py",
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
        default="docs/screenshots/preview-snap-controls.png",
        help="PNG output path (default: docs/screenshots/preview-snap-controls.png)",
    )
    args = parser.parse_args()
    render(Path(args.output))


if __name__ == "__main__":
    main()
