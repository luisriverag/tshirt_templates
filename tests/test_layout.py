from tshirt_templates.layout import compute_panels, expand_badges, place_badges


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


def test_scatter_layout_is_deterministic():
    first = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    second = place_badges(["a", "b", "c"], ["front"], mode="scatter")[1][0].placements
    assert first == second


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
