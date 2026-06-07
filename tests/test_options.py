from pytest import approx

from tshirt_templates.options import LayoutOptions, parse_layout_options


def _getlist(values):
    return lambda key: list(values.get(key, []))


def test_parse_layout_options_accepts_valid_values():
    values = {
        "page_size": "a3",
        "orientation": "landscape",
        "mode": "border",
        "unit": "in",
        "badge_size": "2.0",
        "spacing": "0.6",
        "copies": "3",
        "include_logo": "on",
        "logo_size": "3.0",
        "mirror": "on",
        "order": "category",
        "front_text": "  Ada   Lovelace  ",
        "back_text": "MakeSpace Madrid",
        "text_font": "dejavu",
        "include_print_marks": "on",
        "include_cut_lines": "on",
        "include_curve_effect": "on",
        "curve_device": "mug",
        "curve_diameter": "3.25",
    }

    assert parse_layout_options(values, _getlist({"sides": ["back"]})) == LayoutOptions(
        sides=["back"],
        page_size="a3",
        orientation="landscape",
        mode="border",
        unit="in",
        badge_size="2.0",
        spacing="0.6",
        include_logo=True,
        logo_size="3.0",
        badge_size_inches=2.0,
        spacing_inches=0.6,
        logo_size_inches=3.0,
        copies=3,
        order="category",
        mirror=True,
        front_text="Ada Lovelace",
        back_text="MakeSpace Madrid",
        text_font="dejavu",
        include_print_marks=True,
        include_cut_lines=True,
        include_curve_effect=True,
        curve_device="mug",
        curve_diameter="3.25",
        curve_diameter_inches=3.25,
    )


def test_parse_layout_options_normalizes_invalid_values():
    values = {
        "page_size": "poster",
        "orientation": "sideways",
        "mode": "zigzag",
        "unit": "meters",
        "badge_size": "huge",
        "spacing": "-4",
        "copies": "999",
        "include_logo": "maybe",
        "logo_size": "100",
        "mirror": "off",
        "order": "unknown",
        "front_text": "x" * 80,
        "text_font": "papyrus",
        "include_print_marks": "maybe",
        "include_cut_lines": "maybe",
        "include_curve_effect": "maybe",
        "curve_device": "bucket",
        "curve_diameter": "0",
    }

    options = parse_layout_options(values, _getlist({"sides": ["front", "sleeve"]}))

    assert options == LayoutOptions(
        sides=["front"],
        page_size="a4",
        orientation="portrait",
        mode="grid",
        unit="cm",
        badge_size="3.5",
        spacing="0.5",
        include_logo=False,
        logo_size="5.0",
        badge_size_inches=approx(3.5 / 2.54),
        spacing_inches=approx(0.5 / 2.54),
        logo_size_inches=approx(5.0 / 2.54),
        copies=24,
        order="selected",
        mirror=False,
        front_text="x" * 64,
        text_font="ubuntu",
        include_print_marks=False,
        include_cut_lines=False,
        include_curve_effect=False,
        curve_device="custom",
        curve_diameter="2.5",
        curve_diameter_inches=approx(2.5 / 2.54),
    )


def test_parse_layout_options_defaults_to_both_sides_and_mirror_when_none_are_valid():
    options = parse_layout_options({}, _getlist({"sides": ["sleeve"]}))

    assert options.sides == ["front", "back"]
    assert options.page_size == "a4"
    assert options.unit == "cm"
    assert options.mirror is True


def test_parse_layout_options_accepts_m_pixel_mode():
    options = parse_layout_options({"mode": "m-pixels"}, _getlist({"sides": ["front"]}))

    assert options.mode == "m-pixels"


def test_parse_layout_options_accepts_new_decorative_modes():
    for mode in ["circle", "spiral", "wave"]:
        options = parse_layout_options({"mode": mode}, _getlist({"sides": ["front"]}))

        assert options.mode == mode


def test_parse_layout_options_accepts_alphabetical_order():
    options = parse_layout_options({"order": "alphabetical"}, _getlist({"sides": ["front"]}))

    assert options.order == "alphabetical"


def test_parse_layout_options_converts_centimeters_to_inches():
    options = parse_layout_options(
        {"unit": "cm", "badge_size": "10.0", "spacing": "2.0", "logo_size": "15.0", "curve_diameter": "12.0"},
        _getlist({"sides": ["front"]}),
    )

    assert options.badge_size_inches == approx(10.0 / 2.54)
    assert options.spacing_inches == approx(2.0 / 2.54)
    assert options.logo_size_inches == approx(15.0 / 2.54)
    assert options.curve_diameter_inches == approx(12.0 / 2.54)


def test_parse_layout_options_uses_curve_device_preset_when_no_diameter_is_supplied():
    options = parse_layout_options(
        {"unit": "cm", "curve_device": "mug", "include_curve_effect": "on"},
        _getlist({"sides": ["front"]}),
    )

    assert options.include_curve_effect is True
    assert options.curve_device == "mug"
    assert options.curve_diameter == "8.2"
    assert options.curve_diameter_inches == approx(8.2 / 2.54)
