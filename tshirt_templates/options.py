"""Request option parsing and validation for template generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

DEFAULT_SIDES = ("front", "back")
VALID_SIDES = frozenset(DEFAULT_SIDES)
VALID_PAGE_SIZES = frozenset({"letter", "a4", "a3"})
VALID_ORIENTATIONS = frozenset({"portrait", "landscape"})
VALID_LAYOUT_MODES = frozenset(
    {"grid", "rows", "diagonal", "scatter", "circle", "spiral", "wave", "border", "m-pixels"}
)


@dataclass(frozen=True)
class LayoutOptions:
    """Validated options used to generate a template layout."""

    sides: list[str]
    page_size: str = "letter"
    orientation: str = "portrait"
    mode: str = "grid"
    badge_size_inches: float = 1.35
    spacing_inches: float = 0.18
    copies: int = 1
    mirror: bool = True


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value in {"1", "true", "on", "yes"}


def _safe_float(value: str | None, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value if value not in {None, ""} else default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value if value not in {None, ""} else default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _valid_choice(value: str | None, valid_choices: frozenset[str], default: str) -> str:
    return value if value in valid_choices else default


def _valid_sides(raw_sides: list[str]) -> list[str]:
    sides = [side for side in DEFAULT_SIDES if side in raw_sides]
    return sides or list(DEFAULT_SIDES)


def parse_layout_options(
    values: Mapping[str, str],
    getlist: Callable[[str], list[str]],
) -> LayoutOptions:
    """Parse request-like values into safe layout options."""

    return LayoutOptions(
        sides=_valid_sides(getlist("sides")),
        page_size=_valid_choice(values.get("page_size"), VALID_PAGE_SIZES, "letter"),
        orientation=_valid_choice(values.get("orientation"), VALID_ORIENTATIONS, "portrait"),
        mode=_valid_choice(values.get("mode"), VALID_LAYOUT_MODES, "grid"),
        badge_size_inches=_safe_float(values.get("badge_size"), 1.35, 0.35, 4.0),
        spacing_inches=_safe_float(values.get("spacing"), 0.18, 0.0, 2.0),
        copies=_safe_int(values.get("copies"), 1, 1, 24),
        mirror=_truthy(values.get("mirror"), default=True),
    )
