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


@pytest.fixture
def autodoc_app_without_module_names(
    make_app, sphinx_test_tempdir, rootdir
) -> SphinxTestApp:
    test_root_path = rootdir / "test-autodoc"
    srcdir = sphinx_test_tempdir / "autodoc-without-module-names"
    import shutil

    shutil.copytree(test_root_path, srcdir, dirs_exist_ok=True)
    app = make_app(
        buildername="mintlify",
        srcdir=srcdir / "docs",
        confoverrides={"add_module_names": False},
    )
    yield app


def test_class_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `class Greeter`" in text
    assert (
        "```python\n"
        "from example import Greeter\n\n"
        "class Greeter(name, polite):\n"
        "    category: Category\n"
        "    product: Product\n"
        "    schema_version: ClassVar[str]\n"
        "```" in text
    )
    assert "class example.Greeter(name, polite)" not in text


def test_class_without_attributes_has_ellipsis(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "catalog/product.mdx").read_text("utf-8")
    assert (
        "```python\n"
        "from example.catalog.product import Product\n\n"
        "class Product():\n"
        "    ...\n"
        "```" in text
    )


def test_method_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "#### `greet()`" in text
    assert "def greet(target) -> str" in text


def test_exception_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `exception ExampleError`" in text
    assert (
        "```python\n"
        "from example import ExampleError\n\n"
        "class ExampleError(message):\n"
        "    ...\n"
        "```" in text
    )
    assert "exception example.ExampleError(message)" not in text


def test_function_signature_and_anchor(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "## `add()`" in text
    assert "```python\nfrom example import add\n\n\ndef add(a, b) -> int\n```" in text
    assert "def example.add(a, b)" not in text
    assert '<a id="example.add"></a>' in text


def test_nested_module_function_signature(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert (
        "```python\n"
        "from example.operations import parse_check_image_file\n\n\n"
        "def parse_check_image_file(response) -> bool\n"
        "```" in text
    )
    assert "def example.operations.parse_check_image_file(response)" not in text


def test_function_import_when_module_names_hidden(
    autodoc_app_without_module_names,
) -> None:
    autodoc_app_without_module_names.build()
    text = (Path(autodoc_app_without_module_names.outdir) / "index.mdx").read_text(
        "utf-8"
    )
    assert (
        "```python\n"
        "from example.operations import parse_check_image_file\n\n\n"
        "def parse_check_image_file(response) -> bool\n"
        "```" in text
    )
    assert (
        "```python\n"
        "from example import Greeter\n\n"
        "class Greeter(name, polite):\n"
        "    category: Category\n"
        "    product: Product\n"
        "    schema_version: ClassVar[str]\n"
        "```" in text
    )
    assert (
        "```python\n"
        "from example import ExampleError\n\n"
        "class ExampleError(message):\n"
        "    ...\n"
        "```" in text
    )
    assert '<ResponseField name="schema_version" type="ClassVar[str]" />' in text


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


def test_hidden_toctree_not_rendered(autodoc_app) -> None:
    autodoc_app.build()
    text = (Path(autodoc_app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Columns" not in text
    assert "<Card" not in text
