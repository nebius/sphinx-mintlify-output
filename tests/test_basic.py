"""Tests for Stage 1 — base markdown rendering (rst + MyST)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="basic")
def test_rst_page_renders(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")

    assert text.startswith("---\n")
    assert "title: Basic Document" in text

    assert "*emphasis*" in text
    assert "**strong**" in text
    assert "`literal`" in text
    assert "<sub>2</sub>" in text
    assert "<sup>2</sup>" in text

    assert "## Subsection" in text

    assert "- one" in text
    assert "- two" in text
    assert "  - nested A" in text
    assert "  - nested B" in text
    assert "- three" in text

    assert "1. first" in text
    assert "2. second" in text
    assert "3. third" in text

    assert "> Quoted text spanning" in text
    assert "---" in text

    assert "```python" in text
    assert "def hello():" in text


@pytest.mark.sphinx("mintlify", testroot="basic")
def test_myst_page_renders(app) -> None:
    app.build()
    text = (Path(app.outdir) / "myst.mdx").read_text("utf-8")

    assert "title: MyST page" in text
    assert "*italic*" in text
    assert "**bold**" in text
    assert "`inline code`" in text
    assert "- alpha" in text
    assert "- beta" in text
    assert "- gamma" in text
    assert "```python" in text
    assert 'print("hi")' in text
