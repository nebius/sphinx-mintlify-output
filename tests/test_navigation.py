"""Tests for Stage 7 — docs.json navigation generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="navigation")
def test_navigation_groups(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    assert "groups" in data["navigation"]
    captions = [g["group"] for g in data["navigation"]["groups"]]
    assert "Get started" in captions
    assert "Reference" in captions


@pytest.mark.sphinx("mintlify", testroot="navigation")
def test_navigation_pages_in_group(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    groups = {g["group"]: g["pages"] for g in data["navigation"]["groups"]}
    assert "tutorial/quickstart" in groups["Get started"]
    assert "tutorial/install" in groups["Get started"]


@pytest.mark.sphinx("mintlify", testroot="navigation")
def test_nested_toctree_yields_nested_group(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    groups = {g["group"]: g["pages"] for g in data["navigation"]["groups"]}
    ref_pages = groups["Reference"]
    nested = next((p for p in ref_pages if isinstance(p, dict)), None)
    assert nested is not None
    assert "reference/index" in nested["pages"]
    assert "reference/commands" in nested["pages"]
    assert "reference/options" in nested["pages"]


@pytest.mark.sphinx("mintlify", testroot="navigation")
def test_user_overrides_merge(app) -> None:
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    assert data["name"] == "Nav Docs"
    assert data["colors"]["primary"] == "#0d9373"
    assert data["theme"] == "mint"


@pytest.mark.sphinx("mintlify", testroot="navigation-mixed")
def test_top_level_mixed_pages_and_groups_preserved(app) -> None:
    """Captioned + uncaptioned top-level toctrees must not drop entries."""
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    nav = data["navigation"]
    assert "pages" in nav, "mixed toctree should fall back to top-level pages"
    items = nav["pages"]
    bare = [p for p in items if isinstance(p, str)]
    groups = {g["group"]: g for g in items if isinstance(g, dict)}
    assert "intro" in bare
    assert "about" in bare
    assert "Guides" in groups
    assert "guide_one" in groups["Guides"]["pages"]
    assert "guide_two" in groups["Guides"]["pages"]
    nested = next(
        (p for p in items if isinstance(p, dict) and p.get("group") != "Guides"),
        None,
    )
    assert nested is not None, "sub/index nested group must be present"


@pytest.mark.sphinx("mintlify", testroot="navigation-mixed")
def test_doc_with_sub_groups_and_sub_pages_preserves_both(app) -> None:
    """page_for_doc must keep sub_groups when sub_pages also exist."""
    app.build()
    data = json.loads((Path(app.outdir) / "docs.json").read_text("utf-8"))
    items = data["navigation"]["pages"]
    sub_entry = next(
        (
            p
            for p in items
            if isinstance(p, dict)
            and any(
                isinstance(child, str) and child == "sub/index"
                for child in p.get("pages", [])
            )
        ),
        None,
    )
    assert sub_entry is not None, "sub/index page entry missing"
    sub_pages = sub_entry["pages"]
    assert "sub/index" in sub_pages
    assert "sub/alpha" in sub_pages, "uncaptioned sub_pages must be preserved"
    sub_groups = [p for p in sub_pages if isinstance(p, dict)]
    captions = {g["group"] for g in sub_groups}
    assert "Sub Group" in captions, "captioned sub_groups must be preserved"
