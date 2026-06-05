"""Badge discovery for the MakeSpace Madrid open-badges repository."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from time import time
from typing import Iterable

GITHUB_TREE_URL = (
    "https://api.github.com/repos/makespacemadrid/open-badges/git/trees/HEAD?recursive=1"
)
RAW_BASE_URL = "https://raw.githubusercontent.com/makespacemadrid/open-badges/HEAD"
IMAGE_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg")
BADGE_CACHE_TTL_SECONDS = 10 * 60


@dataclass(frozen=True)
class Badge:
    """A renderable badge asset discovered from the source repository."""

    id: str
    name: str
    path: str
    raw_url: str
    extension: str
    local_path: str | None = None


def _humanize(path: str) -> str:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return stem.replace("_", " ").replace("-", " ").title()


def _badge_from_path(path: str) -> Badge:
    extension = "." + path.rsplit(".", 1)[-1].lower()
    return Badge(
        id=path,
        name=_humanize(path),
        path=path,
        raw_url=f"{RAW_BASE_URL}/{path}",
        extension=extension,
    )


def _is_badge_asset(path: str) -> bool:
    normalized = path.lower()
    return normalized.endswith(IMAGE_EXTENSIONS) and not normalized.startswith(".")


def _sort_badges(badges: Iterable[Badge]) -> list[Badge]:
    return sorted(badges, key=lambda badge: (badge.name.lower(), badge.path.lower()))


def _fallback_badges() -> list[Badge]:
    return [
        Badge(
            id="demo-badge.svg",
            name="Demo Badge",
            path="demo-badge.svg",
            raw_url="/static/demo-badge.svg",
            extension=".svg",
        )
    ]


def _cache_bucket() -> int:
    return int(time() // BADGE_CACHE_TTL_SECONDS)


@lru_cache(maxsize=2)
def _list_badges_cached(_bucket: int) -> list[Badge]:
    """Return image badges from the upstream repository, with a safe fallback."""

    try:
        import requests

        response = requests.get(GITHUB_TREE_URL, timeout=12)
        response.raise_for_status()
        tree = response.json().get("tree", [])
        badges = [
            _badge_from_path(item["path"])
            for item in tree
            if item.get("type") == "blob" and _is_badge_asset(item.get("path", ""))
        ]
        if badges:
            return _sort_badges(badges)
    except Exception:
        pass

    return _fallback_badges()


def list_badges() -> list[Badge]:
    """Return upstream image badges, refreshing automatically on a short TTL."""

    return _list_badges_cached(_cache_bucket())


list_badges.cache_clear = _list_badges_cached.cache_clear


def refresh_badges() -> None:
    """Clear the in-process GitHub badge cache so the next request fetches HEAD again."""

    _list_badges_cached.cache_clear()


def get_badges_by_id(ids: Iterable[str], upload_folder: str | None = None) -> list[Badge]:
    """Resolve selected badge ids while preserving the user's selection order."""

    available = {badge.id: badge for badge in list_badges()}
    if upload_folder:
        from .uploads import list_uploaded_badges

        available.update({badge.id: badge for badge in list_uploaded_badges(upload_folder)})
    return [available[badge_id] for badge_id in ids if badge_id in available]
