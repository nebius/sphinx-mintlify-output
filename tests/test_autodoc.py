"""Tests for Stage 5 — autodoc desc.* and field_list rendering."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_class_signature(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `class Greeter`" in text
    assert "class example.Greeter(name, polite)" in text


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_method_signature(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "#### `greet()`" in text
    assert "def greet(target) -> str" in text


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_function_signature_and_anchor(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `add()`" in text
    assert "def example.add(a, b)" in text
    assert '<a id="example.add"></a>' in text


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_param_field_rendered(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ParamField path="name"' in text
    assert "The display name of the greeter." in text
    assert "</ParamField>" in text


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_response_field(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ResponseField name="returns">' in text
    assert "A greeting string." in text


@pytest.mark.sphinx("mintlify", testroot="autodoc")
def test_raises_field(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ResponseField name="raises">' in text
    assert "ValueError" in text
