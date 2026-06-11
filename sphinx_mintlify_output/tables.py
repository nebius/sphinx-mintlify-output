"""Table rendering: GFM-flavored markdown and HTML fallback for complex tables.

A docutils table arrives as a :class:`~sphinx_mintlify_output.state.TableState`
populated by the translator. :func:`render_table` picks GFM when every cell
fits on one line and the table has no row/colspans, otherwise it falls back
to ``<table>`` HTML for fidelity.
"""

from __future__ import annotations

import re

from sphinx_mintlify_output.state import TableCell, TableState


def render_table(state: TableState) -> str:
    """Pick GFM vs HTML rendering for ``state`` based on complexity."""
    if state.complex or has_multiline_cells(state.head, state.body):
        return render_html_table(state.title, state.head, state.body)
    return render_gfm_table(state.title, state.head, state.body)


def has_multiline_cells(
    head: list[list[TableCell]],
    body: list[list[TableCell]],
) -> bool:
    for group in (head, body):
        for row in group:
            for cell in row:
                if "\n" in cell.text:
                    return True
    return False


_GFM_CELL_ESCAPE_RE = re.compile(r"\\.|[|\n]", re.DOTALL)


def _gfm_cell_sub(match: re.Match[str]) -> str:
    token = match.group(0)
    if token == "|":
        return "\\|"
    if token == "\n":
        return "<br />"
    return token  # already-escaped sequence "\X" passes through verbatim


def escape_gfm_cell(text: str) -> str:
    """Escape pipes and collapse newlines so a cell stays on one GFM row.

    Existing backslash escapes (``\\<``, ``\\{``, ...) are preserved as-is so
    we don't double-escape MDX-safe text that already went through
    :func:`~sphinx_mintlify_output.escaping.escape_mdx_text`.
    """
    if not text:
        return " "
    return _GFM_CELL_ESCAPE_RE.sub(_gfm_cell_sub, text)


def render_gfm_table(
    title: str,
    head: list[list[TableCell]],
    body: list[list[TableCell]],
) -> str:
    rows = head + body
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    header: list[TableCell] = head[0] if head else [TableCell(text="")] * col_count
    while len(header) < col_count:
        header.append(TableCell(text=""))

    lines: list[str] = []
    if title:
        lines.append(f"**{title}**")
        lines.append("")
    lines.append(
        "| " + " | ".join(escape_gfm_cell(cell.text) for cell in header) + " |"
    )
    lines.append("|" + "|".join(["---"] * col_count) + "|")
    for row in head[1:] + body:
        cells = list(row)
        while len(cells) < col_count:
            cells.append(TableCell(text=""))
        lines.append("| " + " | ".join(escape_gfm_cell(c.text) for c in cells) + " |")
    return "\n".join(lines)


def render_html_table(
    title: str,
    head: list[list[TableCell]],
    body: list[list[TableCell]],
) -> str:
    lines: list[str] = ["<table>"]
    if title:
        lines.append(f"  <caption>{title}</caption>")
    if head:
        lines.append("  <thead>")
        for row in head:
            lines.append("    <tr>")
            for cell in row:
                lines.append("      " + render_html_cell(cell, header=True))
            lines.append("    </tr>")
        lines.append("  </thead>")
    if body:
        lines.append("  <tbody>")
        for row in body:
            lines.append("    <tr>")
            for cell in row:
                lines.append("      " + render_html_cell(cell, header=False))
            lines.append("    </tr>")
        lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)


def render_html_cell(cell: TableCell, *, header: bool) -> str:
    tag = "th" if header else "td"
    attrs: list[str] = []
    if cell.morerows:
        attrs.append(f'rowspan="{cell.morerows + 1}"')
    if cell.morecols:
        attrs.append(f'colspan="{cell.morecols + 1}"')
    open_tag = f"<{tag}{(' ' + ' '.join(attrs)) if attrs else ''}>"
    return f"{open_tag}{cell.text}</{tag}>"
