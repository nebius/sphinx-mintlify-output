"""Definition lists and RFC2822-style field lists rendered as ``<dl>`` / lines."""

from __future__ import annotations

from sphinx_mintlify_output.nodes.base import TranslationNode


class DefinitionListNode(TranslationNode):
    def render(self) -> str:
        return "<dl>\n" + self.render_children() + "</dl>\n\n"


class TermNode(TranslationNode):
    def render(self) -> str:
        return f"  <dt>{self.render_children()}</dt>\n"


class ClassifierNode(TranslationNode):
    def render(self) -> str:
        return f" <em>{self.render_children()}</em>"


class DefinitionNode(TranslationNode):
    def render(self) -> str:
        body = self.render_children().strip("\n").strip()
        return f"  <dd>\n{body}\n  </dd>\n"


class FieldListNode(TranslationNode):
    """Plain field list — ``- **name** — value`` lines.

    When this field list lives inside a desc_content the surrounding
    :class:`~sphinx_mintlify_output.nodes.autodoc.DescNode` intercepts it;
    this path only fires for top-level field lists (e.g. RFC2822 fields
    at the start of a document).
    """

    def render(self) -> str:
        return self.render_children() + "\n"


class FieldNameNode(TranslationNode):
    def render(self) -> str:
        return f"- **{self.render_children()}** — "


class FieldBodyNode(TranslationNode):
    def render(self) -> str:
        body = self.render_children().strip("\n").strip()
        return body.replace("\n\n", "\n  ") + "\n"
