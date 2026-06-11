"""Tests for Stage 6 — math, raw, substitution, glossary, comments."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_inline_math(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "$a^2 + b^2 = c^2$" in text


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_block_math(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "$$" in text
    assert "E = mc^2" in text


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_raw_html_kept(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<span class="custom">raw html</span>' in text


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_raw_latex_skipped(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "skip me" not in text or "\\section" not in text


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_substitution(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "My Project" in text


@pytest.mark.sphinx("mintlify", testroot="misc")
def test_glossary_definition_list(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<dt>builder</dt>" in text
    assert "A Sphinx object" in text
    assert "<dt>directive</dt>" in text
