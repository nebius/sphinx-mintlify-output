"""Bullet and enumerated lists."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.nodes.base import TranslationContext, TranslationNode


class BulletListNode(TranslationNode):
    """Unordered list — children handle their own markers via parent lookup."""

    def render(self) -> str:
        return self.render_children() + "\n"


class EnumeratedListNode(TranslationNode):
    """Ordered list — mutable ``counter`` is read+bumped by each child item."""

    __slots__ = ("counter",)

    def __init__(
        self,
        node: nodes.Node,
        parent: TranslationNode | None,
        ctx: TranslationContext,
    ) -> None:
        super().__init__(node, parent, ctx)
        self.counter = (
            int(node.get("start", 1)) if isinstance(node, nodes.Element) else 1
        )

    def next_marker(self) -> str:
        marker = f"{self.counter}. "
        self.counter += 1
        return marker

    def render(self) -> str:
        return self.render_children() + "\n"


class ListItemNode(TranslationNode):
    """A list item — asks its enclosing list for the bullet/number prefix."""

    def render(self) -> str:
        body = self.render_children().strip("\n")
        marker = self._marker()
        indent = " " * len(marker)
        lines = body.split("\n")
        out = [marker + lines[0]] if lines else [marker.rstrip()]
        for line in lines[1:]:
            out.append("\n")
            if line:
                out.append(indent + line)
        return "".join(out) + "\n"

    def _marker(self) -> str:
        parent = self.parent
        if isinstance(parent, EnumeratedListNode):
            return parent.next_marker()
        return "- "
