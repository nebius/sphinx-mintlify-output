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
