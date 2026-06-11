"""Tests for the wider Mintlify component mapping."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_check_via_class(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<Check title="Success!">' in text
    assert "The check passed." in text
    assert "</Check>" in text


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_steps_via_class(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Steps>" in text
    assert '<Step title="Build the package.">' in text
    assert '<Step title="Push the image.">' in text
    assert '<Step title="Apply the manifest.">' in text
    assert "</Steps>" in text


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_callout_via_class(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<Callout title="Hot tip">' in text
    assert "Custom callout content." in text


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_abbreviation_to_tooltip(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<Tooltip tip="Application Programming Interface">API</Tooltip>' in text


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_grid_as_columns_with_cols(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Columns cols={3}>" in text
    assert "</Columns>" in text


@pytest.mark.sphinx("mintlify", testroot="mintlify-components")
def test_codegroup_for_all_code_tabs(app) -> None:
    app.build()
    text = (Path(app.outdir) / "codes.mdx").read_text("utf-8")
    assert "<CodeGroup>" in text
    assert "```python python" in text
    assert 'print("hi")' in text
    assert "```javascript javascript" in text
    assert 'console.log("hi");' in text
    assert "</CodeGroup>" in text
