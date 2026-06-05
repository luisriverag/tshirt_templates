import pytest

pytest.importorskip("flask")

import sys
from io import BytesIO
from types import SimpleNamespace

from tshirt_templates.app import create_app
from tshirt_templates.badges import Badge


DEMO_BADGE = Badge(
    id="demo-badge.svg",
    name="Demo Badge",
    path="demo-badge.svg",
    raw_url="/static/demo-badge.svg",
    extension=".svg",
)


def test_index_renders_badge_picker(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Generate front & back t-shirt badge PDF templates" in response.data
    assert b'class="brand-mark"' in response.data
    assert b"Template workflow" in response.data
    assert b"M pixel shape" in response.data
    assert b"Circle wreath" in response.data
    assert b"Spiral trail" in response.data
    assert b"Wave ribbon" in response.data
    assert b"Portrait" in response.data
    assert b"Landscape" in response.data
    assert b'<option value="a4" selected>A4</option>' in response.data
    assert b"Units" in response.data
    assert b"Centimeters" in response.data
    assert b"Only common print-cut sizes" in response.data
    assert b"Include MakeSpace logo" in response.data
    assert b"Logo size" in response.data
    assert b"Badge order" in response.data
    assert b"Alphabetical" in response.data
    assert b"By category" in response.data
    assert b'name="mirror" value="off"' in response.data
    assert b"Demo Badge" in response.data


def test_preview_renders_selected_layout(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front", "back"],
            "mode": "grid",
            "page_size": "letter",
            "orientation": "landscape",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "copies": "2",
        },
    )

    assert response.status_code == 200
    assert b"PDF template preview" in response.data
    assert b'class="brand-mark"' in response.data
    assert b'viewBox="0 0 792.0 612.0"' in response.data
    assert b'name="orientation" value="landscape"' in response.data
    assert b"Manual placement" in response.data
    assert b'class="draggable-badge"' in response.data
    assert b"FRONT" in response.data
    assert b"BACK" in response.data


def test_pdf_route_returns_mirrored_pdf_download_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append(kwargs) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "copies": "1",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-template.pdf"
    assert response.data.startswith(b"%PDF")
    assert calls == [{"mirror": True}]


def test_refresh_route_clears_cache_and_redirects(monkeypatch):
    called = []
    monkeypatch.setattr("tshirt_templates.app.refresh_badges", lambda: called.append(True))
    app = create_app()

    response = app.test_client().post("/refresh")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert called == [True]


def test_preview_saves_uploaded_badges(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/preview",
        data={
            "uploads": (BytesIO(b"<svg></svg>"), "custom.svg"),
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.2",
            "spacing": "0.2",
            "copies": "1",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Custom" in response.data
    assert b"upload:" in response.data


def test_preview_orders_badges_alphabetically(monkeypatch):
    alpha = Badge("alpha.svg", "Alpha", "alpha.svg", "/static/demo-badge.svg", ".svg")
    zulu = Badge("zulu.svg", "Zulu", "zulu.svg", "/static/demo-badge.svg", ".svg")
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [zulu, alpha])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [zulu.id, alpha.id],
            "sides": ["front"],
            "mode": "grid",
            "order": "alphabetical",
        },
    )

    assert response.status_code == 200
    assert response.data.index(b"Alpha") < response.data.index(b"Zulu")


def test_pdf_route_applies_manual_coordinates(monkeypatch):
    captured = {}
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])

    def fake_render_pdf(badges, page_size, layouts, **kwargs):
        captured["placement"] = layouts[0].placements[0]
        return b"%PDF-1.4\n%%EOF"

    monkeypatch.setitem(sys.modules, "tshirt_templates.pdf", SimpleNamespace(render_pdf=fake_render_pdf))
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "unit": "in",
            "badge_size": "1.0",
            "manual_0_0_x": "1.5",
            "manual_0_0_y": "2.5",
            "manual_0_0_rotation": "15",
        },
    )

    assert response.status_code == 200
    assert captured["placement"].x == 108.0
    assert captured["placement"].y == 792.0 - 180.0 - 72.0
    assert captured["placement"].rotation == 15


def test_preview_can_include_makespace_logo(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "include_logo": "on",
            "logo_size": "5.0",
        },
    )

    assert response.status_code == 200
    assert b"MakeSpace Madrid Logo" in response.data
    assert b"makespace-bk.svg" in response.data


def test_pdf_route_includes_makespace_logo_placement(monkeypatch):
    captured = {}
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])

    def fake_render_pdf(badges, page_size, layouts, **kwargs):
        captured["badges"] = badges
        captured["layout"] = layouts[0]
        return b"%PDF-1.4\n%%EOF"

    monkeypatch.setitem(sys.modules, "tshirt_templates.pdf", SimpleNamespace(render_pdf=fake_render_pdf))
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "unit": "in",
            "badge_size": "1.0",
            "include_logo": "on",
            "logo_size": "3.0",
        },
    )

    assert response.status_code == 200
    assert [badge.id for badge in captured["badges"]] == [DEMO_BADGE.id, "makespace-logo"]
    logo_placement = captured["layout"].placements[-1]
    assert logo_placement.badge_id == "makespace-logo"
    assert logo_placement.width == 216.0
    assert logo_placement.height == 216.0


def test_api_health_options_and_badges(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    health = client.get("/api/v1/health")
    options = client.get("/api/v1/options")
    badges = client.get("/api/v1/badges?include_logo=true")

    assert health.status_code == 200
    assert health.json == {"status": "ok", "service": "tshirt_templates"}
    assert options.status_code == 200
    assert options.json["defaults"]["page_size"] == "a4"
    assert options.json["logo_size_options"]["cm"]
    assert badges.status_code == 200
    assert [badge["id"] for badge in badges.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]


def test_api_layout_preview_computes_json_layout_with_logo(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()

    response = app.test_client().post(
        "/api/v1/layouts/preview",
        json={
            "badge_ids": [DEMO_BADGE.id],
            "options": {
                "sides": ["front"],
                "unit": "in",
                "badge_size": "1.0",
                "spacing": "0.2",
                "include_logo": True,
                "logo_size": "2.0",
            },
            "manual_placements": [
                {"layout_index": 0, "placement_index": 0, "x": 1.0, "y": 2.0, "rotation": 12}
            ],
        },
    )

    assert response.status_code == 200
    assert response.json["page"]["unit"] == "in"
    assert response.json["options"]["include_logo"] is True
    assert [badge["id"] for badge in response.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]
    placements = response.json["layouts"][0]["placements"]
    assert [placement["badge_id"] for placement in placements] == [DEMO_BADGE.id, "makespace-logo"]
    assert placements[0]["x"] == 1.0
    assert placements[0]["rotation"] == 12.0
    assert placements[-1]["width"] == 2.0


def test_mcp_metadata_and_tools(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    metadata = client.get("/mcp")
    initialize = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    layout = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "compute_layout",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id],
                    "options": {"sides": ["front"], "unit": "cm", "badge_size": "3.5"},
                },
            },
        },
    )

    assert metadata.status_code == 200
    assert metadata.json["endpoint"] == "/mcp"
    assert initialize.status_code == 200
    assert initialize.json["result"]["serverInfo"]["name"] == "tshirt_templates"
    assert tools.status_code == 200
    assert {tool["name"] for tool in tools.json["result"]["tools"]} >= {
        "get_options",
        "list_badges",
        "compute_layout",
    }
    assert layout.status_code == 200
    content = layout.json["result"]["structuredContent"]
    assert content["layouts"][0]["placements"][0]["badge_id"] == DEMO_BADGE.id
