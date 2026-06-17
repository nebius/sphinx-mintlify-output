"""Block-level structural nodes: sections, titles, paragraphs, code blocks."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.escaping import escape_attr, pick_block_fence
from sphinx_mintlify_output.nodes.base import TranslationNode


class SectionNode(TranslationNode):
    """A docutils section — bumps heading depth for children."""

    def render(self) -> str:
        self.ctx.section_level += 1
        try:
            body = self.render_children()
        finally:
            self.ctx.section_level -= 1
        return body


class TitleNode(TranslationNode):
    """A section title — captured into frontmatter if top-level, else heading."""

    def render(self) -> str:
        # Titles inside tables and admonitions are consumed by the wrapping
        # node (table caption, admonition component) — emit nothing here.
        if isinstance(self.node.parent, nodes.table | nodes.Admonition):
            return ""
        parent_section = isinstance(self.parent, SectionNode)
        if (
            parent_section
            and not self.ctx.title_captured
            and self.ctx.section_level == 1
        ):
            self.ctx.frontmatter.setdefault("title", self.node.astext().strip())
            self.ctx.title_captured = True
            return ""
        level = max(1, self.ctx.section_level)
        prefix = ""
        if self.ctx.builder.config.mintlify_emit_anchors and isinstance(
            self.node.parent, nodes.section
        ):
            ids = self.node.parent.get("ids") or []
            # Mintlify derives the primary heading slug from markdown; only
            # emit anchors for additional explicit reference targets.
            for sid in ids[1:]:
                prefix += f'<a id="{escape_attr(sid)}"></a>\n'
        return prefix + f"{'#' * level} {self.render_children()}\n\n"


class ParagraphNode(TranslationNode):
    def render(self) -> str:
        return self.render_children() + "\n\n"


class BlockQuoteNode(TranslationNode):
    def render(self) -> str:
        body = self.render_children().strip("\n")
        lines = ("> " + line if line else ">" for line in body.split("\n"))
        return "\n".join(lines) + "\n\n"


class TransitionNode(TranslationNode):
    def render(self) -> str:
        return "---\n\n"


class LiteralBlockNode(TranslationNode):
    """A ``code-block`` — fenced with a width that won't collide with content."""

    def render(self) -> str:
        text = self.node.astext().rstrip("\n")
        language = self.node.get("language") or ""
        if language in {"default", "none"}:
            language = ""
        fence = pick_block_fence(text)
        return f"{fence}{language}\n{text}\n{fence}\n\n"


class MermaidNode(TranslationNode):
    """``sphinxcontrib.mermaid`` ``mermaid`` node → Mintlify `` ```mermaid `` fence.

    Diagram source lives in the node ``code`` attribute, not in child nodes.
    """

    def render(self) -> str:
        code = str(self.node.get("code", "")).rstrip("\n")
        fence = pick_block_fence(code)
        return f"{fence}mermaid\n{code}\n{fence}\n\n"
