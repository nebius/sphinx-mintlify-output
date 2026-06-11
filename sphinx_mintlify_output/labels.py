"""Footnote and citation label extraction from docutils nodes."""

from __future__ import annotations

from docutils import nodes


def footnote_label(node: nodes.footnote) -> str:
    for child in node.children:
        if isinstance(child, nodes.label):
            return str(child.astext())
    names = node.get("names") or node.get("ids") or [""]
    return str(names[0])


def citation_label(node: nodes.citation) -> str:
    for child in node.children:
        if isinstance(child, nodes.label):
            return str(child.astext())
    names = node.get("names") or node.get("ids") or [""]
    return str(names[0])
