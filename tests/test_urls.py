"""Direct unit tests for :mod:`urls`.

These run without Sphinx so a failure points at the helper, not the
plumbing. :func:`url_for` reads a :class:`contextvars.ContextVar`, so
each test that touches absolute mode resets it via the token API to
avoid state bleeding across tests.
"""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from sphinx_mintlify_output import urls
from sphinx_mintlify_output.urls import url_for


@pytest.fixture(autouse=True)
def reset_base_path() -> None:
    """Ensure no state leaks between tests."""
    token = urls.base_path.set(None)
    yield
    urls.base_path.reset(token)


# ---------------------------------------------------------------------------
# Relative mode (no base_path set)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "from_doc,target,expected",
    [
        # Same level — neighbour pages
        ("index", "intro", "./intro"),
        ("index", "guide/install", "./guide/install"),
        # Nested page linking to a sibling at root
        ("guide/setup", "intro", "../intro"),
        ("guide/setup", "guide/install", "./install"),
        # Deeper nesting
        ("guide/sub/page", "intro", "../../intro"),
        ("guide/sub/page", "guide/install", "../install"),
        # Image-style targets follow the same rules
        ("index", "images/logo.png", "./images/logo.png"),
        ("guide/setup", "images/logo.png", "../images/logo.png"),
        # Leading slashes on target are stripped — caller-friendly
        ("index", "/intro", "./intro"),
        ("guide/setup", "/intro", "../intro"),
    ],
)
def test_url_for_relative_mode(from_doc: str, target: str, expected: str) -> None:
    assert url_for(from_doc, target) == expected


# ---------------------------------------------------------------------------
# Absolute mode (base_path contextvar set)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base,from_doc,target,expected",
    [
        # from_doc is irrelevant in absolute mode — only the prefix + target
        # matter.
        ("/sandboxes/sdk", "index", "intro", "/sandboxes/sdk/intro"),
        ("/sandboxes/sdk", "guide/setup", "intro", "/sandboxes/sdk/intro"),
        (
            "/sandboxes/sdk",
            "index",
            "images/logo.png",
            "/sandboxes/sdk/images/logo.png",
        ),
        # Root prefix '/' still produces absolute paths
        ("/", "index", "intro", "/intro"),
        ("/", "guide/setup", "intro", "/intro"),
        # Leading slash on target is tolerated
        ("/sandboxes/sdk", "index", "/intro", "/sandboxes/sdk/intro"),
    ],
)
def test_url_for_absolute_mode(
    base: str, from_doc: str, target: str, expected: str
) -> None:
    token = urls.base_path.set(PurePosixPath(base))
    try:
        assert url_for(from_doc, target) == expected
    finally:
        urls.base_path.reset(token)


def test_contextvar_default_is_none() -> None:
    """A freshly-imported module starts in relative mode."""
    assert urls.base_path.get() is None


def test_contextvar_set_reset_restores_relative_mode() -> None:
    """``reset`` returns the helper to its previous (None) state."""
    token = urls.base_path.set(PurePosixPath("/x"))
    assert url_for("index", "intro") == "/x/intro"
    urls.base_path.reset(token)
    assert url_for("index", "intro") == "./intro"
