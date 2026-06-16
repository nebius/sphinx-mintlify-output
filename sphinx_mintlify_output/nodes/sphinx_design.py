"""sphinx-design containers: card, tab-set, dropdown, and grid rows."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.components import (
    grid_cols_from_classes,
    sphinx_design_card_body,
    sphinx_design_card_href,
    sphinx_design_card_title,
    sphinx_design_dropdown_body,
    sphinx_design_dropdown_title,
    tab_item_code,
    tab_item_is_code_only,
    tab_item_title,
)
from sphinx_mintlify_output.escaping import escape_attr, pick_block_fence
from sphinx_mintlify_output.nodes.base import TranslationNode


class ContainerNode(TranslationNode):
    """A ``container`` — dispatch to sphinx-design or default to children."""

    node: nodes.container

    def render(self) -> str:
        component = self.node.get("design_component") or ""
        classes = set(self.node.get("classes") or [])
        if component == "tab-set":
            return self._render_tab_set()
        if component == "dropdown":
            return self._render_dropdown()
        if component == "card":
            return self._render_card()
        if "sd-row" in classes:
            return self._render_grid_row(classes)
        return self.render_children()

    def _render_card(self) -> str:
        title = sphinx_design_card_title(self.node)
        href = sphinx_design_card_href(self.node)
        body_children = sphinx_design_card_body(self.node)
        attrs: list[str] = []
        if title:
            attrs.append(f'title="{escape_attr(title)}"')
        if href:
            attrs.append(f'href="{escape_attr(href)}"')
        attr_str = (" " + " ".join(attrs)) if attrs else ""
        body = self.render_docutils_nodes(body_children).strip("\n").strip()
        inner = body + "\n" if body else ""
        return f"<Card{attr_str}>\n{inner}</Card>\n\n"

    def _render_tab_set(self) -> str:
        items = [
            child
            for child in self.node.children
            if isinstance(child, nodes.container)
            and "sd-tab-item" in (child.get("classes") or [])
        ]
        if items and all(tab_item_is_code_only(item) for item in items):
            return self._render_code_group(items)

        sync_attr = ""
        if self.node.get("sync") is False or (
            "sync" in self.node.attributes and self.node.attributes["sync"] == "false"
        ):
            sync_attr = " sync={false}"

        out = [f"<Tabs{sync_attr}>\n"]
        for item in items:
            out.append(self._render_tab_item(item))
        out.append("</Tabs>\n\n")
        return "".join(out)

    def _render_code_group(self, items: list[nodes.container]) -> str:
        # Mintlify's documented form is ``<CodeGroup>`` with explicit
        # ``<CodeBlock title="...">`` children, but its MDX renderer also
        # accepts plain fenced code blocks where the fence label carries
        # ``<language> <title>`` and lifts them into a CodeGroup tab.
        # We emit the fence form because (1) it keeps the source
        # roundtrippable through standard markdown tools and (2) it does
        # not need a separate JSX wrapper per item. If Mintlify ever
        # drops this convenience, swap to ``<CodeBlock>`` children here.
        out = ["<CodeGroup>\n\n"]
        for item in items:
            title = tab_item_title(item)
            code, language = tab_item_code(item)
            fence = pick_block_fence(code)
            label = f"{language} {title}".strip() if language else title
            out.append(f"{fence}{label}\n{code}\n{fence}\n\n")
        out.append("</CodeGroup>\n\n")
        return "".join(out)

    def _render_tab_item(self, item: nodes.container) -> str:
        title = ""
        content_children: list[nodes.Node] = []
        for child in item.children:
            classes = (
                child.get("classes") or [] if isinstance(child, nodes.Element) else []
            )
            if isinstance(child, nodes.rubric) or "sd-tab-label" in classes:
                title = child.astext().strip()
                continue
            if isinstance(child, nodes.container) and "sd-tab-content" in classes:
                content_children.extend(child.children)
                continue
            content_children.append(child)
        body = self.render_docutils_nodes(content_children).strip("\n").strip()
        inner = body + "\n\n" if body else ""
        return f'<Tab title="{escape_attr(title)}">\n{inner}</Tab>\n'

    def _render_dropdown(self) -> str:
        title = sphinx_design_dropdown_title(self.node)
        body_children = sphinx_design_dropdown_body(self.node)
        body = self.render_docutils_nodes(body_children).strip("\n").strip()
        inner = body + "\n" if body else ""
        return f'<Accordion title="{escape_attr(title)}">\n{inner}</Accordion>\n\n'

    def _render_grid_row(self, classes: set[str]) -> str:
        cols = grid_cols_from_classes(classes)
        body = self.render_children()
        return f"<Columns cols={{{cols}}}>\n\n{body}</Columns>\n\n"
