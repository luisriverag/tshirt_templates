"""Flask web application for badge-based t-shirt sublimation templates."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template, request, send_from_directory, url_for

from .badges import Badge, get_badges_by_id, list_badges, order_badges, refresh_badges
from .layout import PanelLayout, Placement, place_badges
from .options import (
    BADGE_AMOUNTS,
    CENTIMETERS_PER_INCH,
    DEFAULT_BADGE_AMOUNTS,
    DEFAULT_LOGO_AMOUNTS,
    DEFAULT_SPACING_AMOUNTS,
    DEFAULT_UNIT,
    LOGO_AMOUNTS,
    SPACING_AMOUNTS,
    parse_layout_options,
)
from .uploads import list_uploaded_badges, save_uploaded_badges

LAYOUT_MODES = {
    "grid": "Grid",
    "rows": "Staggered rows",
    "diagonal": "Diagonal sash",
    "scatter": "Organic scatter",
    "circle": "Circle wreath",
    "spiral": "Spiral trail",
    "wave": "Wave ribbon",
    "border": "Border frame",
    "m-pixels": "M pixel shape",
}
PAGE_SIZES = {
    "a4": "A4",
    "a3": "A3",
    "letter": "US Letter",
}
ORIENTATIONS = {
    "portrait": "Portrait",
    "landscape": "Landscape",
}
ORDER_MODES = {
    "selected": "Selection order",
    "alphabetical": "Alphabetical",
    "category": "By category",
}
UNITS = {
    "cm": "Centimeters",
    "in": "Inches",
}
BADGE_SIZE_OPTIONS = {
    unit: sorted(amounts, key=float) for unit, amounts in BADGE_AMOUNTS.items()
}
SPACING_OPTIONS = {
    unit: sorted(amounts, key=float) for unit, amounts in SPACING_AMOUNTS.items()
}
LOGO_SIZE_OPTIONS = {unit: sorted(amounts, key=float) for unit, amounts in LOGO_AMOUNTS.items()}
COPY_OPTIONS = list(range(1, 25))
LOGO_BADGE = Badge(
    id="makespace-logo",
    name="MakeSpace Madrid Logo",
    path="assets/images/logo/makespace-bk.svg",
    raw_url=(
        "https://raw.githubusercontent.com/makespacemadrid/"
        "makespacemadrid.github.io/main/assets/images/logo/makespace-bk.svg"
    ),
    extension=".svg",
)


def points_per_unit(unit: str) -> float:
    """Return the number of PDF points in one displayed unit."""

    if unit == "cm":
        return 72.0 / CENTIMETERS_PER_INCH
    return 72.0


def append_logo_placements(layouts: list[PanelLayout], logo_size_inches: float) -> list[PanelLayout]:
    """Append the optional MakeSpace logo placement to every panel layout."""

    logo_size = logo_size_inches * 72.0
    adjusted_layouts: list[PanelLayout] = []
    for layout in layouts:
        width = min(logo_size, layout.width)
        height = min(logo_size, layout.height)
        margin = min(18.0, max(0.0, (layout.height - height) / 2))
        placement = Placement(
            badge_id=LOGO_BADGE.id,
            x=layout.x + (layout.width - width) / 2,
            y=layout.y + margin,
            width=width,
            height=height,
        )
        adjusted_layouts.append(
            PanelLayout(
                layout.side,
                layout.x,
                layout.y,
                layout.width,
                layout.height,
                [*layout.placements, placement],
            )
        )
    return adjusted_layouts


def badge_to_dict(badge: Badge) -> dict[str, str | None]:
    """Serialize a badge for JSON APIs and MCP tools."""

    if badge.id == LOGO_BADGE.id:
        source = "logo"
    elif badge.local_path:
        source = "upload"
    elif badge.raw_url.startswith("/static/demo-badge.svg"):
        source = "fallback"
    else:
        source = "upstream"
    return {
        "id": badge.id,
        "name": badge.name,
        "path": badge.path,
        "raw_url": badge.raw_url,
        "extension": badge.extension,
        "source": source,
    }


def options_payload() -> dict:
    """Return supported option values and defaults for API consumers."""

    return {
        "page_sizes": PAGE_SIZES,
        "orientations": ORIENTATIONS,
        "layout_modes": LAYOUT_MODES,
        "order_modes": ORDER_MODES,
        "units": UNITS,
        "badge_size_options": BADGE_SIZE_OPTIONS,
        "spacing_options": SPACING_OPTIONS,
        "logo_size_options": LOGO_SIZE_OPTIONS,
        "copy_options": COPY_OPTIONS,
        "defaults": {
            "page_size": "a4",
            "orientation": "portrait",
            "mode": "grid",
            "unit": DEFAULT_UNIT,
            "badge_size": DEFAULT_BADGE_AMOUNTS[DEFAULT_UNIT],
            "spacing": DEFAULT_SPACING_AMOUNTS[DEFAULT_UNIT],
            "include_logo": False,
            "logo_size": DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT],
            "copies": 1,
            "order": "selected",
            "sides": ["front", "back"],
            "mirror": True,
        },
    }


def placement_to_dict(placement: Placement, unit: str) -> dict:
    """Serialize a placement in both display units and PDF points."""

    divisor = points_per_unit(unit)
    return {
        "badge_id": placement.badge_id,
        "x": placement.x / divisor,
        "y": placement.y / divisor,
        "width": placement.width / divisor,
        "height": placement.height / divisor,
        "rotation": placement.rotation,
        "unit": unit,
        "points": {
            "x": placement.x,
            "y": placement.y,
            "width": placement.width,
            "height": placement.height,
        },
    }


def layout_to_dict(layout: PanelLayout, unit: str) -> dict:
    """Serialize a panel layout in both display units and PDF points."""

    divisor = points_per_unit(unit)
    return {
        "side": layout.side,
        "x": layout.x / divisor,
        "y": layout.y / divisor,
        "width": layout.width / divisor,
        "height": layout.height / divisor,
        "unit": unit,
        "points": {
            "x": layout.x,
            "y": layout.y,
            "width": layout.width,
            "height": layout.height,
        },
        "placements": [placement_to_dict(placement, unit) for placement in layout.placements],
    }


def apply_json_manual_placements(
    layouts: list[PanelLayout],
    page_height: float,
    unit: str,
    manual_placements: list,
) -> list[PanelLayout]:
    """Apply API manual placement overrides addressed by layout/placement index."""

    if not manual_placements:
        return layouts
    overrides = {}
    for item in manual_placements:
        if not isinstance(item, dict):
            continue
        try:
            key = (int(item.get("layout_index", -1)), int(item.get("placement_index", -1)))
        except (TypeError, ValueError):
            continue
        overrides[key] = item
    divisor = points_per_unit(unit)
    adjusted_layouts: list[PanelLayout] = []
    for layout_index, layout in enumerate(layouts):
        placements = []
        for placement_index, placement in enumerate(layout.placements):
            override = overrides.get((layout_index, placement_index))
            if not override:
                placements.append(placement)
                continue
            x = _json_coordinate(override.get("x"), placement.x, divisor)
            preview_y = _json_coordinate(
                override.get("y"), page_height - placement.y - placement.height, divisor
            )
            rotation = _json_float(override.get("rotation"), placement.rotation)
            placements.append(
                Placement(
                    badge_id=placement.badge_id,
                    x=x,
                    y=page_height - preview_y - placement.height,
                    width=placement.width,
                    height=placement.height,
                    rotation=rotation,
                )
            )
        adjusted_layouts.append(
            PanelLayout(layout.side, layout.x, layout.y, layout.width, layout.height, placements)
        )
    return adjusted_layouts


def _json_coordinate(value, default: float, point_multiplier: float) -> float:
    try:
        return float(value) * point_multiplier if value not in {None, ""} else default
    except (TypeError, ValueError):
        return default


def _json_float(value, default: float) -> float:
    try:
        return float(value) if value not in {None, ""} else default
    except (TypeError, ValueError):
        return default


def json_form_values(options: dict) -> dict[str, str]:
    """Normalize JSON option values into form-like strings for existing parsing."""

    values = {}
    for key, value in options.items():
        if isinstance(value, bool):
            values[key] = "on" if value else "off"
        elif value is not None and not isinstance(value, list):
            values[key] = str(value)
    return values


def json_getlist(options: dict):
    """Return a getlist-compatible callback for JSON option arrays."""

    def getlist(key: str) -> list[str]:
        value = options.get(key, [])
        if isinstance(value, list):
            return [str(item) for item in value]
        if value in {None, ""}:
            return []
        return [str(value)]

    return getlist


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
            orientations=ORIENTATIONS,
            order_modes=ORDER_MODES,
            units=UNITS,
            default_unit=DEFAULT_UNIT,
            default_badge_amounts=DEFAULT_BADGE_AMOUNTS,
            default_spacing_amounts=DEFAULT_SPACING_AMOUNTS,
            default_logo_amounts=DEFAULT_LOGO_AMOUNTS,
            badge_size_options=BADGE_SIZE_OPTIONS,
            spacing_options=SPACING_OPTIONS,
            logo_size_options=LOGO_SIZE_OPTIONS,
            copy_options=COPY_OPTIONS,
        )

    @app.post("/refresh")
    def refresh() -> Response:
        refresh_badges()
        return redirect(url_for("index"))

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str) -> Response:
        return send_from_directory(_upload_folder(), filename)

    @app.get("/api/v1/health")
    def api_health() -> Response:
        return jsonify({"status": "ok", "service": "tshirt_templates"})

    @app.get("/api/v1/options")
    def api_options() -> Response:
        return jsonify(options_payload())

    @app.get("/api/v1/badges")
    def api_badges() -> Response:
        if request.args.get("refresh") in {"1", "true", "yes"}:
            refresh_badges()
        order = request.args.get("order", "alphabetical")
        badges = order_badges(_available_badges(), order)
        include_logo = request.args.get("include_logo") in {"1", "true", "yes"}
        if include_logo:
            badges = [*badges, LOGO_BADGE]
        return jsonify({"badges": [badge_to_dict(badge) for badge in badges]})

    @app.post("/api/v1/layouts/preview")
    def api_layout_preview() -> Response:
        payload = request.get_json(silent=True) or {}
        result = _layout_from_json(payload)
        return jsonify(result)

    @app.get("/mcp")
    def mcp_metadata() -> Response:
        return jsonify(_mcp_metadata())

    @app.post("/mcp")
    def mcp_json_rpc() -> Response:
        message = request.get_json(silent=True) or {}
        response = _handle_mcp_message(message)
        status = 400 if "error" in response else 200
        return jsonify(response), status

    @app.post("/preview")
    def preview() -> str:
        badge_ids, badges = _selected_badges_with_uploads()
        page_size, layouts = _layout_from_form(badge_ids)
        layouts = _append_logo_placements(layouts)
        layouts = _apply_manual_placements(layouts, page_size)
        return render_template(
            "preview.html",
            badges=badges,
            badge_lookup={badge.id: badge for badge in badges},
            layouts=layouts,
            page_width=page_size[0],
            page_height=page_size[1],
            form=request.form,
            selected_ids=badge_ids,
            unit=_layout_options().unit,
            points_per_unit=_points_per_unit(_layout_options().unit),
        )

    @app.post("/pdf")
    def pdf() -> Response:
        badge_ids, badges = _selected_badges_with_uploads()
        page_size, layouts = _layout_from_form(badge_ids)
        layouts = _append_logo_placements(layouts)
        layouts = _apply_manual_placements(layouts, page_size)
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

    def _selected_badges_with_uploads() -> tuple[list[str], list]:
        uploaded = save_uploaded_badges(request.files.getlist("uploads"), _upload_folder())
        badge_ids = [*request.form.getlist("badges"), *[badge.id for badge in uploaded]]
        badges = get_badges_by_id(badge_ids, _upload_folder())
        options = _layout_options()
        ordered_badges = order_badges(badges, options.order)
        render_badges = [*ordered_badges, LOGO_BADGE] if options.include_logo else ordered_badges
        return [badge.id for badge in ordered_badges], render_badges

    def _layout_options():
        return parse_layout_options(request.form, request.form.getlist)

    def _layout_from_form(badge_ids: list[str]):
        options = _layout_options()
        return place_badges(
            badge_ids=badge_ids,
            sides=options.sides,
            page_size=options.page_size,
            orientation=options.orientation,
            mode=options.mode,
            badge_size_inches=options.badge_size_inches,
            spacing_inches=options.spacing_inches,
            copies=options.copies,
        )

    def _append_logo_placements(layouts: list[PanelLayout]) -> list[PanelLayout]:
        options = _layout_options()
        if not options.include_logo:
            return layouts
        return append_logo_placements(layouts, options.logo_size_inches)

    def _apply_manual_placements(
        layouts: list[PanelLayout], page_size: tuple[float, float]
    ) -> list[PanelLayout]:
        page_height = page_size[1]
        adjusted_layouts: list[PanelLayout] = []
        for layout_index, layout in enumerate(layouts):
            placements: list[Placement] = []
            for placement_index, placement in enumerate(layout.placements):
                prefix = f"manual_{layout_index}_{placement_index}"
                manual_x = request.form.get(f"{prefix}_x")
                manual_y = request.form.get(f"{prefix}_y")
                manual_rotation = request.form.get(f"{prefix}_rotation")
                if manual_x is None and manual_y is None and manual_rotation is None:
                    placements.append(placement)
                    continue
                points_per_unit = _points_per_unit(_layout_options().unit)
                x = _manual_coordinate_points(manual_x, placement.x, points_per_unit)
                preview_y = _manual_coordinate_points(
                    manual_y, page_height - placement.y - placement.height, points_per_unit
                )
                y = page_height - preview_y - placement.height
                rotation = _manual_float(manual_rotation, placement.rotation)
                placements.append(
                    Placement(
                        badge_id=placement.badge_id,
                        x=x,
                        y=y,
                        width=placement.width,
                        height=placement.height,
                        rotation=rotation,
                    )
                )
            adjusted_layouts.append(
                PanelLayout(
                    layout.side, layout.x, layout.y, layout.width, layout.height, placements
                )
            )
        return adjusted_layouts

    def _manual_coordinate_points(
        value: str | None, default: float, points_per_unit: float
    ) -> float:
        try:
            return float(value) * points_per_unit if value not in {None, ""} else default
        except (TypeError, ValueError):
            return default

    def _manual_float(value: str | None, default: float) -> float:
        try:
            return float(value) if value not in {None, ""} else default
        except (TypeError, ValueError):
            return default

    def _points_per_unit(unit: str) -> float:
        return points_per_unit(unit)

    def _layout_from_json(payload: dict) -> dict:
        raw_options = payload.get("options", {})
        if not isinstance(raw_options, dict):
            raw_options = {}
        options = parse_layout_options(json_form_values(raw_options), json_getlist(raw_options))
        badge_ids = [str(badge_id) for badge_id in payload.get("badge_ids", [])]
        badges = get_badges_by_id(badge_ids, _upload_folder())
        ordered_badges = order_badges(badges, options.order)
        ordered_ids = [badge.id for badge in ordered_badges]
        render_badges = [*ordered_badges, LOGO_BADGE] if options.include_logo else ordered_badges
        page_size, layouts = place_badges(
            badge_ids=ordered_ids,
            sides=options.sides,
            page_size=options.page_size,
            orientation=options.orientation,
            mode=options.mode,
            badge_size_inches=options.badge_size_inches,
            spacing_inches=options.spacing_inches,
            copies=options.copies,
        )
        if options.include_logo:
            layouts = append_logo_placements(layouts, options.logo_size_inches)
        layouts = apply_json_manual_placements(
            layouts, page_size[1], options.unit, payload.get("manual_placements", [])
        )
        divisor = points_per_unit(options.unit)
        return {
            "page": {
                "width": page_size[0] / divisor,
                "height": page_size[1] / divisor,
                "unit": options.unit,
                "points": {"width": page_size[0], "height": page_size[1]},
            },
            "badges": [badge_to_dict(badge) for badge in render_badges],
            "layouts": [layout_to_dict(layout, options.unit) for layout in layouts],
            "options": {
                "page_size": options.page_size,
                "orientation": options.orientation,
                "mode": options.mode,
                "unit": options.unit,
                "badge_size": options.badge_size,
                "spacing": options.spacing,
                "include_logo": options.include_logo,
                "logo_size": options.logo_size,
                "copies": options.copies,
                "order": options.order,
                "sides": options.sides,
                "mirror": options.mirror,
            },
        }

    def _mcp_metadata() -> dict:
        return {
            "name": "tshirt_templates",
            "protocol": "mcp-json-rpc",
            "endpoint": "/mcp",
            "capabilities": {"tools": True, "resources": True},
            "tools": ["get_options", "list_badges", "compute_layout"],
            "resources": ["tshirt://options", "tshirt://badges"],
        }

    def _mcp_tools() -> list[dict]:
        return [
            {
                "name": "get_options",
                "description": "Return supported template options and defaults.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "list_badges",
                "description": "Return available badge artwork.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean"},
                        "order": {"type": "string"},
                        "include_logo": {"type": "boolean"},
                    },
                },
            },
            {
                "name": "compute_layout",
                "description": "Compute a template layout from badge IDs and options.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "badge_ids": {"type": "array", "items": {"type": "string"}},
                        "options": {"type": "object"},
                    },
                },
            },
        ]

    def _mcp_result(message_id, payload: dict) -> dict:
        return {"jsonrpc": "2.0", "id": message_id, "result": payload}

    def _mcp_error(message_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}

    def _handle_mcp_message(message: dict) -> dict:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params") or {}
        if method == "initialize":
            return _mcp_result(
                message_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "tshirt_templates", "version": "0.1.0"},
                },
            )
        if method == "tools/list":
            return _mcp_result(message_id, {"tools": _mcp_tools()})
        if method == "resources/list":
            return _mcp_result(
                message_id,
                {
                    "resources": [
                        {"uri": "tshirt://options", "name": "Template options"},
                        {"uri": "tshirt://badges", "name": "Badge catalog"},
                    ]
                },
            )
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            if tool_name == "get_options":
                return _mcp_result(message_id, {"structuredContent": options_payload()})
            if tool_name == "list_badges":
                if arguments.get("refresh"):
                    refresh_badges()
                order = str(arguments.get("order", "alphabetical"))
                badges = order_badges(_available_badges(), order)
                if arguments.get("include_logo"):
                    badges = [*badges, LOGO_BADGE]
                return _mcp_result(
                    message_id,
                    {"structuredContent": {"badges": [badge_to_dict(badge) for badge in badges]}},
                )
            if tool_name == "compute_layout":
                return _mcp_result(message_id, {"structuredContent": _layout_from_json(arguments)})
            return _mcp_error(message_id, -32602, f"Unknown tool: {tool_name}")
        return _mcp_error(message_id, -32601, f"Unknown MCP method: {method}")

    return app


app = create_app()
