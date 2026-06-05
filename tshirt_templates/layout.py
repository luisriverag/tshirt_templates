"""Automatic badge placement for t-shirt sublimation panels."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, cos, radians, sin, sqrt
from random import Random

PAGE_SIZES = {
    "letter": (612.0, 792.0),
    "a4": (595.28, 841.89),
    "a3": (841.89, 1190.55),
}
PANEL_MARGIN = 36.0
POINTS_PER_INCH = 72.0


@dataclass(frozen=True)
class Placement:
    """A single badge placement in PDF points."""

    badge_id: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0


@dataclass(frozen=True)
class PanelLayout:
    """Computed layout for one print side."""

    side: str
    x: float
    y: float
    width: float
    height: float
    placements: list[Placement]


def page_size_points(page_size: str) -> tuple[float, float]:
    """Return a supported PDF page size in points."""

    return PAGE_SIZES.get(page_size, PAGE_SIZES["letter"])


def expand_badges(badge_ids: list[str], copies: int) -> list[str]:
    """Repeat badge ids by copy count while keeping a stable order."""

    copies = max(1, min(copies, 24))
    return [badge_id for badge_id in badge_ids for _ in range(copies)]


def compute_panels(page_width: float, page_height: float, sides: list[str]) -> dict[str, tuple[float, float, float, float]]:
    """Return front/back panel rectangles for the selected sides."""

    selected = [side for side in ("front", "back") if side in sides]
    if not selected:
        selected = ["front"]

    content_x = PANEL_MARGIN
    content_y = PANEL_MARGIN
    content_width = page_width - 2 * PANEL_MARGIN
    content_height = page_height - 2 * PANEL_MARGIN

    if len(selected) == 1:
        return {selected[0]: (content_x, content_y, content_width, content_height)}

    gap = 24.0
    panel_width = (content_width - gap) / 2
    return {
        "front": (content_x, content_y, panel_width, content_height),
        "back": (content_x + panel_width + gap, content_y, panel_width, content_height),
    }


def _grid_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    count = len(ids)
    cols = max(1, int((width + spacing) // (badge_size + spacing)))
    rows = max(1, ceil(count / cols))
    actual_cols = min(cols, count)
    total_width = actual_cols * badge_size + max(0, actual_cols - 1) * spacing
    total_height = rows * badge_size + max(0, rows - 1) * spacing
    start_x = x + max(0, (width - total_width) / 2)
    start_y = y + height - max(0, (height - total_height) / 2) - badge_size

    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        row, col = divmod(index, cols)
        placements.append(
            Placement(
                badge_id=badge_id,
                x=start_x + col * (badge_size + spacing),
                y=start_y - row * (badge_size + spacing),
                width=badge_size,
                height=badge_size,
            )
        )
    return placements


def _rows_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    cols = max(1, int((width + spacing) // (badge_size + spacing)))
    rows = max(1, ceil(len(ids) / cols))
    row_gap = min(badge_size + spacing * 1.5, height / rows)
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        row, col = divmod(index, cols)
        row_count = min(cols, len(ids) - row * cols)
        offset = spacing * 0.5 if row % 2 else 0
        total_width = row_count * badge_size + max(0, row_count - 1) * spacing + offset
        start_x = x + max(0, (width - total_width) / 2) + offset
        placement_y = y + height - (row + 1) * row_gap + (row_gap - badge_size) / 2
        placements.append(
            Placement(badge_id, start_x + col * (badge_size + spacing), placement_y, badge_size, badge_size)
        )
    return placements


def _diagonal_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    angle = -28.0
    diagonal = sqrt(width * width + height * height)
    step = max(badge_size + spacing, diagonal / max(1, len(ids)))
    center_x = x + width / 2
    center_y = y + height / 2
    start = -step * (len(ids) - 1) / 2
    placements: list[Placement] = []
    for index, badge_id in enumerate(ids):
        distance = start + index * step
        px = center_x + cos(radians(angle)) * distance - badge_size / 2
        py = center_y + sin(radians(angle)) * distance - badge_size / 2
        placements.append(
            Placement(
                badge_id,
                min(max(px, x), x + width - badge_size),
                min(max(py, y), y + height - badge_size),
                badge_size,
                badge_size,
                angle,
            )
        )
    return placements


def _scatter_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    rng = Random("tshirt-template-scatter")
    placements: list[Placement] = []
    for badge_id in ids:
        px = x + rng.random() * max(1, width - badge_size)
        py = y + rng.random() * max(1, height - badge_size)
        rotation = rng.choice([-18, -10, -6, 0, 6, 10, 18])
        placements.append(Placement(badge_id, px, py, badge_size, badge_size, rotation))
    return placements


def _border_positions(ids: list[str], panel: tuple[float, float, float, float], badge_size: float, spacing: float) -> list[Placement]:
    x, y, width, height = panel
    if not ids:
        return []

    step = badge_size + spacing
    positions: list[tuple[float, float, float]] = []

    top_y = y + height - badge_size
    bottom_y = y
    left_x = x
    right_x = x + width - badge_size

    horizontal_slots = max(1, int((width + spacing) // step))
    vertical_slots = max(0, int((height - 2 * step + spacing) // step))

    for slot in range(horizontal_slots):
        px = x + slot * step
        if px <= right_x:
            positions.append((px, top_y, 0.0))
    for slot in range(vertical_slots):
        py = top_y - (slot + 1) * step
        if py >= bottom_y + step:
            positions.append((right_x, py, 90.0))
    for slot in range(horizontal_slots):
        px = right_x - slot * step
        if px >= left_x:
            positions.append((px, bottom_y, 180.0))
    for slot in range(vertical_slots):
        py = bottom_y + (slot + 1) * step
        if py <= top_y - step:
            positions.append((left_x, py, -90.0))

    if not positions:
        positions = [(x + (width - badge_size) / 2, y + (height - badge_size) / 2, 0.0)]

    placements = []
    for index, badge_id in enumerate(ids):
        px, py, rotation = positions[index % len(positions)]
        inset = (index // len(positions)) * min(spacing, badge_size * 0.2)
        placements.append(
            Placement(
                badge_id,
                min(max(px + inset, x), x + width - badge_size),
                min(max(py + inset, y), y + height - badge_size),
                badge_size,
                badge_size,
                rotation,
            )
        )
    return placements


def place_badges(
    badge_ids: list[str],
    sides: list[str],
    page_size: str = "letter",
    mode: str = "grid",
    badge_size_inches: float = 1.35,
    spacing_inches: float = 0.18,
    copies: int = 1,
) -> tuple[tuple[float, float], list[PanelLayout]]:
    """Compute printable panel layouts for selected badges."""

    page_width, page_height = page_size_points(page_size)
    badge_size = max(0.35, min(badge_size_inches, 4.0)) * POINTS_PER_INCH
    spacing = max(0.0, min(spacing_inches, 2.0)) * POINTS_PER_INCH
    expanded_ids = expand_badges(badge_ids, copies)
    panels = compute_panels(page_width, page_height, sides)
    placers = {
        "grid": _grid_positions,
        "rows": _rows_positions,
        "diagonal": _diagonal_positions,
        "scatter": _scatter_positions,
        "border": _border_positions,
    }
    placer = placers.get(mode, _grid_positions)

    layouts = [
        PanelLayout(side, *panel, placer(expanded_ids, panel, badge_size, spacing))
        for side, panel in panels.items()
    ]
    return (page_width, page_height), layouts
