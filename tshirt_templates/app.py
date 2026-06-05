"""Flask web application for badge-based t-shirt sublimation templates."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, send_from_directory, url_for

from .badges import get_badges_by_id, list_badges, refresh_badges
from .layout import place_badges
from .options import parse_layout_options
from .uploads import list_uploaded_badges, save_uploaded_badges

LAYOUT_MODES = {
    "grid": "Grid",
    "rows": "Staggered rows",
    "diagonal": "Diagonal sash",
    "scatter": "Organic scatter",
    "border": "Border frame",
}
PAGE_SIZES = {
    "letter": "US Letter",
    "a4": "A4",
    "a3": "A3",
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.setdefault("UPLOAD_FOLDER", str(Path(app.instance_path) / "uploads"))
    app.config.setdefault("MAX_CONTENT_LENGTH", 32 * 1024 * 1024)

    @app.get("/")
    def index() -> str:
        badges = _available_badges()
        selected_ids = [badge.id for badge in badges[: min(8, len(badges))]]
        return render_template(
            "index.html",
            badges=badges,
            selected_ids=selected_ids,
            modes=LAYOUT_MODES,
            page_sizes=PAGE_SIZES,
        )

    @app.post("/refresh")
    def refresh() -> Response:
        refresh_badges()
        return redirect(url_for("index"))

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str) -> Response:
        return send_from_directory(_upload_folder(), filename)

    @app.post("/preview")
    def preview() -> str:
        badge_ids = _selected_badge_ids_with_uploads()
        badges = get_badges_by_id(badge_ids, _upload_folder())
        page_size, layouts = _layout_from_form(badge_ids)
        return render_template(
            "preview.html",
            badges=badges,
            badge_lookup={badge.id: badge for badge in badges},
            layouts=layouts,
            page_width=page_size[0],
            page_height=page_size[1],
            form=request.form,
            selected_ids=badge_ids,
        )

    @app.post("/pdf")
    def pdf() -> Response:
        badge_ids = _selected_badge_ids_with_uploads()
        badges = get_badges_by_id(badge_ids, _upload_folder())
        page_size, layouts = _layout_from_form(badge_ids)
        from .pdf import render_pdf

        content = render_pdf(badges, page_size, layouts, mirror=_layout_options().mirror)
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=tshirt-badge-template.pdf"},
        )

    def _upload_folder() -> str:
        return app.config["UPLOAD_FOLDER"]

    def _available_badges():
        return [*list_badges(), *list_uploaded_badges(_upload_folder())]

    def _selected_badge_ids_with_uploads() -> list[str]:
        uploaded = save_uploaded_badges(request.files.getlist("uploads"), _upload_folder())
        return [*request.form.getlist("badges"), *[badge.id for badge in uploaded]]

    def _layout_options():
        return parse_layout_options(request.form, request.form.getlist)

    def _layout_from_form(badge_ids: list[str]):
        options = _layout_options()
        return place_badges(
            badge_ids=badge_ids,
            sides=options.sides,
            page_size=options.page_size,
            mode=options.mode,
            badge_size_inches=options.badge_size_inches,
            spacing_inches=options.spacing_inches,
            copies=options.copies,
        )

    return app


app = create_app()
