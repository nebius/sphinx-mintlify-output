"""References, anchors and inline targets."""

from __future__ import annotations

from sphinx_mintlify_output.escaping import escape_md_url
from sphinx_mintlify_output.nodes.base import TranslationNode


class ReferenceNode(TranslationNode):
    """An inline link: ``[text](url)`` or ``[text](#anchor)``.

    Citation references (which docutils rewrites from ``citation_reference``
    to plain ``reference`` nodes during transforms) are detected by
    matching ``refid`` against :attr:`TranslationContext.citation_ids` and
    rendered as ``[^id]`` so they pair with the corresponding
    ``[^id]: body`` definition emitted by ``CitationNode``.
    """

    def render(self) -> str:
        refuri = self.node.get("refuri")
        refid = self.node.get("refid")
        if refid and refid in self.ctx.citation_ids:
            return f"[^{refid}]"
        text = self.render_children()
        if refuri:
            return f"[{text}]({escape_md_url(refuri)})"
        if refid:
            return f"[{text}](#{escape_md_url(refid)})"
        return text


class TargetNode(TranslationNode):
    """Inline target — emits ``<a id="...">`` when anchors are enabled."""

    def render(self) -> str:
        if not self.ctx.builder.config.mintlify_emit_anchors:
            return ""
        ids = self.node.get("ids") or []
        if not ids:
            return ""
        return "".join(f'<a id="{sid}"></a>' for sid in ids)
