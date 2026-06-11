"""Inline text formatting: emphasis, strong, literal, sub/sup, abbreviation."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.escaping import (
    escape_attr,
    escape_mdx_text,
    pick_inline_code_fence,
)
from sphinx_mintlify_output.nodes.base import TranslationNode


class TextNode(TranslationNode):
    """Plain text — escape MDX-significant characters (raw inside signatures).

    Only leaf node where the wrapped docutils value is a
    :class:`docutils.nodes.Text` rather than an
    :class:`docutils.nodes.Element`. Read via ``.astext()`` which both
    types expose.
    """

    node: nodes.Text  # type: ignore[assignment]

    def render(self) -> str:
        text = self.node.astext()
        if self.ctx.signature_depth > 0:
            return text
        return escape_mdx_text(text)


class EmphasisNode(TranslationNode):
    def render(self) -> str:
        return f"*{self.render_children()}*"


class StrongNode(TranslationNode):
    def render(self) -> str:
        return f"**{self.render_children()}**"


class LiteralNode(TranslationNode):
    """Inline ``literal`` (``backticks``) — pick a fence wider than content."""

    def render(self) -> str:
        text = self.node.astext()
        if self.ctx.signature_depth > 0:
            return text
        fence = pick_inline_code_fence(text)
        spacer = " " if text.startswith("`") or text.endswith("`") else ""
        return f"{fence}{spacer}{text}{spacer}{fence}"


class SubscriptNode(TranslationNode):
    def render(self) -> str:
        return f"<sub>{self.render_children()}</sub>"


class SuperscriptNode(TranslationNode):
    def render(self) -> str:
        return f"<sup>{self.render_children()}</sup>"


class AbbreviationNode(TranslationNode):
    """``:abbr:`X (explanation)``` → ``<Tooltip tip="explanation">X</Tooltip>``."""

    def render(self) -> str:
        text = self.node.astext()
        explanation = ""
        if isinstance(self.node, nodes.Element):
            explanation = self.node.get("explanation") or ""
        if explanation:
            return f'<Tooltip tip="{escape_attr(explanation)}">{text}</Tooltip>'
        return text
