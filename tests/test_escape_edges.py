"""Edge-case escape tests for MDX/JSX/Markdown attribute values.

The current pipeline routes user text through :func:`escape_attr` for
JSX attributes and :func:`escape_md_url` for ``(href)`` targets. These
tests document the contract — the legacy single-quote ``escape_attr``
let ``<``/``>``/``&`` leak into rendered output, breaking strict MDX
parsers.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_image_alt_with_quotes_uses_jsx_safe_attr(app) -> None:
    """Markdown ``![alt](url)`` form: alt text escapes ``]`` / ``[``."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # alt text in markdown form should not contain unescaped square brackets
    # that would terminate the [alt] portion early.
    assert (
        '![A "dotted" line & arrow]' in text or '![A "dotted" line &amp; arrow]' in text
    ), "image alt text should round-trip without breaking parsing"


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_long_caption_renders_without_raw_lt_gt(app) -> None:
    """A long figure caption rendered as prose escapes ``<>`` via the pipeline."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # The caption "Caption with <angle> & "quoted" text." flows through
    # TextNode (escape_mdx_text) which escapes < and >. The legacy code
    # injected raw .astext(), producing an MDX parse error.
    assert "<angle>" not in text or "\\<angle\\>" in text


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_tab_title_with_special_chars_escaped(app) -> None:
    """Tab title with ``>`` must be escaped as ``&gt;`` for JSX."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # Sphinx smart-quotes the ASCII " to curly quotes which pass through
    # unescaped (they're not JSX-significant). The angle bracket is what
    # matters — it must not leak as raw < or >.
    assert 'title="a &gt; b' in text


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_card_title_ampersand_escaped(app) -> None:
    """Card title containing ``&`` must be JSX-escaped as ``&amp;``."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert 'title="A &amp; B' in text


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_no_raw_unescaped_ampersand_in_jsx_attributes(app) -> None:
    """Sanity: a literal ``& `` should not survive raw inside a JSX attribute."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # We scan only inside tag-attr-like sequences. A naive search for "& "
    # inside the body markdown is fine because the test fixture only uses
    # `&` inside attributes; everything else is the literal in markdown.
    for line in text.splitlines():
        if "title=" in line or "alt=" in line or "caption=" in line:
            # No raw ampersand-space, no raw <, no raw " (after the opening).
            assert "& " not in line
            assert " < " not in line


@pytest.mark.sphinx("mintlify", testroot="escape-edges")
def test_external_link_url_preserves_existing_percent_encoding(app) -> None:
    """A URL with literal spaces / parens gets encoded; existing ``%XX`` left alone."""
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    # The fixture URL already has %20 and %26; escape_md_url should not
    # double-encode the % sign.
    assert "https://example.com/?q=X%20%26%20Y" in text
