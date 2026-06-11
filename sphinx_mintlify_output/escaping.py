"""Text escaping and MDX-compatibility helpers.

Pure functions with no Sphinx/docutils dependency — the building blocks
shared across :mod:`tables`, :mod:`autodoc`, and the main translator.
"""

from __future__ import annotations

import re


def escape_mdx_text(text: str) -> str:
    """Escape characters that would otherwise be interpreted by MDX/Markdown."""
    out: list[str] = []
    for ch in text:
        if ch in {"<", ">", "{", "}"}:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def escape_attr(text: str) -> str:
    """Escape a value for a double-quoted JSX/HTML attribute.

    Covers the four characters that can confuse a JSX or HTML parser
    inside ``key="value"``: ``&`` (entity start), ``"`` (closes the
    attribute), and ``<``/``>`` (would open a tag). Single-pass — call
    this exactly once per attribute value.
    """
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def escape_md_link_text(text: str) -> str:
    """Escape characters that would terminate a markdown ``[text](...)`` link."""
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def escape_md_url(text: str) -> str:
    """Percent-encode the characters that would terminate a ``(url)``.

    The minimal set that breaks ``(...)`` link targets: literal parens,
    whitespace and the angle-bracket variant. Existing percent-encoded
    sequences pass through (we don't re-encode ``%``).
    """
    return (
        text.replace(" ", "%20")
        .replace("(", "%28")
        .replace(")", "%29")
        .replace("<", "%3C")
        .replace(">", "%3E")
    )


def pick_inline_code_fence(text: str) -> str:
    """Pick an inline code fence that does not collide with the text content."""
    width = 1
    while "`" * width in text:
        width += 1
    return "`" * width


def pick_block_fence(text: str) -> str:
    """Pick a fence wider than any backtick run in the block."""
    width = 3
    longest = 0
    run = 0
    for ch in text:
        if ch == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    if longest >= width:
        width = longest + 1
    return "`" * width


def indent_continuation(text: str, indent: str) -> str:
    """Indent every line after the first by ``indent`` (preserving blank lines)."""
    lines = text.split("\n")
    out: list[str] = [lines[0]] if lines else [""]
    for line in lines[1:]:
        out.append("\n")
        if line:
            out.append(indent + line)
    return "".join(out)


def quote_lines(text: str) -> str:
    """Prefix every line with a markdown blockquote marker (``> `` or ``>``)."""
    out_lines: list[str] = []
    for line in text.split("\n"):
        if line:
            out_lines.append("> " + line)
        else:
            out_lines.append(">")
    return "\n".join(out_lines)


def split_first_line(text: str) -> tuple[str, str]:
    """Split rendered list_item content into (title, remaining body)."""
    stripped = text.strip()
    if not stripped:
        return "", ""
    parts = stripped.split("\n", 1)
    title = parts[0].strip().strip("*").strip("_").strip("#").strip()
    if not title:
        title = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return title, rest


HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE)
HTML_HEAD_ONLY_TAG_RE = re.compile(
    r"<(?:meta|link|base|title|style)\b[^>]*/?>",
    re.IGNORECASE,
)
HTML_VOID_OPEN_RE = re.compile(
    r"<(?P<tag>area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr)"
    r"\b(?P<attrs>[^>]*?)(?<!/)>",
    re.IGNORECASE,
)


def sanitize_for_mdx(html: str) -> str:
    """Make a raw HTML fragment palatable to MDX/JSX parsers.

    MDX rejects HTML comments, DOCTYPE declarations and unclosed void elements.
    The transform strips page-level tags that have no body meaning
    (``<meta>``, ``<link>``, ``<style>``, ``<title>``, ``<base>``) and
    self-closes any remaining void tags so the result parses as JSX.
    """
    html = HTML_COMMENT_RE.sub("", html)
    html = HTML_DOCTYPE_RE.sub("", html)
    html = HTML_HEAD_ONLY_TAG_RE.sub("", html)

    def close_void(match: re.Match[str]) -> str:
        tag = match.group("tag")
        attrs = match.group("attrs")
        return f"<{tag}{attrs} />"

    html = HTML_VOID_OPEN_RE.sub(close_void, html)
    return html
