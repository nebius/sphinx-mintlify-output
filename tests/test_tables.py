"""Tests for Stage 3 — tables, definition lists, fields, options."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="tables")
def test_simple_table_gfm(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "| Key | Value |" in text
    assert "|---|---|" in text
    assert "| one | 1 |" in text
    assert "| two | 2 |" in text


@pytest.mark.sphinx("mintlify", testroot="tables")
def test_complex_table_html(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<table>" in text
    assert 'colspan="2"' in text


@pytest.mark.sphinx("mintlify", testroot="tables")
def test_definition_list(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<dl>" in text
    assert "<dt>term one</dt>" in text
    assert "A definition for term one." in text
    assert "<em>adjective</em>" in text


@pytest.mark.sphinx("mintlify", testroot="tables")
def test_field_list(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "- **author** — Alice" in text
    assert "- **date** — today" in text


@pytest.mark.sphinx("mintlify", testroot="tables")
def test_option_list(app) -> None:
    """`.. option::` renders as a ``<dl>`` definition block, not a Python sig."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # No Python-style heading or fence for option directives.
    assert "## `--file`" not in text
    assert "```python\nFILE--file" not in text
    # The option signature is a <dl> with backticked desc_name parts.
    assert "<dl>\n  <dt>`-f`, `--file` FILE</dt>" in text
    assert "<dl>\n  <dt>`--verbose`</dt>" in text
    assert "Path to the input file." in text
    assert "Print extra detail." in text


@pytest.mark.sphinx("mintlify", testroot="tables-special")
def test_gfm_cell_escapes_pipe(app) -> None:
    """A literal | inside a GFM cell must be backslash-escaped."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "a \\| b" in text, "GFM cell should escape | as \\|"


@pytest.mark.sphinx("mintlify", testroot="tables-special")
def test_gfm_cell_preserves_amp_and_lt_in_plain_text(app) -> None:
    """Plain-text `<` becomes \\<; `&` stays literal."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # plain-text cells go through escape_mdx_text
    assert "tag \\<strong\\>" in text
    assert "amp & co" in text


@pytest.mark.sphinx("mintlify", testroot="tables-special")
def test_html_cell_keeps_pipe_literal_and_escapes_lt(app) -> None:
    """Complex (HTML) table cells must not pipe-escape and must \\<-escape `<`."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<table>" in text
    assert "x | y" in text, "HTML cell does not need pipe escaping"
    assert "a & b \\< c" in text


@pytest.mark.sphinx("mintlify", testroot="tables-special")
def test_gfm_table_uses_single_line_rows(app) -> None:
    """A GFM-rendered table emits exactly one line per row."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "| Symbol | Meaning |" in text
    assert "| `a \\| b` | logical or |" in text
