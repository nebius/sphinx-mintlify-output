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
def test_anchor_target(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<a id="anchor-target"></a>' in text
    assert "](#anchor-target)" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_image_sized(app) -> None:
    app.build()
    text = (Path(app.outdir) / "second.mdx").read_text("utf-8")
    assert '<img src="./images/logo.png"' in text
    assert 'width="64px"' in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_figure_wraps_in_frame(app) -> None:
    app.build()
    text = (Path(app.outdir) / "second.mdx").read_text("utf-8")
    assert '<Frame caption="A diagram caption.">' in text
    assert "</Frame>" in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_linked_badge_image_stays_inline(app) -> None:
    """Image link text must not get block-level blank lines inside the wrapper."""
    app.build()
    text = (Path(app.outdir) / "badges.mdx").read_text("utf-8")
    assert "[![Logo](./images/logo.png)](https://example.com)" in text
    assert "](./images/logo.png)\n\n](" not in text


@pytest.mark.sphinx("mintlify", testroot="links")
def test_images_copied(app) -> None:
    app.build()
    out = Path(app.outdir)
    assert (out / "images" / "logo.png").exists()
    assert (out / "images" / "diagram.png").exists()
