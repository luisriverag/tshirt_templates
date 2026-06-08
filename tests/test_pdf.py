from tshirt_templates.badges import Badge
from tshirt_templates.layout import PanelLayout, Placement
import tshirt_templates.pdf as pdf_module
from tshirt_templates.pdf import _curved_placement, render_calibration_pdf, render_pdf, verify_pdf_assets


def test_render_pdf_can_include_print_marks_and_metadata():
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [Placement(badge.id, 50.0, 50.0, 40.0, 40.0)],
    )

    content = render_pdf(
        [badge],
        (200.0, 200.0),
        [layout],
        print_marks=True,
        cut_lines=True,
        metadata={"include_cut_lines": "true", "include_print_marks": "true", "mode": "grid"},
    )

    assert content.startswith(b"%PDF")
    assert b"include_print_marks=true" in content
    assert b"include_cut_lines=true" in content
    assert b"mode=grid" in content
    assert b"/Subject" in content


def test_render_calibration_pdf_includes_rulers_and_warning_metadata():
    content = render_calibration_pdf((300.0, 240.0), unit="in", mirror=False)

    assert content.startswith(b"%PDF")
    assert b"Print calibration page" in content
    assert b"Mirror warning" in content
    assert b"unit=in" in content


def test_verify_pdf_assets_reports_unrenderable_badges(tmp_path):
    broken_png = tmp_path / "broken.png"
    broken_png.write_bytes(b"not a png")
    badge = Badge(
        id="upload:broken.png",
        name="Broken",
        path="uploaded/broken.png",
        raw_url="/uploads/broken.png",
        extension=".png",
        local_path=broken_png,
    )

    failures = verify_pdf_assets([badge])

    assert failures[0]["badge_id"] == badge.id
    assert failures[0]["name"] == "Broken"


def test_render_pdf_smoke_checks_page_size_and_placement_count(monkeypatch):
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [
            Placement(badge.id, 40.0, 45.0, 30.0, 30.0),
            Placement(badge.id, 80.0, 90.0, 30.0, 30.0),
        ],
    )
    drawn = []
    monkeypatch.setattr(pdf_module, "_draw_badge", lambda *args: drawn.append(args))

    content = render_pdf([badge], (200.0, 300.0), [layout], mirror=False)

    assert content.startswith(b"%PDF")
    assert b"/MediaBox [ 0 0 200 300 ]" in content
    assert len(drawn) == 2


def test_render_pdf_does_not_draw_panel_headers_or_page_numbers(monkeypatch):
    drawn_text = []
    original_canvas = pdf_module.canvas.Canvas

    class TrackingCanvas(original_canvas):
        def drawString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawString(x, y, text)

        def drawCentredString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawCentredString(x, y, text)

        def drawRightString(self, x, y, text):
            drawn_text.append(str(text))
            return super().drawRightString(x, y, text)

    monkeypatch.setattr(pdf_module.canvas, "Canvas", TrackingCanvas)

    content = render_pdf(
        [],
        (200.0, 300.0),
        [PanelLayout("front", 20.0, 20.0, 160.0, 120.0, [])],
        mirror=False,
    )

    assert content.startswith(b"%PDF")
    assert drawn_text == []


def test_render_pdf_fetches_each_badge_asset_once_for_repeated_placements(monkeypatch):
    badge = Badge(
        id="demo-badge.svg",
        name="Demo Badge",
        path="demo-badge.svg",
        raw_url="/static/demo-badge.svg",
        extension=".svg",
    )
    layout = PanelLayout(
        "front",
        20.0,
        20.0,
        160.0,
        160.0,
        [
            Placement(badge.id, 40.0, 45.0, 30.0, 30.0),
            Placement(badge.id, 80.0, 90.0, 30.0, 30.0),
        ],
    )
    fetches = []
    monkeypatch.setattr(pdf_module, "_fetch_asset", lambda fetched_badge: fetches.append(fetched_badge.id) or pdf_module.DEMO_SVG)

    content = render_pdf([badge], (200.0, 300.0), [layout], mirror=False)

    assert content.startswith(b"%PDF")
    assert fetches == [badge.id]


def test_curved_placement_rotates_and_sags_from_panel_center():
    layout = PanelLayout("front", 0.0, 0.0, 200.0, 120.0, [])

    center_x, center_y, rotation = _curved_placement(
        layout,
        center_x=150.0,
        center_y=60.0,
        rotation=0.0,
        curve_settings={"diameter_inches": 3.0},
    )

    assert center_x == 150.0
    assert center_y < 60.0
    assert rotation > 0.0
