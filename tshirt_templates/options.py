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
VALID_ORDER_MODES = frozenset({"selected", "alphabetical", "category"})
VALID_UNITS = frozenset({"cm", "in"})
VALID_TEXT_FONTS = frozenset({"ubuntu", "helvetica", "times", "courier", "dejavu"})
MAX_PANEL_TEXT_LENGTH = 64
CENTIMETERS_PER_INCH = 2.54
DEFAULT_PAGE_SIZE = "a4"
DEFAULT_UNIT = "cm"
DEFAULT_BADGE_AMOUNTS = {"cm": "3.5", "in": "1.4"}
DEFAULT_SPACING_AMOUNTS = {"cm": "0.5", "in": "0.2"}
DEFAULT_LOGO_AMOUNTS = {"cm": "5.0", "in": "2.0"}
BADGE_AMOUNTS = {
    "cm": frozenset(
        {
            "1.0",
            "1.5",
            "2.0",
            "2.5",
            "3.0",
            "3.5",
            "4.0",
            "4.5",
            "5.0",
            "6.0",
            "7.5",
            "10.0",
        }
    ),
    "in": frozenset(
        {
            "0.4",
            "0.6",
            "0.8",
            "1.0",
            "1.2",
            "1.4",
            "1.6",
            "1.8",
            "2.0",
            "2.5",
            "3.0",
            "4.0",
        }
    ),
}
SPACING_AMOUNTS = {
    "cm": frozenset({"0.0", "0.2", "0.5", "0.8", "1.0", "1.5", "2.0", "3.0", "4.0", "5.0"}),
    "in": frozenset(
        {"0.0", "0.1", "0.2", "0.3", "0.4", "0.6", "0.8", "1.2", "1.6", "2.0"}
    ),
}
LOGO_AMOUNTS = {
    "cm": frozenset({"2.5", "3.5", "5.0", "7.5", "10.0", "12.5", "15.0"}),
    "in": frozenset({"1.0", "1.4", "2.0", "3.0", "4.0", "5.0", "6.0"}),
}


@dataclass(frozen=True)
class LayoutOptions:
    """Validated options used to generate a template layout."""

    sides: list[str]
    page_size: str = DEFAULT_PAGE_SIZE
    orientation: str = "portrait"
    mode: str = "grid"
    unit: str = DEFAULT_UNIT
    badge_size: str = DEFAULT_BADGE_AMOUNTS[DEFAULT_UNIT]
    spacing: str = DEFAULT_SPACING_AMOUNTS[DEFAULT_UNIT]
    include_logo: bool = False
    logo_size: str = DEFAULT_LOGO_AMOUNTS[DEFAULT_UNIT]
    badge_size_inches: float = 3.5 / CENTIMETERS_PER_INCH
    spacing_inches: float = 0.5 / CENTIMETERS_PER_INCH
    logo_size_inches: float = 5.0 / CENTIMETERS_PER_INCH
    copies: int = 1
    order: str = "selected"
    mirror: bool = True
    include_print_marks: bool = False
    front_text: str = ""
    back_text: str = ""
    text_font: str = "ubuntu"


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value in {"1", "true", "on", "yes"}


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


def _unit_amount_inches(amount: str, unit: str) -> float:
    parsed = float(amount)
    if unit == "cm":
        return parsed / CENTIMETERS_PER_INCH
    return parsed


def _safe_panel_text(value: str | None) -> str:
    """Return text safe for shirt-panel labels, keeping it short enough to fit."""

    if value is None:
        return ""
    return " ".join(value.split())[:MAX_PANEL_TEXT_LENGTH]


def _valid_unit_amount(
    value: str | None,
    valid_amounts: dict[str, frozenset[str]],
    defaults: dict[str, str],
    unit: str,
) -> str:
    default = defaults[unit]
    return _valid_choice(value, valid_amounts[unit], default)


def parse_layout_options(
    values: Mapping[str, str],
    getlist: Callable[[str], list[str]],
) -> LayoutOptions:
    """Parse request-like values into safe layout options."""

    unit = _valid_choice(values.get("unit"), VALID_UNITS, DEFAULT_UNIT)
    badge_size = _valid_unit_amount(
        values.get("badge_size"), BADGE_AMOUNTS, DEFAULT_BADGE_AMOUNTS, unit
    )
    spacing = _valid_unit_amount(
        values.get("spacing"), SPACING_AMOUNTS, DEFAULT_SPACING_AMOUNTS, unit
    )
    logo_size = _valid_unit_amount(
        values.get("logo_size"), LOGO_AMOUNTS, DEFAULT_LOGO_AMOUNTS, unit
    )

    return LayoutOptions(
        sides=_valid_sides(getlist("sides")),
        page_size=_valid_choice(values.get("page_size"), VALID_PAGE_SIZES, DEFAULT_PAGE_SIZE),
        orientation=_valid_choice(values.get("orientation"), VALID_ORIENTATIONS, "portrait"),
        mode=_valid_choice(values.get("mode"), VALID_LAYOUT_MODES, "grid"),
        unit=unit,
        badge_size=badge_size,
        spacing=spacing,
        include_logo=_truthy(values.get("include_logo")),
        logo_size=logo_size,
        badge_size_inches=_unit_amount_inches(badge_size, unit),
        spacing_inches=_unit_amount_inches(spacing, unit),
        logo_size_inches=_unit_amount_inches(logo_size, unit),
        copies=_safe_int(values.get("copies"), 1, 1, 24),
        order=_valid_choice(values.get("order"), VALID_ORDER_MODES, "selected"),
        mirror=_truthy(values.get("mirror"), default=True),
        include_print_marks=_truthy(values.get("include_print_marks")),
        front_text=_safe_panel_text(values.get("front_text")),
        back_text=_safe_panel_text(values.get("back_text")),
        text_font=_valid_choice(values.get("text_font"), VALID_TEXT_FONTS, "ubuntu"),
    )
