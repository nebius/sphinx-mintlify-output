"""Admonitions (note / tip / warning / ...) and ``versionmodified`` blocks."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.components import (
    ADMONITION_TO_COMPONENT,
    CLASS_TO_COMPONENT,
)
from sphinx_mintlify_output.escaping import escape_attr, split_first_line
from sphinx_mintlify_output.nodes.base import TranslationNode


class AdmonitionNode(TranslationNode):
    """Wraps a docutils admonition into the matching Mintlify component.

    Mintlify-specific components (Check, Steps, Callout, ...) can be
    selected via the directive's ``:class:`` option — e.g.
    ``.. admonition:: X :class: steps`` renders as ``<Steps>``.
    """

    def render(self) -> str:
        component = self._component()
        if component == "Steps":
            return self._render_steps()
        attrs = self._attributes()
        attr_str = (" " + " ".join(attrs)) if attrs else ""
        body = self.render_children().strip("\n").strip()
        return f"<{component}{attr_str}>\n{body}\n</{component}>\n\n"

    def _classes(self) -> list[str]:
        if not isinstance(self.node, nodes.Element):
            return []
        return [c.lower() for c in (self.node.get("classes") or [])]

    def _component(self) -> str:
        kind = type(self.node).__name__
        overrides = self.ctx.builder.config.mintlify_component_map or {}
        component = overrides.get(kind) or ADMONITION_TO_COMPONENT.get(kind, "Note")
        for cls in self._classes():
            mapped = CLASS_TO_COMPONENT.get(cls)
            if mapped:
                return mapped
        return component

    def _attributes(self) -> list[str]:
        if not isinstance(self.node, nodes.Element):
            return []
        attrs: list[str] = []
        kind = type(self.node).__name__
        title = ""
        if kind == "admonition":
            for child in self.node.children:
                if isinstance(child, nodes.title):
                    title = child.astext().strip()
                    break
            if title.lower() in {"admonition title", ""}:
                title = ""
        if title:
            attrs.append(f'title="{escape_attr(title)}"')
        for cls in self._classes():
            if cls.startswith("icon-"):
                attrs.append(f'icon="{escape_attr(cls[len("icon-") :])}"')
            elif cls.startswith("color-"):
                attrs.append(f'color="{escape_attr(cls[len("color-") :])}"')
        return attrs

    def _render_steps(self) -> str:
        items: list[nodes.list_item] = []
        for child in self.node.findall(condition=nodes.list_item):
            items.append(child)
            if len(items) > 50:
                break
        if not items:
            return ""
        out = ["<Steps>\n"]
        for item in items:
            body = self.render_docutils_nodes(list(item.children)).strip("\n").strip()
            title, content = split_first_line(body)
            out.append(f'<Step title="{escape_attr(title)}">\n')
            if content:
                out.append(content + "\n")
            out.append("</Step>\n")
        out.append("</Steps>\n\n")
        return "".join(out)


class VersionModifiedNode(AdmonitionNode):
    """``.. versionadded::`` / ``versionchanged`` / ``deprecated`` blocks."""

    def _component(self) -> str:
        if not isinstance(self.node, nodes.Element):
            return "Info"
        kind = self.node.get("type", "versionchanged")
        return "Warning" if kind == "deprecated" else "Info"


class AdmonitionTitleNode(TranslationNode):
    """A ``title`` child inside an admonition — handled by the wrapping node."""

    def render(self) -> str:
        return ""
