"""Tests for raw HTML asset externalization (inline SVG and base64 URIs)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="raw-assets")
def test_standalone_svg_externalized(app) -> None:
    app.build()
    out = Path(app.outdir)
    text = (out / "index.mdx").read_text("utf-8")
    assert "<svg " not in text, "inline SVG should be replaced"
    assert "xml:space" not in text
    # Default URL mode is relative — the externalised SVG sits at
    # ``images/raw-...`` relative to the current page.
    assert 'src="./images/raw-' in text
    svgs = list((out / "images").glob("raw-*.svg"))
    assert len(svgs) == 1
    content = svgs[0].read_text("utf-8")
    assert 'fill="red"' in content


@pytest.mark.sphinx("mintlify", testroot="raw-assets")
def test_base64_png_externalized(app) -> None:
    app.build()
    out = Path(app.outdir)
    text = (out / "index.mdx").read_text("utf-8")
    assert "data:image/png" not in text, "base64 data URI should be replaced"
    pngs = list((out / "images").glob("raw-*.png"))
    assert len(pngs) == 1
    assert pngs[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.sphinx("mintlify", testroot="raw-assets")
def test_plain_html_passes_through(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<div class="custom-marker">just text</div>' in text


@pytest.mark.sphinx(
    "mintlify",
    testroot="raw-assets",
    confoverrides={"mintlify_externalize_assets": False},
)
def test_disabling_keeps_inline(app) -> None:
    app.build()
    out = Path(app.outdir)
    text = (out / "index.mdx").read_text("utf-8")
    assert "<svg " in text
    assert "data:image/png" in text
    assert not (out / "images").exists() or not list((out / "images").glob("raw-*"))
