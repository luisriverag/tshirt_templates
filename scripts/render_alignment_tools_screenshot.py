"""Render a deterministic manual alignment-tools screenshot artifact without a browser."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 720
YELLOW = "#ffff00"
BLACK = "#000000"
TEXT = "#f0efed"
BG = "#202020"
SURFACE = "#111111"
MUTED = "#cfcfbd"
LINE = "#4b4b4b"


def _font(size: int, *, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _button(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, font) -> int:
    text_box = draw.textbbox((0, 0), label, font=font)
    width = text_box[2] - text_box[0] + 34
    draw.rectangle((x + 4, y + 4, x + width + 4, y + 46), fill=YELLOW)
    draw.rectangle((x, y, x + width, y + 42), outline=YELLOW, width=2, fill=SURFACE)
    draw.text((x + 17, y + 10), label, fill=YELLOW, font=font)
    return width


def render(output: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), YELLOW)
    draw = ImageDraw.Draw(image)
    title_font = _font(46, bold=True)
    heading_font = _font(30, bold=True)
    body_font = _font(22)
    small_font = _font(20)

    draw.rectangle((32, 28, WIDTH - 32, 182), fill=YELLOW, outline=BLACK, width=4)
    draw.text((64, 54), "PREVIEW MANUAL PLACEMENT TOOLS", fill=BLACK, font=small_font)
    draw.text((64, 90), "PANEL ALIGNMENT", fill=BLACK, font=title_font)
    draw.text(
        (64, 146),
        "Deterministic artifact for multi-select, alignment, and distribution controls.",
        fill=BLACK,
        font=small_font,
    )

    panel = (64, 222, WIDTH - 64, HEIGHT - 54)
    draw.rectangle((panel[0] + 8, panel[1] + 8, panel[2] + 8, panel[3] + 8), fill=BLACK)
    draw.rectangle(panel, fill=BG, outline=YELLOW, width=3)
    draw.text((panel[0] + 28, panel[1] + 24), "MANUAL PLACEMENT", fill=YELLOW, font=heading_font)
    draw.text(
        (panel[0] + 28, panel[1] + 70),
        "Ctrl/Shift-click badges to select a group, then drag, align, or distribute.",
        fill=TEXT,
        font=small_font,
    )

    y = panel[1] + 120
    x = panel[0] + 28
    for label in ["Reset automatic placement", "Rotate 0°", "Rotate 45°", "Rotate 90°", "Rotate -45°"]:
        width = _button(draw, x, y, label, small_font)
        x += width + 18

    y += 76
    draw.line((panel[0] + 28, y, panel[2] - 28, y), fill=LINE, width=2)
    y += 28
    x = panel[0] + 28
    row_labels = ["Align left", "Center horizontally", "Align right", "Align top"]
    for label in row_labels:
        width = _button(draw, x, y, label, body_font)
        x += width + 18

    y += 70
    x = panel[0] + 28
    for label in ["Center vertically", "Align bottom", "Distribute horizontally", "Distribute vertically"]:
        width = _button(draw, x, y, label, body_font)
        x += width + 18

    draw.text(
        (panel[0] + 28, panel[3] - 46),
        "Generated with scripts/render_alignment_tools_screenshot.py",
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
        default="docs/screenshots/alignment-tools.png",
        help="PNG output path (default: docs/screenshots/alignment-tools.png)",
    )
    args = parser.parse_args()
    render(Path(args.output))


if __name__ == "__main__":
    main()
