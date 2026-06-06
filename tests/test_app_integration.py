import pytest

pytest.importorskip("flask")

import base64
import json
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
    assert b"Download calibration page" in response.data
    assert b'href="/calibration.pdf"' in response.data
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
    assert b"All badges are selected by default" in response.data
    assert b"Search badges" in response.data
    assert b"Skip badge list and continue to actions" in response.data
    assert b'id="badge-picker-help"' in response.data
    assert b'aria-describedby="badge-picker-help"' in response.data
    assert b'id="template-actions"' in response.data
    assert b"Select visible" in response.data
    assert b"Clear visible" in response.data
    assert b'draggable="true"' in response.data
    assert b'data-category="uncategorized"' in response.data
    assert b"Front text" in response.data
    assert b"Back text" in response.data
    assert b"Ubuntu" in response.data
    assert b"Alphabetical" in response.data
    assert b"By category" in response.data
    assert b'name="mirror" value="off"' in response.data
    assert b"Add crop and registration marks" in response.data
    assert b'name="include_print_marks" value="off"' in response.data
    assert b"Add badge cut-line outlines" in response.data
    assert b'name="include_cut_lines" value="off"' in response.data
    assert b"Demo Badge" in response.data


def test_index_renders_delete_button_for_uploaded_badges(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Replace upload" in response.data
    assert b"Delete upload" in response.data
    assert b'name="replace_upload" value="abc-team.svg"' in response.data
    assert b'name="delete_upload" value="abc-team.svg"' in response.data


def test_browser_replace_upload_route_updates_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().post(
        "/uploads/replace",
        data={
            "replace_upload": uploaded.name,
            "replacement_upload": (BytesIO(b"<svg>new</svg>"), "new.svg"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert uploaded.read_bytes() == b"<svg>new</svg>"


def test_browser_delete_upload_route_removes_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().post("/uploads/delete", data={"delete_upload": uploaded.name})

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    assert not uploaded.exists()


def test_preview_shows_upload_dimension_warnings(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/preview",
        data={
            "badges": [DEMO_BADGE.id],
            "uploads": (BytesIO(b'<svg viewBox="0 0 32 32"></svg>'), "tiny.svg"),
            "sides": ["front"],
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Upload notices" in response.data
    assert b"32" in response.data


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
            "front_text": "Ada",
            "back_text": "MakeSpace",
            "text_font": "dejavu",
            "include_cut_lines": "on",
        },
    )

    assert response.status_code == 200
    assert b"PDF template preview" in response.data
    assert b"Layout summary" in response.data
    assert b"Demo Badge on Front" in response.data
    assert b"Detailed placement coordinates" in response.data
    assert b"High-contrast outlines" in response.data
    assert b"badge-contrast-outline" in response.data
    assert b"cut-line-outline" in response.data
    assert b"highContrastPreview" in response.data
    assert b'class="brand-mark"' in response.data
    assert b'viewBox="0 0 792.0 612.0"' in response.data
    assert b'name="orientation" value="landscape"' in response.data
    assert b"Manual placement" in response.data
    assert b"Reset automatic placement" in response.data
    assert b"Snap to grid" in response.data
    assert b"Snap to panel edges" in response.data
    assert b'id="edge-snap-tolerance"' in response.data
    assert b"data-panel-x" in response.data
    assert b"snapBadgeToPanelEdges" in response.data
    assert b"Rotate 45" in response.data
    assert b"preview-status" in response.data
    assert b'class="draggable-badge"' in response.data
    assert b'class="collision-outline"' in response.data
    assert b"FRONT" in response.data
    assert b"BACK" in response.data
    assert b"Ada" in response.data
    assert b"MakeSpace" in response.data
    assert b'name="front_text" value="Ada"' in response.data
    assert b'name="back_text" value="MakeSpace"' in response.data
    assert b'name="text_font" value="dejavu"' in response.data


def test_calibration_pdf_route_returns_printable_pdf():
    app = create_app()

    response = app.test_client().get("/calibration.pdf?page_size=letter&orientation=landscape&unit=in")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-calibration-page.pdf"
    assert response.data.startswith(b"%PDF")
    assert b"Print calibration page" in response.data
    assert b"unit=in" in response.data


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
    assert calls[0]["mirror"] is True
    assert calls[0]["panel_text"] == {"front": "", "back": "", "font": "ubuntu"}
    assert calls[0]["print_marks"] is False
    assert calls[0]["cut_lines"] is False
    assert calls[0]["metadata"]["include_print_marks"] == "false"
    assert calls[0]["metadata"]["include_cut_lines"] == "false"


def test_pdf_route_passes_panel_text_options(monkeypatch):
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
            "sides": ["front", "back"],
            "front_text": "Ada",
            "back_text": "MakeSpace",
            "text_font": "courier",
        },
    )

    assert response.status_code == 200
    assert calls[0]["panel_text"] == {"front": "Ada", "back": "MakeSpace", "font": "courier"}


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
    ready = client.get("/api/v1/ready")
    options = client.get("/api/v1/options")
    badges = client.get("/api/v1/badges?include_logo=true")

    assert health.status_code == 200
    assert health.json == {"status": "ok", "service": "tshirt_templates"}
    assert ready.status_code == 200
    assert ready.json == {
        "status": "ready",
        "service": "tshirt_templates",
        "checks": {"upload_folder": "ok"},
    }
    assert options.status_code == 200
    assert options.json["defaults"]["page_size"] == "a4"
    assert options.json["defaults"]["text_font"] == "ubuntu"
    assert options.json["text_fonts"]["ubuntu"] == "Ubuntu"
    assert options.json["logo_size_options"]["cm"]
    assert badges.status_code == 200
    assert [badge["id"] for badge in badges.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]


def test_api_uploads_saves_badges(monkeypatch, tmp_path):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/api/v1/uploads",
        data={"uploads": (BytesIO(b"<svg></svg>"), "team badge.svg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    uploaded = response.json["badges"][0]
    assert uploaded["id"].startswith("upload:")
    assert uploaded["name"] == "Team Badge"
    assert uploaded["source"] == "upload"
    assert response.json["warnings"][0]["code"] == "missing_dimensions"
    assert (tmp_path / uploaded["id"].removeprefix("upload:")).exists()


def test_api_uploads_rejects_empty_payload(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post("/api/v1/uploads", data={})

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"
    assert response.json["error"]["field"] == "uploads"


def test_api_replace_upload_updates_saved_badge(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().put(
        f"/api/v1/uploads/{uploaded.name}",
        data={"upload": (BytesIO(b"<svg>new</svg>"), "replacement.svg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.json["badge"]["id"] == f"upload:{uploaded.name}"
    assert uploaded.read_bytes() == b"<svg>new</svg>"
    assert response.json["warnings"][0]["code"] == "missing_dimensions"


def test_api_uploads_reject_invalid_image_content(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().post(
        "/api/v1/uploads",
        data={"uploads": (BytesIO(b"not an image"), "fake.png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"


def test_api_replace_upload_rejects_missing_file_field(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg>old</svg>")

    response = app.test_client().put(f"/api/v1/uploads/{uploaded.name}")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_upload"


def test_api_delete_upload_removes_saved_badge(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    uploaded = tmp_path / "abc-team.svg"
    uploaded.write_bytes(b"<svg></svg>")

    response = app.test_client().delete(f"/api/v1/uploads/{uploaded.name}")

    assert response.status_code == 200
    assert response.json == {"deleted": uploaded.name}
    assert not uploaded.exists()


def test_api_delete_upload_returns_not_found_for_unknown_file(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = app.test_client().delete("/api/v1/uploads/missing.svg")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "upload_not_found"


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
                "front_text": "Ada",
                "back_text": "MakeSpace",
                "text_font": "times",
            },
            "manual_placements": [
                {"layout_index": 0, "placement_index": 0, "x": 1.0, "y": 2.0, "rotation": 12}
            ],
        },
    )

    assert response.status_code == 200
    assert response.json["page"]["unit"] == "in"
    assert response.json["options"]["include_logo"] is True
    assert response.json["options"]["front_text"] == "Ada"
    assert response.json["options"]["back_text"] == "MakeSpace"
    assert response.json["options"]["text_font"] == "times"
    assert [badge["id"] for badge in response.json["badges"]] == [DEMO_BADGE.id, "makespace-logo"]
    placements = response.json["layouts"][0]["placements"]
    assert [placement["badge_id"] for placement in placements] == [DEMO_BADGE.id, "makespace-logo"]
    assert placements[0]["x"] == 1.0
    assert placements[0]["rotation"] == 12.0
    assert placements[-1]["width"] == 2.0


def test_api_pdf_generates_pdf_from_json(monkeypatch):
    calls = []
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/api/v1/pdfs",
        json={
            "badge_ids": [DEMO_BADGE.id],
            "options": {
                "sides": ["front"],
                "unit": "in",
                "badge_size": "1.0",
                "front_text": "Ada",
                "text_font": "courier",
                "mirror": False,
                "include_print_marks": True,
                "include_cut_lines": True,
            },
            "manual_placements": [
                {"layout_index": 0, "placement_index": 0, "x": 1.0, "y": 2.0, "rotation": 12}
            ],
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-template.pdf"
    assert response.data.startswith(b"%PDF")
    args, kwargs = calls[0]
    assert [badge.id for badge in args[0]] == [DEMO_BADGE.id]
    assert args[2][0].placements[0].x == 72.0
    assert args[2][0].placements[0].rotation == 12.0
    assert kwargs["mirror"] is False
    assert kwargs["panel_text"] == {"front": "Ada", "back": "", "font": "courier"}
    assert kwargs["print_marks"] is True
    assert kwargs["cut_lines"] is True
    assert kwargs["metadata"]["include_print_marks"] == "true"
    assert kwargs["metadata"]["include_cut_lines"] == "true"


def test_api_pdf_rejects_non_json_payload():
    app = create_app()

    response = app.test_client().post("/api/v1/pdfs", data="not-json")

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_json"


def test_mcp_metadata_resources_prompts_and_tools(monkeypatch):
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    app = create_app()
    client = app.test_client()

    metadata = client.get("/mcp")
    initialize = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    ping = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "ping"})
    initialized = client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "notifications/initialized"})
    tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"})
    resources = client.post("/mcp", json={"jsonrpc": "2.0", "id": 5, "method": "resources/list"})
    read_options = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "resources/read",
            "params": {"uri": "tshirt://options"},
        },
    )
    read_badges = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 11,
            "method": "resources/read",
            "params": {"uri": "tshirt://badges"},
        },
    )
    resource_templates = client.post("/mcp", json={"jsonrpc": "2.0", "id": 8, "method": "resources/templates/list"})
    prompts = client.post("/mcp", json={"jsonrpc": "2.0", "id": 9, "method": "prompts/list"})
    prompt = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 10,
            "method": "prompts/get",
            "params": {"name": "explain_layout"},
        },
    )
    layout = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 7,
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
    assert "render_pdf" in metadata.json["tools"]
    assert initialize.status_code == 200
    assert initialize.json["result"]["serverInfo"]["name"] == "tshirt_templates"
    assert initialize.json["result"]["capabilities"]["prompts"]["listChanged"] is False
    assert ping.status_code == 200
    assert ping.json["result"] == {}
    assert initialized.status_code == 200
    assert initialized.json["result"] == {}
    assert tools.status_code == 200
    assert {tool["name"] for tool in tools.json["result"]["tools"]} >= {
        "get_options",
        "list_badges",
        "compute_layout",
        "render_pdf",
        "upload_badge_artwork",
        "validate_template",
    }
    assert resources.status_code == 200
    assert {resource["uri"] for resource in resources.json["result"]["resources"]} >= {
        "tshirt://options",
        "tshirt://badges",
    }
    assert read_options.status_code == 200
    options_resource = read_options.json["result"]["contents"][0]
    assert options_resource["mimeType"] == "application/json"
    assert json.loads(options_resource["text"])["defaults"]["text_font"] == "ubuntu"
    assert read_badges.status_code == 200
    badges_resource = read_badges.json["result"]["contents"][0]
    assert json.loads(badges_resource["text"])["badges"][0]["id"] == DEMO_BADGE.id
    assert resource_templates.status_code == 200
    assert resource_templates.json["result"] == {"resourceTemplates": []}
    assert prompts.status_code == 200
    assert {prompt["name"] for prompt in prompts.json["result"]["prompts"]} >= {
        "design_tshirt_template",
        "optimize_cut_sheet",
        "explain_layout",
    }
    assert prompt.status_code == 200
    assert prompt.json["result"]["messages"][0]["content"]["type"] == "text"
    assert layout.status_code == 200
    content = layout.json["result"]["structuredContent"]
    assert content["layouts"][0]["placements"][0]["badge_id"] == DEMO_BADGE.id


def test_mcp_rejects_unknown_resources_and_invalid_uploads(tmp_path):
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    client = app.test_client()

    unknown_resource = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": "tshirt://missing"},
        },
    )
    invalid_upload = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "upload_badge_artwork",
                "arguments": {"filename": "badge.svg", "content_base64": "not-base64"},
            },
        },
    )

    assert unknown_resource.status_code == 200
    assert unknown_resource.json["error"]["message"] == "Unknown resource: tshirt://missing"
    assert invalid_upload.status_code == 200
    assert invalid_upload.json["error"]["message"] == "content_base64 is not valid base64."


