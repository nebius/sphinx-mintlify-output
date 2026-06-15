"""End-to-end tests for the ``mintlify_base_path`` config knob.

When set, every generated absolute URL — ``:doc:`` cross-refs, image
``src``, toctree card ``href``, externalised raw-asset paths — is
rooted at the prefix. The companion ``test_relative_urls.py`` covers
the default mode.
"""

from __future__ import annotations

from pathlib import Path

import pytest


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


@pytest.mark.sphinx(
    "mintlify",
    testroot="autodoc",
    confoverrides={"mintlify_base_path": "/sandboxes/sdk"},
)
def test_autodoc_type_link_prefixed(app) -> None:
    app.build()
    index = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    settings = (Path(app.outdir) / "nested/settings.mdx").read_text("utf-8")
    assert "(/sandboxes/sdk/nested/config#example.nested.config.Config)" in index
    assert "(/sandboxes/sdk/nested/settings#example.nested.settings.Settings)" in index
    assert 'href="/sandboxes/sdk/nested/settings"' in index
    assert "(/sandboxes/sdk/nested/config#example.nested.config.Config)" in settings
