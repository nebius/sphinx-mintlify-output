"""Images, figures and standalone captions."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.assets import relative_image_path
from sphinx_mintlify_output.escaping import (
    escape_attr,
    escape_md_link_text,
    escape_md_url,
)
from sphinx_mintlify_output.nodes.base import TranslationNode


class ImageNode(TranslationNode):
    """``.. image::`` — Markdown ``![alt](src)`` or ``<img>`` when sized."""

    def render(self) -> str:
        uri = self.node.get("uri", "")
        alt = self.node.get("alt", "")
        builder = self.ctx.builder
        canonical = builder.images.get(uri, uri)
        image_dir = builder.config.mintlify_image_dir
        target = relative_image_path(self.ctx.docname, image_dir, canonical)
        width = self.node.get("width")
        height = self.node.get("height")
        if width or height:
            attrs = [f'src="{escape_attr(target)}"']
            if alt:
                attrs.append(f'alt="{escape_attr(alt)}"')
            if width:
                attrs.append(f'width="{escape_attr(str(width))}"')
            if height:
                attrs.append(f'height="{escape_attr(str(height))}"')
            text = "<img " + " ".join(attrs) + " />"
        else:
            text = f"![{escape_md_link_text(alt)}]({escape_md_url(target)})"
        # A standalone image (direct child of section/container/document) is a
        # block — give it its own blank line. Inline images (inside a
        # paragraph) ride that paragraph's trailing newline.
        if self._is_block():
            return text + "\n\n"
        return text

    def _is_block(self) -> bool:
        parent = self.node.parent
        return parent is not None and not isinstance(parent, nodes.paragraph)


class FigureNode(TranslationNode):
    """``.. figure::`` → ``<Frame caption="…">`` or ``<Frame>…<caption>``.

    A short single-line caption is lifted into the ``caption=""`` attribute
    (escaped for JSX). A long or multi-line caption stays in the body,
    rendered through the normal pipeline so inline markup survives and
    MDX-meta characters get escaped via :class:`TextNode`.
    """

    def render(self) -> str:
        caption_node: nodes.caption | None = None
        for child in self.node.children:
            if isinstance(child, nodes.caption):
                caption_node = child
                break

        caption_text = caption_node.astext().strip() if caption_node else ""
        caption_in_attr = (
            bool(caption_text) and "\n" not in caption_text and len(caption_text) < 200
        )
        opening = (
            f'<Frame caption="{escape_attr(caption_text)}">\n'
            if caption_in_attr
            else "<Frame>\n"
        )

        body_parts: list[str] = []
        for child in self.node.children:
            if isinstance(child, nodes.caption):
                continue
            body_parts.append(
                TranslationNode.from_docutils(child, self, self.ctx).render()
            )
        body = "".join(body_parts).rstrip("\n")

        trailer = ""
        if not caption_in_attr and caption_node is not None:
            # Render the caption through the pipeline so inline markup is
            # preserved and MDX-meta characters get escaped — never inject
            # the raw .astext() into the page.
            inline_caption = self.render_docutils_nodes(
                list(caption_node.children)
            ).strip()
            if inline_caption:
                trailer = f"\n*{inline_caption}*\n"
        return f"{opening}{body}{trailer}</Frame>\n\n"


class CaptionNode(TranslationNode):
    """Image/figure caption rendered inline as ``*text*``.

    :class:`FigureNode` consumes captions itself for the ``<Frame>`` attribute,
    so this only fires on captions outside figures (e.g. for code-block titles).
    """

    def render(self) -> str:
        return f"*{self.render_children()}*\n\n"
