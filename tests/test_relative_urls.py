"""Default URL mode — relative links, Sphinx-HTML-style.

When ``mintlify_base_path`` is unset, generated URLs are computed
relative to the current document so the build is portable across
deployment prefixes. These tests verify both the same-level case and
the nested case (``guide/setup`` linking up to ``intro``).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_same_level_doc_link_no_dotdot(app) -> None:
    """Top-level → top-level link uses a plain slug, no leading slash."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(intro)" in text
    assert "(/intro)" not in text


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_same_level_image_uses_relative_path(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(images/dot.png)" in text
    assert "(/images/dot.png)" not in text


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_nested_doc_link_uses_dotdot(app) -> None:
    """A nested page linking to a sibling at root climbs via ``..``."""
    app.build()
    text = (Path(app.outdir) / "guide" / "setup.mdx").read_text("utf-8")
    assert "(../index)" in text
    assert "(../intro)" in text


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_nested_image_uses_dotdot(app) -> None:
    app.build()
    text = (Path(app.outdir) / "guide" / "setup.mdx").read_text("utf-8")
    assert "(../images/dot.png)" in text


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_toctree_card_href_relative(app) -> None:
    """Toctree cards at the top level reference siblings without a leading /."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert 'href="intro"' in text
    assert 'href="guide/setup"' in text
    assert 'href="/intro"' not in text
