"""Footnote and citation rendering as Markdown ``[^id]`` references."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="footnotes")
def test_footnote_reference_uses_caret_id(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "[^1]" in text
    assert "[^2]" in text


@pytest.mark.sphinx("mintlify", testroot="footnotes")
def test_footnote_definition_with_continuation(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "[^1]: This is the first footnote, with **emphasis** inside." in text
    assert "[^2]: Auto-numbered footnote body." in text


@pytest.mark.sphinx("mintlify", testroot="footnotes")
def test_citation_reference_renders_as_footnote_marker(app) -> None:
    """A resolved citation reference must NOT become a regular [text](#id) link."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # Sphinx normalises citation refids to lowercase; markers on both
    # sides must match the same id.
    assert "[^smith2020]" in text
    assert "[^smith2020]: Smith, J. (2020). *An important paper.*" in text
    # Should not fall back to the regular reference rendering.
    assert "[[Smith2020]](#smith2020)" not in text
