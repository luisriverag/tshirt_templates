"""PDF rendering for sublimation badge templates."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

from .badges import Badge
from .layout import PanelLayout

FONT_FILES = {
    "ubuntu": [
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ],
    "dejavu": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}
BUILT_IN_FONTS = {
    "helvetica": "Helvetica-Bold",
    "times": "Times-Bold",
    "courier": "Courier-Bold",
}
REGISTERED_FONTS: dict[str, str] = {}


DEMO_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
<circle cx="100" cy="100" r="94" fill="#ffe066" stroke="#222" stroke-width="8"/>
<path d="M55 110 L88 142 L148 62" fill="none" stroke="#2f9e44" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
<text x="100" y="178" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">DEMO</text>
</svg>"""


def _fetch_asset(badge: Badge) -> bytes:
    if badge.local_path:
        return Path(badge.local_path).read_bytes()
    if badge.raw_url.startswith("/static/demo-badge.svg"):
        return DEMO_SVG
    import requests

    response = requests.get(badge.raw_url, timeout=20)
    response.raise_for_status()
    return response.content


def _draw_svg(pdf: canvas.Canvas, content: bytes, x: float, y: float, width: float, height: float) -> None:
    with NamedTemporaryFile(suffix=".svg") as svg_file:
        svg_file.write(content)
        svg_file.flush()
        drawing = svg2rlg(svg_file.name)
    if not drawing:
        return
    scale = min(width / drawing.width, height / drawing.height)
    pdf.saveState()
    pdf.translate(x + (width - drawing.width * scale) / 2, y + (height - drawing.height * scale) / 2)
    pdf.scale(scale, scale)
    renderPDF.draw(drawing, pdf, 0, 0)
    pdf.restoreState()


def _draw_raster(pdf: canvas.Canvas, content: bytes, x: float, y: float, width: float, height: float) -> None:
    pdf.drawImage(ImageReader(BytesIO(content)), x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")


def _draw_badge(pdf: canvas.Canvas, badge: Badge, x: float, y: float, width: float, height: float) -> None:
    try:
        content = _fetch_asset(badge)
        if badge.extension == ".svg" or content.lstrip().startswith(b"<svg"):
            _draw_svg(pdf, content, x, y, width, height)
        else:
            _draw_raster(pdf, content, x, y, width, height)
    except Exception:
        pdf.setStrokeColor(colors.HexColor("#cc3a3a"))
        pdf.setFillColor(colors.HexColor("#fff5f5"))
        pdf.roundRect(x, y, width, height, 8, stroke=1, fill=1)
        pdf.setFillColor(colors.HexColor("#7a1f1f"))
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x + width / 2, y + height / 2, escape(badge.name[:24]))


def _font_name(font_key: str) -> str:
    if font_key in BUILT_IN_FONTS:
        return BUILT_IN_FONTS[font_key]
    if font_key in REGISTERED_FONTS:
        return REGISTERED_FONTS[font_key]
    for font_file in FONT_FILES.get(font_key, []):
        if Path(font_file).exists():
            registered_name = f"PanelText-{font_key}"
            pdfmetrics.registerFont(TTFont(registered_name, font_file))
            REGISTERED_FONTS[font_key] = registered_name
            return registered_name
    return "Helvetica-Bold"


def _draw_panel_text(
    pdf: canvas.Canvas,
    layout: PanelLayout,
    panel_text: dict[str, str] | None,
) -> None:
    if not panel_text:
        return
    text = (panel_text.get(layout.side) or "").strip()
    if not text:
        return
    font_name = _font_name(panel_text.get("font", "ubuntu"))
    font_size = min(30.0, max(14.0, layout.width / max(len(text), 1) * 1.35))
    pdf.saveState()
    pdf.setFillColor(colors.HexColor("#111111"))
    pdf.setFont(font_name, font_size)
    pdf.drawCentredString(layout.x + layout.width / 2, layout.y + 16, text)
    pdf.restoreState()


def _draw_print_marks(pdf: canvas.Canvas, page_width: float, page_height: float) -> None:
    """Draw crop and registration marks around the page edges."""

    mark = 18.0
    inset = 18.0
    center_radius = 5.0
    pdf.saveState()
    pdf.setStrokeColor(colors.HexColor("#111111"))
    pdf.setLineWidth(0.6)
    pdf.setDash()
    for x, y, x_direction, y_direction in [
        (inset, inset, 1, 1),
        (page_width - inset, inset, -1, 1),
        (inset, page_height - inset, 1, -1),
        (page_width - inset, page_height - inset, -1, -1),
    ]:
        pdf.line(x, y, x + mark * x_direction, y)
        pdf.line(x, y, x, y + mark * y_direction)
    for x, y in [
        (page_width / 2, inset),
        (page_width / 2, page_height - inset),
        (inset, page_height / 2),
        (page_width - inset, page_height / 2),
    ]:
        pdf.circle(x, y, center_radius, stroke=1, fill=0)
        pdf.line(x - center_radius * 1.8, y, x + center_radius * 1.8, y)
        pdf.line(x, y - center_radius * 1.8, x, y + center_radius * 1.8)
    pdf.restoreState()



