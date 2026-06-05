from tshirt_templates.badges import Badge, badge_category, order_badges


def _badge(path, name):
    return Badge(path, name, path, f"/raw/{path}", ".svg")


def test_badge_category_uses_parent_path_or_uncategorized():
    assert badge_category(_badge("electronics/led.svg", "LED")) == "electronics"
    assert badge_category(_badge("plain.svg", "Plain")) == "Uncategorized"


def test_order_badges_can_sort_alphabetically_or_by_category():
    badges = [
        _badge("wood/zebra.svg", "Zebra"),
        _badge("electronics/alpha.svg", "Alpha"),
        _badge("wood/alpha.svg", "Alpha"),
    ]

    assert [badge.id for badge in order_badges(badges, "selected")] == [
        "wood/zebra.svg",
        "electronics/alpha.svg",
        "wood/alpha.svg",
    ]
    assert [badge.id for badge in order_badges(badges, "alphabetical")] == [
        "electronics/alpha.svg",
        "wood/alpha.svg",
        "wood/zebra.svg",
    ]
    assert [badge.id for badge in order_badges(badges, "category")] == [
        "electronics/alpha.svg",
        "wood/alpha.svg",
        "wood/zebra.svg",
    ]
