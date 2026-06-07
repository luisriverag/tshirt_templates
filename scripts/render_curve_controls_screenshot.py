"""Render a deterministic curve-controls screenshot artifact without a browser."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 620
YELLOW = "#ffff00"
BLACK = "#000000"
TEXT = "#f0efed"
BG = "#202020"
SURFACE = "#111111"
MUTED = "#cfcfbd"
BLUE = "#2f80ed"


def _font(size: int, *, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def render(output: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), YELLOW)
    draw = ImageDraw.Draw(image)
    title_font = _font(44, bold=True)
    heading_font = _font(30, bold=True)
    body_font = _font(24)
    small_font = _font(19)

    draw.rectangle((32, 28, WIDTH - 32, 178), fill=YELLOW, outline=BLACK, width=4)
    draw.text((64, 54), "OPEN BADGES → CURVED SUBLIMATION", fill=BLACK, font=small_font)
    draw.text((64, 88), "MUG / CANTEEN ADAPTER PDF", fill=BLACK, font=title_font)
    draw.text((64, 144), "Curved effect uses the device or heater-adapter diameter.", fill=BLACK, font=small_font)

    panel = (64, 218, WIDTH - 64, HEIGHT - 54)
    draw.rectangle((panel[0] + 8, panel[1] + 8, panel[2] + 8, panel[3] + 8), fill=BLACK)
    draw.rectangle(panel, fill=BG, outline=YELLOW, width=3)
    draw.text((panel[0] + 28, panel[1] + 24), "TEMPLATE OPTIONS", fill=YELLOW, font=heading_font)

    y = panel[1] + 92
    draw.text((panel[0] + 36, y), "Curve device", fill=TEXT, font=body_font)
    draw.rectangle((panel[0] + 310, y - 8, panel[0] + 600, y + 42), outline=YELLOW, fill=SURFACE, width=2)
    draw.text((panel[0] + 332, y), "Standard mug", fill=TEXT, font=body_font)

    y += 72
    draw.text((panel[0] + 36, y), "Curve diameter", fill=TEXT, font=body_font)
    draw.rectangle((panel[0] + 310, y - 8, panel[0] + 460, y + 42), outline=YELLOW, fill=SURFACE, width=2)
    draw.text((panel[0] + 342, y), "8.2", fill=TEXT, font=body_font)
    draw.text((panel[0] + 482, y), "cm", fill=TEXT, font=body_font)

    y += 80
    draw.rectangle((panel[0] + 36, y + 2, panel[0] + 60, y + 26), outline=YELLOW, width=3, fill=SURFACE)
    draw.line((panel[0] + 41, y + 14, panel[0] + 47, y + 21, panel[0] + 57, y + 6), fill=YELLOW, width=3)
    draw.text((panel[0] + 76, y), "Add curved mug/canteen adapter effect", fill=TEXT, font=body_font)

    arc_box = (panel[0] + 720, panel[1] + 78, panel[0] + 1030, panel[1] + 294)
    draw.arc(arc_box, start=198, end=342, fill=BLUE, width=6)
    draw.line((panel[0] + 875, panel[1] + 90, panel[0] + 875, panel[1] + 300), fill=BLUE, width=2)
    draw.text((panel[0] + 706, panel[1] + 314), "center curve guide in PDF", fill=MUTED, font=small_font)

    draw.text(
        (panel[0] + 28, panel[3] - 40),
        "Generated with scripts/render_curve_controls_screenshot.py",
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
        default="docs/screenshots/curve-controls.png",
        help="PNG output path (default: docs/screenshots/curve-controls.png)",
    )
    args = parser.parse_args()
    render(Path(args.output))


if __name__ == "__main__":
    main()
