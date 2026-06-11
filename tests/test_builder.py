"""Smoke tests for the Mintlify builder skeleton."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="skeleton")
def test_builds_index_mdx(app, status, warning) -> None:
    app.build()
    out = Path(app.outdir)
    index = out / "index.mdx"
    assert index.exists(), "index.mdx should be produced"
    text = index.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "frontmatter should lead the file"
    assert "title: Welcome" in text
    assert "This is a paragraph of text." in text
    assert "A second paragraph follows the first." in text


@pytest.mark.sphinx("mintlify", testroot="skeleton")
def test_writes_docs_json(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    assert data["name"] == "Skeleton"
    assert data["theme"] == "mint"
    assert "navigation" in data


@pytest.mark.sphinx("mintlify", testroot="skeleton")
def test_page_write_failure_aborts_build(app, monkeypatch) -> None:
    """A failure writing the page output must surface as an exception.

    Silently logging an OSError and continuing produces a "successful"
    build with a missing or partial page in the output tree, which is
    the worst possible failure mode for a docs publisher.
    """
    import builtins

    real_open = builtins.open

    def boom(file, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(file).endswith(".mdx"):
            raise OSError("disk full")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", boom)
    with pytest.raises(OSError, match="disk full"):
        app.build()
