from tshirt_templates.options import LayoutOptions, parse_layout_options


def _getlist(values):
    return lambda key: list(values.get(key, []))


def test_parse_layout_options_accepts_valid_values():
    values = {
        "page_size": "a3",
        "orientation": "landscape",
        "mode": "border",
        "badge_size": "2.25",
        "spacing": "0.5",
        "copies": "3",
        "mirror": "on",
    }

    assert parse_layout_options(values, _getlist({"sides": ["back"]})) == LayoutOptions(
        sides=["back"],
        page_size="a3",
        orientation="landscape",
        mode="border",
        badge_size_inches=2.25,
        spacing_inches=0.5,
        copies=3,
        mirror=True,
    )


def test_parse_layout_options_normalizes_invalid_values():
    values = {
        "page_size": "poster",
        "orientation": "sideways",
        "mode": "zigzag",
        "badge_size": "huge",
        "spacing": "-4",
        "copies": "999",
        "mirror": "off",
    }

    options = parse_layout_options(values, _getlist({"sides": ["front", "sleeve"]}))

    assert options == LayoutOptions(
        sides=["front"],
        page_size="letter",
        orientation="portrait",
        mode="grid",
        badge_size_inches=1.35,
        spacing_inches=0.0,
        copies=24,
        mirror=False,
    )


def test_parse_layout_options_defaults_to_both_sides_and_mirror_when_none_are_valid():
    options = parse_layout_options({}, _getlist({"sides": ["sleeve"]}))

    assert options.sides == ["front", "back"]
    assert options.mirror is True


def test_parse_layout_options_accepts_m_pixel_mode():
    options = parse_layout_options({"mode": "m-pixels"}, _getlist({"sides": ["front"]}))

    assert options.mode == "m-pixels"


def test_parse_layout_options_accepts_new_decorative_modes():
    for mode in ["circle", "spiral", "wave"]:
        options = parse_layout_options({"mode": mode}, _getlist({"sides": ["front"]}))

        assert options.mode == mode
