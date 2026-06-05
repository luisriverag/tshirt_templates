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
            "badge_size": "1.25",
            "spacing": "0.2",
            "copies": "2",
        },
    )

    assert response.status_code == 200
    assert b"PDF template preview" in response.data
    assert b"FRONT" in response.data
    assert b"BACK" in response.data


def test_pdf_route_returns_pdf_download(monkeypatch):
    monkeypatch.setattr("tshirt_templates.badges.list_badges", lambda: [DEMO_BADGE])
    monkeypatch.setitem(
        sys.modules,
        "tshirt_templates.pdf",
        SimpleNamespace(render_pdf=lambda *args, **kwargs: b"%PDF-1.4\n%%EOF"),
    )
    app = create_app()

    response = app.test_client().post(
        "/pdf",
        data={
            "badges": [DEMO_BADGE.id],
            "sides": ["front"],
            "mode": "grid",
            "page_size": "letter",
            "badge_size": "1.25",
            "spacing": "0.2",
            "copies": "1",
            "mirror": "on",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"] == "attachment; filename=tshirt-badge-template.pdf"
    assert response.data.startswith(b"%PDF")


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
            "badge_size": "1.25",
            "spacing": "0.2",
            "copies": "1",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Custom" in response.data
    assert b"upload:" in response.data