def render_calibration_pdf(
    page_size: tuple[float, float],
    unit: str = "cm",
    mirror: bool = False,
) -> bytes:
    """Render a print calibration page with ruler marks and mirror guidance."""

    buffer = BytesIO()
    page_width, page_height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size, pageCompression=0)
    pdf.setTitle("T-shirt template print calibration page")
    pdf.setSubject(f"unit={unit}; mirror={str(mirror).lower()}; print_scale=100%")

    if mirror:
        pdf.translate(page_width, 0)
        pdf.scale(-1, 1)

    pdf.setStrokeColor(colors.HexColor("#111111"))
    pdf.setFillColor(colors.HexColor("#111111"))
    pdf.setLineWidth(0.8)
    margin = 36.0
    step = 72.0 / 2.54 if unit == "cm" else 72.0
    label = "cm" if unit == "cm" else "in"

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, page_height - margin, "Print calibration page")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, page_height - margin - 18, "Print at 100% / actual size. Measure the rulers below before pressing transfers.")
    pdf.drawString(margin, page_height - margin - 34, "Mirror warning: sublimation transfers usually need mirrored artwork; proof/calibration pages usually do not.")

    origin_x = margin
    origin_y = margin
    ruler_length_x = page_width - 2 * margin
    ruler_length_y = page_height - 2 * margin - 72
    pdf.line(origin_x, origin_y, origin_x + ruler_length_x, origin_y)
    pdf.line(origin_x, origin_y, origin_x, origin_y + ruler_length_y)

    horizontal_marks = int(ruler_length_x // step)
    vertical_marks = int(ruler_length_y // step)
    pdf.setFont("Helvetica", 7)
    for index in range(horizontal_marks + 1):
        x = origin_x + index * step
        tick = 12 if index % 5 == 0 else 8
        pdf.line(x, origin_y, x, origin_y + tick)
        pdf.drawCentredString(x, origin_y - 12, str(index))
    for index in range(vertical_marks + 1):
        y = origin_y + index * step
        tick = 12 if index % 5 == 0 else 8
        pdf.line(origin_x, y, origin_x + tick, y)
        pdf.drawRightString(origin_x - 5, y - 2, str(index))

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(origin_x + ruler_length_x / 2, origin_y - 28, f"Horizontal ruler ({label})")
    pdf.saveState()
    pdf.translate(origin_x - 28, origin_y + ruler_length_y / 2)
    pdf.rotate(90)
    pdf.drawCentredString(0, 0, f"Vertical ruler ({label})")
    pdf.restoreState()

    pdf.setDash(4, 3)
    pdf.roundRect(margin, margin, page_width - 2 * margin, page_height - 2 * margin, 10, stroke=1, fill=0)
    pdf.setDash()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()

def render_pdf(
    badges: list[Badge],
    page_size: tuple[float, float],
    layouts: list[PanelLayout],
    mirror: bool = True,
    panel_text: dict[str, str] | None = None,
    print_marks: bool = False,
    metadata: dict[str, str] | None = None,
) -> bytes:
    """Render selected badge layouts into a PDF byte string."""

    badge_lookup = {badge.id: badge for badge in badges}
    buffer = BytesIO()
    page_width, page_height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    pdf.setTitle("T-shirt sublimation badge template")
    if metadata:
        pdf.setSubject("; ".join(f"{key}={value}" for key, value in sorted(metadata.items())))
        pdf.setKeywords(", ".join(f"{key}:{value}" for key, value in sorted(metadata.items())))

    if mirror:
        pdf.translate(page_width, 0)
        pdf.scale(-1, 1)

    if print_marks:
        _draw_print_marks(pdf, page_width, page_height)

    for layout in layouts:
        pdf.setStrokeColor(colors.HexColor("#555555"))
        pdf.setDash(5, 4)
        pdf.roundRect(layout.x, layout.y, layout.width, layout.height, 12, stroke=1, fill=0)
        pdf.setDash()
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.HexColor("#333333"))
        pdf.drawString(layout.x + 10, layout.y + layout.height - 18, layout.side.upper())

        _draw_panel_text(pdf, layout, panel_text)

        for placement in layout.placements:
            badge = badge_lookup.get(placement.badge_id)
            if not badge:
                continue
            pdf.saveState()
            pdf.translate(placement.x + placement.width / 2, placement.y + placement.height / 2)
            pdf.rotate(placement.rotation)
            _draw_badge(pdf, badge, -placement.width / 2, -placement.height / 2, placement.width, placement.height)
            pdf.restoreState()

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
