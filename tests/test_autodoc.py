"""Tests for Stage 5 — autodoc desc.* and field_list rendering."""

from __future__ import annotations

from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


@pytest.fixture
def autodoc_app(make_app, sphinx_test_tempdir, rootdir) -> SphinxTestApp:
    test_root_path = rootdir / "test-autodoc"
    srcdir = sphinx_test_tempdir / "autodoc"
    import shutil

    shutil.copytree(test_root_path, srcdir, dirs_exist_ok=True)
    app = make_app(buildername="mintlify", srcdir=srcdir / "docs")
    yield app


def test_class_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `class Greeter`" in text
    assert "class example.Greeter(name, polite)" in text


def test_method_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "#### `greet()`" in text
    assert "def greet(target) -> str" in text


def test_function_signature_and_anchor(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `add()`" in text
    assert "def example.add(a, b)" in text
    assert '<a id="example.add"></a>' in text


def test_param_field_rendered(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ParamField path="name"' in text
    assert "The display name of the greeter." in text
    assert "</ParamField>" in text


def test_response_field(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ResponseField name="returns">' in text
    assert "A greeting string." in text


def test_raises_field(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert '<ResponseField name="raises">' in text
    assert "ValueError" in text
