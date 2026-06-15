"""Settings types for autodoc tests."""

from __future__ import annotations

from example.nested.config import Config


class Settings:
    """Runtime settings."""

    config: Config
    """Parent configuration."""
