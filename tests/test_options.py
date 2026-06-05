from tshirt_templates.options import LayoutOptions, parse_layout_options


def _getlist(values):
    return lambda key: list(values.get(key, []))


def test_parse_layout_options_accepts_valid_values():
    values = {
        "page_size": "a3",
        "mode": "border",
        "badge_size": "2.25",
        "spacing": "0.5",
        "copies": "3",
        "mirror": "on",
    }

    assert parse_layout_options(values, _getlist({"sides": ["back"]})) == LayoutOptions(
        sides=["back"],
        page_size="a3",
        mode="border",
        badge_size_inches=2.25,
        spacing_inches=0.5,
        copies=3,
        mirror=True,
    )


def test_parse_layout_options_normalizes_invalid_values():
    values = {
        "page_size": "poster",
        "mode": "spiral",
        "badge_size": "huge",
        "spacing": "-4",
        "copies": "999",
        "mirror": "off",
    }

    options = parse_layout_options(values, _getlist({"sides": ["front", "sleeve"]}))

    assert options == LayoutOptions(
        sides=["front"],
        page_size="letter",
        mode="grid",
        badge_size_inches=1.35,
        spacing_inches=0.0,
        copies=24,
        mirror=False,
    )


def test_parse_layout_options_defaults_to_both_sides_when_none_are_valid():
    options = parse_layout_options({}, _getlist({"sides": ["sleeve"]}))

    assert options.sides == ["front", "back"]