def test_mcp_render_pdf_upload_and_validate_template(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("tshirt_templates.app.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: calls.append((args, kwargs)) or b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    client = app.test_client()

    upload = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "upload_badge_artwork",
                "arguments": {
                    "filename": "team.svg",
                    "content_base64": base64.b64encode(b"<svg></svg>").decode("ascii"),
                },
            },
        },
    )
    pdf = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "render_pdf",
                "arguments": {
                    "badge_ids": [DEMO_BADGE.id],
                    "options": {"sides": ["front"], "mirror": False, "front_text": "Ada"},
                },
            },
        },
    )
    validation = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "validate_template",
                "arguments": {"badge_ids": [DEMO_BADGE.id, "missing.svg"], "options": {"sides": ["front"]}},
            },
        },
    )

    assert upload.status_code == 200
    uploaded_badge = upload.json["result"]["structuredContent"]["badge"]
    assert uploaded_badge["id"].startswith("upload:")
    assert (tmp_path / uploaded_badge["id"].removeprefix("upload:")).exists()
    assert pdf.status_code == 200
    pdf_payload = pdf.json["result"]["structuredContent"]
    assert pdf_payload["mime_type"] == "application/pdf"
    assert pdf_payload["resource"]["mimeType"] == "application/pdf"
    assert base64.b64decode(pdf_payload["pdf_base64"]).startswith(b"%PDF")
    pdf_content = pdf.json["result"]["content"]
    assert pdf_content[0]["type"] == "text"
    assert pdf_content[1]["type"] == "resource"
    assert pdf_content[1]["resource"]["blob"] == pdf_payload["pdf_base64"]
    assert calls[0][1]["panel_text"]["front"] == "Ada"
    assert validation.status_code == 200
    validation_payload = validation.json["result"]["structuredContent"]
    assert validation_payload["normalized"]["options"]["sides"] == ["front"]
    assert validation_payload["warnings"][0]["code"] == "unknown_badges"


def test_api_ready_reports_not_ready_when_upload_folder_is_file(tmp_path):
    app = create_app()
    upload_path = tmp_path / "uploads"
    upload_path.write_text("not a directory", encoding="utf-8")
    app.config["UPLOAD_FOLDER"] = str(upload_path)

    response = app.test_client().get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json == {
        "status": "not_ready",
        "service": "tshirt_templates",
        "checks": {"upload_folder": "error"},
    }
