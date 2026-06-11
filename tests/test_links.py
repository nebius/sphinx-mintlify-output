"""Tests for Stage 2 — references, images, figures, anchors."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="links")
def test_external_link(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "[Mintlify](https://mintlify.com)" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_internal_doc_xref(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "](/second)" in text, text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_anchor_target(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<a id="anchor-target"></a>' in text
    assert "](#anchor-target)" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_image_default(app) -> None:
    app.build()
    text = (Path(app.outdir) / "second.mdx").read_text("utf-8")
    assert "![Logo](/images/logo.png)" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_image_sized(app) -> None:
    app.build()
    text = (Path(app.outdir) / "second.mdx").read_text("utf-8")
    assert '<img src="/images/logo.png"' in text
    assert 'width="64px"' in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_figure_wraps_in_frame(app) -> None:
    app.build()
    text = (Path(app.outdir) / "second.mdx").read_text("utf-8")
    assert '<Frame caption="A diagram caption.">' in text
    assert "</Frame>" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_images_copied(app) -> None:
    app.build()
    out = Path(app.outdir)
    assert (out / "images" / "logo.png").exists()
    assert (out / "images" / "diagram.png").exists()


@pytest.mark.sphinx("mintlify", testroot="links")
def test_nested_doc_relative_image(app) -> None:
    app.build()
    text = (Path(app.outdir) / "sub" / "nested.mdx").read_text("utf-8")
    assert "![Logo](/images/logo.png)" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_nested_doc_xref_relative(app) -> None:
    app.build()
    text = (Path(app.outdir) / "sub" / "nested.mdx").read_text("utf-8")
    assert "](/second)" in text
    assert "](/index)" in text
