"""Footnote and citation rendering.

Inline references (``[#fn]_``, ``[Cite]_``) become ``[^id]`` and the
defining block (``.. [#fn] body``) renders as ``[^id]: body`` with
continuation lines indented under the marker.
"""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.escaping import indent_continuation
from sphinx_mintlify_output.labels import citation_label, footnote_label
from sphinx_mintlify_output.nodes.base import TranslationNode


class FootnoteReferenceNode(TranslationNode):
    """``[#fn]_`` / numeric footnote reference → ``[^id]``."""

    def render(self) -> str:
        return f"[^{self.node.astext()}]"


class CitationReferenceNode(TranslationNode):
    """``[Smith2020]_`` citation reference → ``[^id]``."""

    def render(self) -> str:
        return f"[^{self.node.astext()}]"


class FootnoteNode(TranslationNode):
    """A footnote definition: ``[^id]: body`` with continuation indent."""

    node: nodes.footnote

    def render(self) -> str:
        label = footnote_label(self.node)
        body = _render_body_skip_label(self).strip("\n").strip()
        return f"[^{label}]: {indent_continuation(body, '    ')}\n\n"


class CitationNode(TranslationNode):
    """A citation definition — same shape as a footnote in Markdown.

    Uses the docutils-normalised id (``ids[0]``) rather than the human
    label so it pairs with :class:`~sphinx_mintlify_output.nodes.links.ReferenceNode`,
    which only sees the lowercased refid after Sphinx resolves citation
    references to plain reference nodes.
    """

    node: nodes.citation

    def render(self) -> str:
        ids = self.node.get("ids") or []
        marker = ids[0] if ids else citation_label(self.node)
        body = _render_body_skip_label(self).strip("\n").strip()
        return f"[^{marker}]: {indent_continuation(body, '    ')}\n\n"


class LabelNode(TranslationNode):
    """The ``label`` child of a footnote/citation — already in ``[^id]:``."""

    def render(self) -> str:
        return ""


def _render_body_skip_label(host: TranslationNode) -> str:
    """Render every child except the label (whose text is already in the marker)."""
    return host.render_docutils_nodes(
        [c for c in host.node.children if not isinstance(c, nodes.label)]
    )
