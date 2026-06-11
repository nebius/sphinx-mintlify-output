"""Direct unit tests for the pure helpers in :mod:`escaping`.

These run without Sphinx — failures here pinpoint the specific helper,
which is faster to debug than golden-corpus regressions.
"""

from __future__ import annotations

import pytest

from sphinx_mintlify_output.escaping import (
    escape_attr,
    escape_md_link_text,
    escape_md_url,
    escape_mdx_text,
    indent_continuation,
    pick_block_fence,
    pick_inline_code_fence,
    quote_lines,
    sanitize_for_mdx,
    split_first_line,
)

# ---------------------------------------------------------------------------
# escape_mdx_text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("plain text", "plain text"),
        ("a < b", "a \\< b"),
        ("a > b", "a \\> b"),
        ("{key}", "\\{key\\}"),
        ("<Note>", "\\<Note\\>"),
        ("", ""),
        ("a\nb", "a\nb"),
    ],
)
def test_escape_mdx_text(raw: str, expected: str) -> None:
    assert escape_mdx_text(raw) == expected


def test_escape_mdx_text_leaves_amp_alone() -> None:
    # MDX text mode tolerates raw `&` — only JSX attrs need entity-escape.
    assert escape_mdx_text("A & B") == "A & B"


# ---------------------------------------------------------------------------
# escape_attr (JSX/HTML attribute)
# ---------------------------------------------------------------------------


def test_escape_attr_quote() -> None:
    assert escape_attr('hello "world"') == "hello &quot;world&quot;"


def test_escape_attr_ampersand() -> None:
    assert escape_attr("A & B") == "A &amp; B"


def test_escape_attr_angle_brackets() -> None:
    assert escape_attr("<tag>") == "&lt;tag&gt;"


def test_escape_attr_single_pass() -> None:
    # & comes before " in the chain; a literal &amp; should not be re-encoded.
    assert escape_attr("&amp; here") == "&amp;amp; here"
    # The above looks weird but documents the single-pass contract: callers
    # must hand in unescaped text, not pre-encoded entities.


def test_escape_attr_empty() -> None:
    assert escape_attr("") == ""


# ---------------------------------------------------------------------------
# escape_md_link_text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("plain", "plain"),
        ("a [bracket] b", "a \\[bracket\\] b"),
        ("a]b", "a\\]b"),
        ("path\\to\\thing", "path\\\\to\\\\thing"),
    ],
)
def test_escape_md_link_text(raw: str, expected: str) -> None:
    assert escape_md_link_text(raw) == expected


# ---------------------------------------------------------------------------
# escape_md_url
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://example.com", "https://example.com"),
        ("/path with spaces", "/path%20with%20spaces"),
        ("/page(x).html", "/page%28x%29.html"),
        ("javascript:<alert>", "javascript:%3Calert%3E"),
        ("", ""),
    ],
)
def test_escape_md_url(raw: str, expected: str) -> None:
    assert escape_md_url(raw) == expected


def test_escape_md_url_preserves_existing_percent_encoding() -> None:
    # We don't re-encode %, so already-encoded URIs pass through unchanged.
    assert escape_md_url("/already%20encoded") == "/already%20encoded"


# ---------------------------------------------------------------------------
# pick_inline_code_fence / pick_block_fence
# ---------------------------------------------------------------------------


def test_inline_fence_default() -> None:
    assert pick_inline_code_fence("hello") == "`"


def test_inline_fence_widens_on_collision() -> None:
    # Single backtick collides → use two.
    assert pick_inline_code_fence("with `tick`") == "``"
    # Two collide → use three.
    assert pick_inline_code_fence("with ``two``") == "```"


def test_block_fence_default() -> None:
    assert pick_block_fence("plain code") == "```"


def test_block_fence_widens_past_longest_run() -> None:
    text = "```nested\n```"
    assert pick_block_fence(text) == "````"


def test_block_fence_short_text_with_backticks() -> None:
    # `text` shorter than 3, but contains one backtick — fence stays at 3.
    assert pick_block_fence("a `b` c") == "```"


# ---------------------------------------------------------------------------
# indent_continuation
# ---------------------------------------------------------------------------


def test_indent_continuation_single_line() -> None:
    assert indent_continuation("hello", "    ") == "hello"


def test_indent_continuation_multiline() -> None:
    assert (
        indent_continuation("first\nsecond\nthird", "    ")
        == "first\n    second\n    third"
    )


def test_indent_continuation_preserves_blank_lines() -> None:
    assert indent_continuation("a\n\nb", "  ") == "a\n\n  b"


def test_indent_continuation_empty() -> None:
    assert indent_continuation("", "    ") == ""


# ---------------------------------------------------------------------------
# quote_lines
# ---------------------------------------------------------------------------


def test_quote_lines_basic() -> None:
    assert quote_lines("first\nsecond") == "> first\n> second"


def test_quote_lines_blank_line_stays_blank_quote() -> None:
    assert quote_lines("a\n\nb") == "> a\n>\n> b"


def test_quote_lines_empty() -> None:
    assert quote_lines("") == ">"


# ---------------------------------------------------------------------------
# split_first_line
# ---------------------------------------------------------------------------


def test_split_first_line_simple() -> None:
    assert split_first_line("Title\n\nBody text.") == ("Title", "Body text.")


def test_split_first_line_strips_marker_chars() -> None:
    # Leading/trailing * _ # are stripped from the title (used for list_item
    # rendering where the first line carries marker punctuation).
    assert split_first_line("**Bold title**\nBody") == ("Bold title", "Body")


def test_split_first_line_single_line() -> None:
    assert split_first_line("Just a title") == ("Just a title", "")


def test_split_first_line_empty() -> None:
    assert split_first_line("") == ("", "")


def test_split_first_line_whitespace_only_first_line() -> None:
    # When the marker-strip leaves nothing, fall back to the raw first line.
    assert split_first_line("***\nBody") == ("***", "Body")


# ---------------------------------------------------------------------------
# sanitize_for_mdx
# ---------------------------------------------------------------------------


def test_sanitize_strips_html_comments() -> None:
    assert sanitize_for_mdx("before<!-- comment -->after") == "beforeafter"


def test_sanitize_strips_doctype() -> None:
    assert sanitize_for_mdx("<!DOCTYPE html><p>hi</p>") == "<p>hi</p>"


def test_sanitize_strips_head_tags() -> None:
    src = '<meta charset="utf-8"><link rel="stylesheet"><p>body</p>'
    assert sanitize_for_mdx(src) == "<p>body</p>"


def test_sanitize_self_closes_void_tags() -> None:
    src = '<img src="x.png"><br><hr>'
    out = sanitize_for_mdx(src)
    assert "<img " in out and out.count("/>") == 3


def test_sanitize_passes_through_normal_html() -> None:
    assert sanitize_for_mdx("<p>hello</p>") == "<p>hello</p>"
