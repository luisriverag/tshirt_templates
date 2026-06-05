"""PDF rendering for sublimation badge templates."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

from .badges import Badge
from .layout import PanelLayout

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


def render_pdf(
    badges: list[Badge],
    page_size: tuple[float, float],
    layouts: list[PanelLayout],
    mirror: bool = True,
) -> bytes:
    """Render selected badge layouts into a PDF byte string."""

    badge_lookup = {badge.id: badge for badge in badges}
    buffer = BytesIO()
    page_width, page_height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    pdf.setTitle("T-shirt sublimation badge template")

    if mirror:
        pdf.translate(page_width, 0)
        pdf.scale(-1, 1)

    for layout in layouts:
        pdf.setStrokeColor(colors.HexColor("#555555"))
        pdf.setDash(5, 4)
        pdf.roundRect(layout.x, layout.y, layout.width, layout.height, 12, stroke=1, fill=0)
        pdf.setDash()
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.HexColor("#333333"))
        pdf.drawString(layout.x + 10, layout.y + layout.height - 18, layout.side.upper())

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
