"""Default URL mode — relative links, Sphinx-HTML-style.

When ``mintlify_base_path`` is unset, generated URLs are computed
relative to the current document so the build is portable across
deployment prefixes. These tests verify both the same-level case and
the nested case (``guide/setup`` linking up to ``intro``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


@pytest.fixture
def autodoc_app_relative(make_app, sphinx_test_tempdir, rootdir) -> SphinxTestApp:
    test_root_path = rootdir / "test-autodoc"
    srcdir = sphinx_test_tempdir / "autodoc"
    import shutil

    shutil.copytree(test_root_path, srcdir, dirs_exist_ok=True)
    app = make_app(buildername="mintlify", srcdir=srcdir / "docs")
    yield app


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_same_level_doc_link_no_dotdot(app) -> None:
    """Top-level → top-level link uses a plain slug, no leading slash."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(./intro)" in text
    assert "(/intro)" not in text


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_same_level_image_uses_relative_path(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(./images/dot.png)" in text
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
    assert 'href="./intro"' in text
    assert 'href="./guide/setup"' in text
    assert 'href="/intro"' not in text


def test_autodoc_type_link_relative(autodoc_app_relative) -> None:
    autodoc_app_relative.build()
    index = (Path(autodoc_app_relative.outdir) / "index.mdx").read_text("utf-8")
    category = (Path(autodoc_app_relative.outdir) / "catalog/category.mdx").read_text(
        "utf-8"
    )
    cart = (Path(autodoc_app_relative.outdir) / "orders/cart.mdx").read_text("utf-8")
    assert "(./catalog/product#example.catalog.product.Product)" in index
    assert "(./catalog/category#example.catalog.category.Category)" in index
    assert "(./product#example.catalog.product.Product)" in category
    assert "(../catalog/product#example.catalog.product.Product)" in cart
