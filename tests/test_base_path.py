"""End-to-end tests for the ``mintlify_base_path`` config knob.

When set, every generated absolute URL — ``:doc:`` cross-refs, image
``src``, toctree card ``href``, externalised raw-asset paths — is
rooted at the prefix. The companion ``test_relative_urls.py`` covers
the default mode.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


@pytest.fixture
def autodoc_app_prefixed(make_app, sphinx_test_tempdir, rootdir) -> SphinxTestApp:
    test_root_path = rootdir / "test-autodoc"
    srcdir = sphinx_test_tempdir / "autodoc"
    import shutil

    shutil.copytree(test_root_path, srcdir, dirs_exist_ok=True)
    app = make_app(
        buildername="mintlify",
        srcdir=srcdir / "docs",
        confoverrides={"mintlify_base_path": "/sandboxes/sdk"},
    )
    yield app


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_cross_doc_link_prefixed(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(/sandboxes/sdk/intro)" in text
    # No bare /intro link, no relative variant slipped through.
    assert "](/intro)" not in text
    assert "](intro)" not in text


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_image_target_prefixed(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "(/sandboxes/sdk/images/dot.png)" in text


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_toctree_card_href_prefixed(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert 'href="/sandboxes/sdk/intro"' in text


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_externalized_inline_svg_prefixed(app) -> None:
    app.build()
    text = (Path(app.outdir) / "intro.mdx").read_text("utf-8")
    assert "/sandboxes/sdk/images/raw-" in text
    # No un-prefixed asset path leaked through.
    assert 'src="/images/raw-' not in text
    assert 'src="images/raw-' not in text


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_back_link_from_subpage_prefixed(app) -> None:
    app.build()
    text = (Path(app.outdir) / "intro.mdx").read_text("utf-8")
    assert "(/sandboxes/sdk/index)" in text


def test_autodoc_type_link_prefixed(autodoc_app_prefixed) -> None:
    autodoc_app_prefixed.build()
    index = (Path(autodoc_app_prefixed.outdir) / "index.mdx").read_text("utf-8")
    category = (Path(autodoc_app_prefixed.outdir) / "catalog/category.mdx").read_text(
        "utf-8"
    )
    cart = (Path(autodoc_app_prefixed.outdir) / "orders/cart.mdx").read_text("utf-8")
    assert "(/sandboxes/sdk/catalog/product#example.catalog.product.Product)" in index
    assert (
        "(/sandboxes/sdk/catalog/category#example.catalog.category.Category)" in index
    )
    assert (
        "(/sandboxes/sdk/catalog/product#example.catalog.product.Product)" in category
    )
    assert "(/sandboxes/sdk/catalog/product#example.catalog.product.Product)" in cart
