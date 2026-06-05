from tshirt_templates.layout import compute_panels, expand_badges, page_size_points, place_badges


def test_page_size_points_applies_orientation():
    assert page_size_points("letter") == (612.0, 792.0)
    assert page_size_points("letter", "portrait") == (612.0, 792.0)
    assert page_size_points("letter", "landscape") == (792.0, 612.0)


def test_expand_badges_clamps_to_at_least_one_copy():
    assert expand_badges(["a", "b"], 0) == ["a", "b"]


def test_front_and_back_panels_are_side_by_side():
    panels = compute_panels(612, 792, ["front", "back"])
    assert set(panels) == {"front", "back"}
    assert panels["front"][0] < panels["back"][0]
    assert panels["front"][2] == panels["back"][2]


def test_grid_layout_places_each_copy_on_each_selected_panel():
    page_size, layouts = place_badges(
        badge_ids=["alpha", "beta"],
        sides=["front", "back"],
        page_size="letter",
        mode="grid",
        copies=2,
    )
    assert page_size == (612.0, 792.0)
    assert len(layouts) == 2
    assert all(len(layout.placements) == 4 for layout in layouts)


def test_landscape_layout_uses_wide_page_size():
    page_size, layouts = place_badges(
        badge_ids=["alpha"],
        sides=["front"],
        page_size="a4",
        orientation="landscape",
    )

    assert page_size == (841.89, 595.28)
    assert layouts[0].width > layouts[0].height


def test_scatter_layout_is_deterministic():
    first = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    second = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    assert first == second


def test_decorative_layout_modes_place_badges_in_bounds():
    for mode in ["circle", "spiral", "wave"]:
        _, layouts = place_badges(
            [f"badge-{index}" for index in range(8)],
            ["front"],
            mode=mode,
            badge_size_inches=1.0,
            spacing_inches=0.1,
        )
        layout = layouts[0]

        assert len(layout.placements) == 8
        assert any(placement.rotation != 0 for placement in layout.placements)
        for placement in layout.placements:
            assert layout.x <= placement.x <= layout.x + layout.width - placement.width
            assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_single_badge_decorative_layout_modes_center_badge():
    for mode in ["circle", "spiral", "wave"]:
        _, layouts = place_badges(["alpha"], ["front"], mode=mode)
        layout = layouts[0]
        placement = layout.placements[0]

        assert placement.x == layout.x + (layout.width - placement.width) / 2
        assert placement.y == layout.y + (layout.height - placement.height) / 2


def test_border_layout_places_badges_around_panel_edges():
    _, layouts = place_badges(["a", "b", "c", "d"], ["front"], mode="border")
    layout = layouts[0]
    xs = [placement.x for placement in layout.placements]
    ys = [placement.y for placement in layout.placements]

    assert len(layout.placements) == 4
    assert min(xs) >= layout.x
    assert max(xs) <= layout.x + layout.width
    assert min(ys) >= layout.y
    assert max(ys) <= layout.y + layout.height
    assert {placement.rotation for placement in layout.placements}.issubset({-90.0, 0.0, 90.0, 180.0})


def test_m_pixel_layout_places_badges_in_bounds_with_square_pixels():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(13)],
        ["front"],
        mode="m-pixels",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    layout = layouts[0]

    assert len(layout.placements) == 13
    assert {placement.rotation for placement in layout.placements} == {0.0}
    for placement in layout.placements:
        assert placement.width == placement.height
        assert layout.x <= placement.x <= layout.x + layout.width - placement.width
        assert layout.y <= placement.y <= layout.y + layout.height - placement.height


def test_m_pixel_layout_repeats_selected_badges_to_fill_shape():
    _, layouts = place_badges(
        ["alpha", "beta"],
        ["front"],
        mode="m-pixels",
        badge_size_inches=1.0,
        spacing_inches=0.1,
    )

    placements = layouts[0].placements

    assert len(placements) == 13
    assert [placement.badge_id for placement in placements[:4]] == ["alpha", "beta", "alpha", "beta"]
    assert {placement.badge_id for placement in placements} == {"alpha", "beta"}


def test_m_pixel_layout_shrinks_pixels_to_fit_the_panel():
    _, layouts = place_badges(
        [f"badge-{index}" for index in range(25)],
        ["front", "back"],
        mode="m-pixels",
        badge_size_inches=4.0,
        spacing_inches=0.0,
    )

    assert all(len(layout.placements) == 25 for layout in layouts)
    assert all(placement.width < 4.0 * 72 for layout in layouts for placement in layout.placements)
