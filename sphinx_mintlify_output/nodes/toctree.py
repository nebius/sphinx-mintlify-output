"""Toctree-driven ``<Columns>`` of ``<Card>`` links.

There are two shapes the toctree shows up in: an unresolved ``toctree``
node (only when re-injected by
:func:`sphinx_mintlify_output.builder.inject_hidden_toctrees`) and a
post-resolution ``compound`` wrapper that contains a caption + a
bullet_list of references.
"""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.escaping import escape_attr
from sphinx_mintlify_output.nodes.base import TranslationNode
from sphinx_mintlify_output.toctree import (
    doc_icon,
    doc_summary,
    doc_title_or_slug,
    docname_from_refuri,
)
from sphinx_mintlify_output.urls import url_for


class ToctreeNode(TranslationNode):
    """Render an unresolved ``toctree`` directive as a card group."""

    def render(self) -> str:
        caption = (self.node.get("caption") or "").strip()
        entries = self.node.get("entries") or []
        env = self.ctx.builder.env
        cards: list[tuple[str, str, str, str]] = []
        for title, docname in entries:
            if not docname:
                continue
            label = (title or "").strip() or doc_title_or_slug(env, docname)
            description = doc_summary(env, docname)
            icon = doc_icon(env, docname)
            href = url_for(self.ctx.docname, docname)
            cards.append((label, href, description, icon))
        if not cards:
            return ""
        return _render_toctree_cards(caption, cards)


class CompoundNode(TranslationNode):
    """A ``compound`` wrapper — only ``toctree-wrapper`` gets card treatment."""

    def render(self) -> str:
        classes = self.node.get("classes") or []
        if "toctree-wrapper" not in classes:
            return self.render_children()
        caption = ""
        seen: set[str] = set()
        env = self.ctx.builder.env
        cards: list[tuple[str, str, str, str]] = []
        for descendant in self.node.findall():
            if isinstance(descendant, nodes.caption):
                caption = descendant.astext().strip()
                continue
            if not isinstance(descendant, nodes.reference):
                continue
            title = descendant.astext().strip()
            refuri = descendant.get("refuri") or descendant.get("refid") or ""
            if not (title and refuri) or refuri in seen:
                continue
            seen.add(refuri)
            # ``refuri`` already comes from ``MintlifyBuilder.get_relative_uri``,
            # so it's either an absolute URL (``/path`` or ``http(s)://``),
            # a fragment, or a relative slug — emit it verbatim either way.
            docname = docname_from_refuri(self.ctx.docname, refuri)
            icon = doc_icon(env, docname) if docname else ""
            cards.append((title, refuri, "", icon))
        if not cards:
            return ""
        return _render_toctree_cards(caption, cards)


def _render_toctree_cards(caption: str, cards: list[tuple[str, str, str, str]]) -> str:
    out: list[str] = []
    if caption:
        out.append(f"## {caption}\n\n")
    out.append("<Columns cols={2}>\n")
    for label, href, description, icon in cards:
        attrs = [
            f'title="{escape_attr(label)}"',
            f'href="{escape_attr(href)}"',
        ]
        if icon:
            attrs.append(f'icon="{escape_attr(icon)}"')
        out.append(f"  <Card {' '.join(attrs)}>\n")
        if description:
            out.append(f"    {description}\n")
        out.append("  </Card>\n")
    out.append("</Columns>\n\n")
    return "".join(out)
