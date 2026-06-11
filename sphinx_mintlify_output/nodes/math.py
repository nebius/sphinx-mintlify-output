"""Inline and block math — KaTeX-compatible ``$...$`` / ``$$...$$``."""

from __future__ import annotations

from sphinx_mintlify_output.nodes.base import TranslationNode


class MathNode(TranslationNode):
    """Inline math: ``:math:`...``` → ``$...$``."""

    def render(self) -> str:
        return f"${self.node.astext()}$"


class MathBlockNode(TranslationNode):
    """``.. math::`` block → ``$$ ... $$``."""

    def render(self) -> str:
        return f"$$\n{self.node.astext().strip()}\n$$\n\n"
