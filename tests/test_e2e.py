"""End-to-end test: full Mintlify export verifies the integrated pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_all_pages_emitted(app) -> None:
    app.build()
    out = Path(app.outdir)
    assert (out / "index.mdx").exists()
    assert (out / "intro.mdx").exists()
    assert (out / "advanced.mdx").exists()


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_docs_json_complete(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    assert data["name"] == "E2E Docs"
    assert data["logo"]["light"] == "static/favicon.ico"
    groups = data["navigation"]["groups"]
    captions = [g["group"] for g in groups]
    assert "Guides" in captions


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_static_copied_css_skipped(app) -> None:
    app.build()
    out = Path(app.outdir)
    assert (out / "static" / "favicon.ico").exists()
    assert not (out / "static" / "custom.css").exists()


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_global_frontmatter_applied(app) -> None:
    app.build()
    text = (Path(app.outdir) / "advanced.mdx").read_text("utf-8")
    assert "icon: book" in text
    assert "title: Advanced" in text


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_cross_doc_links_relative(app) -> None:
    """Top-level pages link to each other via plain slugs (no leading /)."""
    app.build()
    intro = (Path(app.outdir) / "intro.mdx").read_text("utf-8")
    assert "](index)" in intro
    index = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "](intro)" in index
    # No absolute fall-through.
    assert "](/intro)" not in index
    assert "](/index)" not in intro
