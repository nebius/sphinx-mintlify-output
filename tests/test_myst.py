from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="myst")
def test_myst_frontmatter(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "description: A markdown description" in text
    assert "icon: star-shooting" in text


@pytest.mark.sphinx("mintlify", testroot="myst")
def test_rst_frontmatter(app) -> None:
    app.build()
    text = (Path(app.outdir) / "test.mdx").read_text("utf-8")
    assert "title: Clients" in text
    assert "icon: space-station-moon-construction" in text


@pytest.mark.sphinx("mintlify", testroot="myst")
def test_body_title_used_for_doc_links(app) -> None:
    """Body ``# Title`` must drive ``{doc}`` link text, not the first H2."""
    app.build(["linker", "frontmatter-title"])
    text = (Path(app.outdir) / "linker.mdx").read_text("utf-8")
    assert "[Frontmatter Page Title](./frontmatter-title)" in text
    assert "[First Section](./frontmatter-title)" not in text


@pytest.mark.sphinx("mintlify", testroot="myst")
def test_body_title_captured_in_frontmatter(app) -> None:
    app.build(["frontmatter-title"])
    text = (Path(app.outdir) / "frontmatter-title.mdx").read_text("utf-8")
    assert "title: Frontmatter Page Title" in text
    assert "icon: book" in text
    assert "# Frontmatter Page Title" not in text
    assert "## First Section" in text
