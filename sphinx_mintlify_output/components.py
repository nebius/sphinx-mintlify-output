"""Mappings and helpers for Mintlify components.

Includes the admonition → component lookup, sphinx-design container
helpers (``card``, ``tab-set``, ``dropdown``, grids), and small DOM
utilities used to extract titles, hrefs and body children from those
containers.
"""

from __future__ import annotations

from docutils import nodes

ADMONITION_TO_COMPONENT: dict[str, str] = {
    "note": "Note",
    "tip": "Tip",
    "hint": "Tip",
    "warning": "Warning",
    "attention": "Warning",
    "caution": "Warning",
    "important": "Info",
    "danger": "Danger",
    "error": "Danger",
    "admonition": "Note",
    "seealso": "Info",
}

CLASS_TO_COMPONENT: dict[str, str] = {
    "note": "Note",
    "tip": "Tip",
    "info": "Info",
    "warning": "Warning",
    "danger": "Danger",
    "error": "Danger",
    "check": "Check",
    "success": "Check",
    "ok": "Check",
    "callout": "Callout",
    "steps": "Steps",
}

CLASS_MEMBERS_OPEN = '<div className="pl-4 ml-1 my-4">\n\n'
CLASS_MEMBERS_CLOSE = "</div>\n\n"


def grid_cols_from_classes(classes: set[str]) -> int:
    """Pick the most specific ``sd-row-cols-*`` value from a class set."""
    for breakpoint in ("xxl", "xl", "lg", "md", "sm"):
        for cls in classes:
            prefix = f"sd-row-cols-{breakpoint}-"
            if cls.startswith(prefix):
                try:
                    return int(cls[len(prefix) :])
                except ValueError:
                    continue
    for cls in classes:
        if cls.startswith("sd-row-cols-"):
            tail = cls[len("sd-row-cols-") :]
            if tail.isdigit():
                return int(tail)
    return 2


def tab_item_title(node: nodes.container) -> str:
    for child in node.children:
        if isinstance(child, nodes.Element):
            classes = child.get("classes") or []
            if isinstance(child, nodes.rubric) or "sd-tab-label" in classes:
                return str(child.astext()).strip()
    return ""


def tab_item_content(node: nodes.container) -> list[nodes.Node]:
    for child in node.children:
        if isinstance(child, nodes.container) and "sd-tab-content" in (
            child.get("classes") or []
        ):
            return list(child.children)
    return []


def tab_item_is_code_only(node: nodes.container) -> bool:
    content = tab_item_content(node)
    if not content:
        return False
    meaningful = [
        c for c in content if not (isinstance(c, nodes.Text) and not str(c).strip())
    ]
    return len(meaningful) == 1 and isinstance(meaningful[0], nodes.literal_block)


def tab_item_code(node: nodes.container) -> tuple[str, str]:
    for child in tab_item_content(node):
        if isinstance(child, nodes.literal_block):
            language = child.get("language") or ""
            if language in {"default", "none"}:
                language = ""
            return child.astext().rstrip("\n"), language
    return "", ""


def sphinx_design_card_title(node: nodes.container) -> str:
    for descendant in node.findall(condition=nodes.Element):
        if descendant.get("design_component") == "card-title":
            return descendant.astext().strip()
        classes = descendant.get("classes") or []
        if "sd-card-header" in classes or "sd-card-title" in classes:
            return descendant.astext().strip()
    return ""


def sphinx_design_card_href(node: nodes.container) -> str:
    for ref in node.findall(nodes.reference):
        return str(ref.get("refuri") or "")
    return ""


def sphinx_design_card_body(node: nodes.container) -> list[nodes.Node]:
    body: list[nodes.Node] = []
    body_container: nodes.Element | None = None
    for descendant in node.findall(condition=nodes.Element):
        if descendant.get("design_component") == "card-body":
            body_container = descendant
            break
    if body_container is None:
        body_container = node
    for child in body_container.children:
        if isinstance(child, nodes.Element):
            comp = child.get("design_component") or ""
            classes = child.get("classes") or []
            if comp in {"card-title", "card-header", "card-footer"}:
                continue
            if (
                "sd-card-title" in classes
                or "sd-card-header" in classes
                or "sd-card-footer" in classes
            ):
                continue
        body.append(child)
    return body


def sphinx_design_dropdown_title(node: nodes.container) -> str:
    for child in node.children:
        if isinstance(child, nodes.rubric):
            return child.astext().strip()
        classes = child.get("classes") or [] if isinstance(child, nodes.Element) else []
        if "sd-summary-title" in classes or "sd-card-header" in classes:
            return child.astext().strip()
    return ""


def sphinx_design_dropdown_body(node: nodes.container) -> list[nodes.Node]:
    body: list[nodes.Node] = []
    for child in node.children:
        if isinstance(child, nodes.rubric):
            continue
        classes = child.get("classes") or [] if isinstance(child, nodes.Element) else []
        if "sd-summary-title" in classes or "sd-card-header" in classes:
            continue
        if isinstance(child, nodes.container) and (
            "sd-summary-content" in classes or "sd-card-body" in classes
        ):
            body.extend(child.children)
            continue
        body.append(child)
    return body
