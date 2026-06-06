from tshirt_templates.badges import Badge
from tshirt_templates.layout import PanelLayout, Placement
from tshirt_templates.pdf import render_calibration_pdf, render_pdf


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
