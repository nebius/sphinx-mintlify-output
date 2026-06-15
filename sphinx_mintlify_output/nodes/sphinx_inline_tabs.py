"""Support for sphinx-inline-tabs."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.escaping import escape_attr
from sphinx_mintlify_output.nodes.base import TranslationNode


class TabContainerNode(TranslationNode):
    """Render consecutive ``TabContainer`` nodes as Mintlify ``<Tabs>``."""

    _INLINE_TAB_NODE = "TabContainer"
    _TAB_CONTENT_CLASS = "tab-content"

    def render(self) -> str:
        parent = self.node.parent
        if not isinstance(parent, nodes.Element):
            return self._render_tab()

        index = parent.index(self.node)
        siblings = parent.children

        parts: list[str] = []
        if self._opens_tab_group(siblings, index):
            parts.append(f"<Tabs{self._tabs_sync_attr()}>\n")
        parts.append(self._render_tab())
        if self._closes_tab_group(siblings, index):
            parts.append("</Tabs>\n\n")
        return "".join(parts)

    def _opens_tab_group(self, siblings: list[nodes.Node], index: int) -> bool:
        # Opens <Tabs> unless the previous sibling is a tab and this tab
        # did not request a new set (``new_set`` is checked on self).
        previous = self._inline_tab_at(siblings, index - 1)
        if previous is None:
            return True
        return self._starts_new_tab_set(self.node)

    def _closes_tab_group(self, siblings: list[nodes.Node], index: int) -> bool:
        # Closes </Tabs> when there is no following tab, or the next tab
        # starts a new set (``new_set`` is checked on the next sibling).
        next_tab = self._inline_tab_at(siblings, index + 1)
        if next_tab is None:
            return True
        return self._starts_new_tab_set(next_tab)

    def _tabs_sync_attr(self) -> str:
        if self.node.get("sync") is False or (
            "sync" in self.node.attributes and self.node.attributes["sync"] == "false"
        ):
            return " sync={false}"
        return ""

    def _render_tab(self) -> str:
        title, content_children = self._tab_parts()
        parts = [f'<Tab title="{escape_attr(title)}">\n']
        if content_children:
            rendered = self.render_docutils_nodes(content_children).strip("\n")
            if rendered:
                parts.append(rendered + "\n\n")
        parts.append("</Tab>\n")
        return "".join(parts)

    def _tab_parts(self) -> tuple[str, list[nodes.Node]]:
        title = ""
        content_children: list[nodes.Node] = []
        for child in self.node.children:
            if isinstance(child, nodes.label):
                title = child.astext().strip()
            elif isinstance(child, nodes.container) and self._TAB_CONTENT_CLASS in (
                child.get("classes") or []
            ):
                content_children = list(child.children)
        return title, content_children

    @classmethod
    def _inline_tab_at(
        cls, siblings: list[nodes.Node], index: int
    ) -> nodes.Element | None:
        if index < 0 or index >= len(siblings):
            return None
        node = siblings[index]
        if not isinstance(node, nodes.Element):
            return None
        if type(node).__name__ != cls._INLINE_TAB_NODE:
            return None
        return node

    @staticmethod
    def _starts_new_tab_set(tab: nodes.Element) -> bool:
        return bool(tab.get("new_set")) or "new-set" in tab.attributes
