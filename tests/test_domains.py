"""Domain-aware signature rendering (design/tasks.md).

Non-Python domains must never render as Python declarations: no ``def``,
no ``@decorator`` prefixes, no python-fence — each domain gets its own
:class:`~sphinx_mintlify_output.autodoc.SignatureStyle`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp

from sphinx_mintlify_output.autodoc import (
    FALLBACK_STYLE,
    SIGNATURE_STYLES,
    decorate_signature,
    signature_style,
)


@pytest.fixture
def domains_app(make_app, sphinx_test_tempdir, rootdir) -> SphinxTestApp:
    test_root_path = rootdir / "test-domains"
    srcdir = sphinx_test_tempdir / "domains"
    shutil.copytree(test_root_path, srcdir, dirs_exist_ok=True)
    app = make_app(buildername="mintlify", srcdir=srcdir)
    yield app


@pytest.fixture
def domains_text(domains_app) -> str:
    domains_app.build()
    return (Path(domains_app.outdir) / "index.mdx").read_text("utf-8")


def test_js_function_uses_ts_fence(domains_text: str) -> None:
    assert "```ts\nfunction fetchData(url, options): Promise<Response>\n```" in (
        domains_text
    )


def test_js_method_has_no_keyword(domains_text: str) -> None:
    assert "```ts\nContreeClient.uploadFile(content): Promise<FileResponse>\n```" in (
        domains_text
    )


def test_js_class_signature(domains_text: str) -> None:
    assert "## `class ContreeClient`" in domains_text
    assert "```ts\nclass ContreeClient(options)\n```" in domains_text


def test_js_attribute_renders_as_response_field(domains_text: str) -> None:
    assert '<ResponseField name="baseUrl">' in domains_text


def test_c_function_keeps_raw_signature(domains_text: str) -> None:
    assert "```c\nint add(int a, int b)\n```" in domains_text


def test_unknown_domain_falls_back_to_text_fence(domains_text: str) -> None:
    assert "```text\nfrobnicate(width)\n```" in domains_text


def test_no_python_leaks_into_foreign_domains(domains_text: str) -> None:
    assert "```python" not in domains_text
    assert "def " not in domains_text


def test_js_types_not_linked_via_python_domain(domains_text: str) -> None:
    assert 'type="Promise&lt;Response&gt;"' in domains_text
    assert "[`Promise" not in domains_text


NON_PY_CALLABLE_TYPES = ("function", "method", "staticmethod", "classmethod")


@pytest.mark.parametrize(
    "domain",
    [*sorted(d for d in SIGNATURE_STYLES if d != "py"), "unknown"],
)
@pytest.mark.parametrize("desctype", [*NON_PY_CALLABLE_TYPES, "class"])
def test_invariant_no_def_outside_py_and_rb(domain: str, desctype: str) -> None:
    """No domain except py/rb ever produces ``def``; returns follow the style."""
    style = signature_style(domain)
    sig = decorate_signature("obj.item(a, b)", desctype, "SomeType", style)
    if domain != "rb":
        assert "def " not in sig, (domain, desctype, sig)
    if not style.returns:
        assert "SomeType" not in sig, (domain, desctype, sig)
    assert "@classmethod" not in sig and "@staticmethod" not in sig


def test_signature_style_lookup() -> None:
    assert signature_style("py").fence == "python"
    assert signature_style("") is signature_style("py")
    assert signature_style("nope") is FALLBACK_STYLE


def test_decorate_async_js_function() -> None:
    js = SIGNATURE_STYLES["js"]
    assert decorate_signature("async fetchData(url)", "function", "", js) == (
        "async function fetchData(url)"
    )
    assert decorate_signature("async obj.up(a)", "method", "", js) == "async obj.up(a)"


def test_decorate_py_unchanged() -> None:
    assert decorate_signature("greet(target)", "method", "str") == (
        "def greet(target) -> str"
    )
    assert decorate_signature("async run()", "function") == "async def run()"
