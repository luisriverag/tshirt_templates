"""Upload helpers for user-provided badge artwork."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .badges import Badge, IMAGE_EXTENSIONS

UPLOAD_BADGE_PREFIX = "upload:"
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def is_allowed_upload(filename: str) -> bool:
    """Return whether a filename has a supported image extension."""

    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def _safe_filename(filename: str) -> str:
    stem = Path(filename).stem.replace(" ", "-") or "badge"
    suffix = Path(filename).suffix.lower()
    safe_stem = "".join(character for character in stem if character.isalnum() or character in {"-", "_"})
    return f"{uuid4().hex}-{safe_stem or 'badge'}{suffix}"


def _humanize_upload(filename: str) -> str:
    stem = Path(filename).stem
    if "-" in stem:
        possible_uuid, original = stem.split("-", 1)
        if len(possible_uuid) == 32:
            stem = original
    return stem.replace("_", " ").replace("-", " ").title() or "Uploaded Badge"


def upload_badge_from_filename(filename: str, upload_folder: str | Path) -> Badge:
    """Build a Badge for a previously saved upload filename."""

    upload_path = Path(upload_folder) / filename
    return Badge(
        id=f"{UPLOAD_BADGE_PREFIX}{filename}",
        name=_humanize_upload(filename),
        path=f"uploaded/{filename}",
        raw_url=f"/uploads/{filename}",
        extension=upload_path.suffix.lower(),
        local_path=str(upload_path),
    )


def list_uploaded_badges(upload_folder: str | Path) -> list[Badge]:
    """Return saved user uploads as selectable badge assets."""

    folder = Path(upload_folder)
    if not folder.exists():
        return []

    return sorted(
        [upload_badge_from_filename(path.name, folder) for path in folder.iterdir() if path.is_file() and is_allowed_upload(path.name)],
        key=lambda badge: (badge.name.lower(), badge.path.lower()),
    )


def save_uploaded_badges(files, upload_folder: str | Path) -> list[Badge]:
    """Persist uploaded badge files and return their Badge records."""

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    saved: list[Badge] = []

    for upload in files:
        original_name = getattr(upload, "filename", "") or ""
        if not original_name or not is_allowed_upload(original_name):
            continue

        upload.seek(0, 2)
        size = upload.tell()
        upload.seek(0)
        if size <= 0 or size > MAX_UPLOAD_BYTES:
            continue

        filename = _safe_filename(original_name)
        destination = folder / filename
        upload.save(destination)
        saved.append(upload_badge_from_filename(filename, folder))

    return saved
