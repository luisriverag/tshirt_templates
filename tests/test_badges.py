import builtins
import sys
from types import SimpleNamespace

from tshirt_templates import badges


def test_list_badges_falls_back_when_requests_is_unavailable(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("requests unavailable in test")
        return original_import(name, *args, **kwargs)

    badges.list_badges.cache_clear()
    monkeypatch.setattr(builtins, "__import__", fake_import)

    discovered = badges.list_badges()

    assert discovered == [
        badges.Badge(
            id="demo-badge.svg",
            name="Demo Badge",
            path="demo-badge.svg",
            raw_url="/static/demo-badge.svg",
            extension=".svg",
        )
    ]


def test_list_badges_filters_and_sorts_github_tree(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "tree": [
                    {"type": "blob", "path": "docs/readme.md"},
                    {"type": "tree", "path": "icons"},
                    {"type": "blob", "path": "badges/zeta-badge.svg"},
                    {"type": "blob", "path": ".hidden.svg"},
                    {"type": "blob", "path": "badges/alpha_badge.PNG"},
                ]
            }

    fake_requests = SimpleNamespace(get=lambda url, timeout: FakeResponse())
    badges.list_badges.cache_clear()
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    discovered = badges.list_badges()

    assert [badge.path for badge in discovered] == [
        "badges/alpha_badge.PNG",
        "badges/zeta-badge.svg",
    ]
    assert discovered[0].name == "Alpha Badge"
    assert discovered[0].raw_url.endswith("/badges/alpha_badge.PNG")


def test_list_badges_automatically_refreshes_after_ttl(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            calls.append(len(calls))
            path = "badges/first.svg" if len(calls) == 1 else "badges/second.svg"
            return {"tree": [{"type": "blob", "path": path}]}

    fake_requests = SimpleNamespace(get=lambda url, timeout: FakeResponse())
    badges.list_badges.cache_clear()
    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    monkeypatch.setattr(badges, "time", lambda: 0)

    first = badges.list_badges()
    second_same_bucket = badges.list_badges()

    monkeypatch.setattr(badges, "time", lambda: badges.BADGE_CACHE_TTL_SECONDS)
    refreshed = badges.list_badges()

    assert [badge.path for badge in first] == ["badges/first.svg"]
    assert second_same_bucket == first
    assert [badge.path for badge in refreshed] == ["badges/second.svg"]
