"""Flask app package for t-shirt sublimation template generation."""


def create_app():
    """Create the Flask application without importing Flask at package import time."""

    from .app import create_app as _create_app

    return _create_app()


__all__ = ["create_app"]
