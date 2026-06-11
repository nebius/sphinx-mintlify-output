"""Raw HTML/MDX passthrough and silent docutils comments."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.assets import externalize_inline_assets
from sphinx_mintlify_output.escaping import sanitize_for_mdx
from sphinx_mintlify_output.nodes.base import TranslationNode


class RawNode(TranslationNode):
    """Raw passthrough — only when the format is ``html`` / ``mdx`` / ``markdown``.

    Optionally extracts inline ``<svg>`` blocks and ``data:image/...`` URIs to
    separate files via :func:`externalize_inline_assets`.
    """

    def render(self) -> str:
        if not isinstance(self.node, nodes.Element):
            return ""
        formats = {f.lower() for f in (self.node.get("format") or "").split()}
        if not formats.intersection({"html", "mdx", "markdown"}):
            return ""
        text = self.node.astext()
        builder = self.ctx.builder
        if builder.config.mintlify_externalize_assets:
            text = externalize_inline_assets(
                text,
                outdir=builder.outdir,
                image_dir=builder.config.mintlify_image_dir,
                from_doc=self.ctx.docname,
            )
        text = sanitize_for_mdx(text)
        if not text.strip():
            return ""
        return text + "\n\n"


class CommentNode(TranslationNode):
    """``.. comment::`` — silently dropped."""

    def render(self) -> str:
        return ""
