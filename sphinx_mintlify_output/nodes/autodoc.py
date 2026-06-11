"""Autodoc desc / desc_signature / desc_content rendering.

Mirrors the existing legacy translator's autodoc layout: a top-level
class becomes a header + fenced Python signature + docstring prose +
``<ParamField>`` / ``<ResponseField>`` blocks, with attributes and
methods grouped under a ``<div className="pl-4 ml-1 my-4">`` block.
"""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.autodoc import (
    PARAM_DASH_SEPARATORS,
    build_clean_signature,
    desc_short_name,
    extract_param_info,
    format_desc_label,
    link_types_in_string,
    parse_param_head,
)
from sphinx_mintlify_output.components import CLASS_MEMBERS_CLOSE, CLASS_MEMBERS_OPEN
from sphinx_mintlify_output.escaping import escape_attr, escape_mdx_text
from sphinx_mintlify_output.nodes.base import TranslationNode


class DescNode(TranslationNode):
    """A ``desc`` node (class/function/method/property/attribute).

    Dispatches by ``desctype``:
    * ``property``/``attribute``/``data`` → :class:`ResponseField`-style block
    * ``class``/``exception`` at the top → header + signature + grouped
      members in a ``<div className="pl-4 ml-1 my-4">`` block
    * Everything else → header + signature + walked content body
    """

    def render(self) -> str:
        if not isinstance(self.node, nodes.Element):
            return ""
        desctype = self.node.get("desctype") or ""
        if desctype == "option":
            return _render_option_desc(self, self.node)
        if desctype in {"property", "attribute", "data"}:
            return _render_desc_as_field(self, self.node)
        if desctype in {"class", "exception"} and self.ctx.desc_depth == 0:
            return self._render_class()
        return self._render_default()

    def _render_default(self) -> str:
        params = extract_param_info(self.node)
        self.ctx.desc_param_stack.append(dict(params))
        self.ctx.desc_depth += 1
        try:
            return self.render_children()
        finally:
            self.ctx.desc_depth -= 1
            self.ctx.desc_param_stack.pop()

    def _render_class(self) -> str:
        from sphinx import addnodes

        signature: nodes.Element | None = None
        content: nodes.Element | None = None
        for child in self.node.children:
            if isinstance(child, addnodes.desc_signature):
                signature = child
            elif isinstance(child, addnodes.desc_content):
                content = child
        if signature is None:
            return ""

        params = extract_param_info(self.node)
        self.ctx.desc_param_stack.append(dict(params))
        self.ctx.desc_depth += 1
        try:
            out: list[str] = []
            out.append(
                TranslationNode.from_docutils(signature, self, self.ctx).render()
            )

            attributes: list[nodes.Element] = []
            methods: list[nodes.Element] = []
            prose: list[nodes.Node] = []
            field_list: nodes.Element | None = None
            if content is not None:
                for child in content.children:
                    if isinstance(child, addnodes.desc):
                        child_type = child.get("desctype") or ""
                        if child_type in {"property", "attribute", "data"}:
                            attributes.append(child)
                        else:
                            methods.append(child)
                    elif isinstance(child, nodes.field_list) and field_list is None:
                        field_list = child
                    else:
                        prose.append(child)
            out.append(self.render_docutils_nodes(prose))
            if field_list is not None:
                out.append(_render_autodoc_field_list(self, field_list))

            if attributes or methods:
                out.append(CLASS_MEMBERS_OPEN)
                if attributes:
                    out.append("### Attributes\n\n")
                    for member in attributes:
                        out.append(_render_desc_as_field(self, member))
                if methods:
                    out.append("### Methods\n\n")
                    # Bump depth so each method's heading lands at h4 to
                    # match the visual indentation under "Methods".
                    self.ctx.desc_depth += 1
                    try:
                        out.append(self.render_docutils_nodes(methods))
                    finally:
                        self.ctx.desc_depth -= 1
                out.append(CLASS_MEMBERS_CLOSE)
        finally:
            self.ctx.desc_depth -= 1
            self.ctx.desc_param_stack.pop()
        return "".join(out)


class DescSignatureNode(TranslationNode):
    """Emit anchor, heading, and the fenced Python signature for a desc."""

    def render(self) -> str:
        if not isinstance(self.node, nodes.Element):
            return ""
        out: list[str] = []
        if self.ctx.builder.config.mintlify_emit_anchors:
            ids = self.node.get("ids") or []
            for sid in ids:
                out.append(f'<a id="{sid}"></a>\n')
            if ids:
                out.append("\n")

        desctype = ""
        parent = self.node.parent
        if isinstance(parent, nodes.Element):
            desctype = parent.get("desctype") or ""
        short_name = desc_short_name(self.node)
        depth = max(self.ctx.desc_depth, 1)
        heading_prefix = "#" * min(2 + depth - 1, 6)
        label = format_desc_label(desctype, short_name)
        out.append(f"{heading_prefix} {label}\n\n")

        return_type = _lookup_return_type(self.node)
        clean_sig = build_clean_signature(self.node, desctype, short_name, return_type)
        if clean_sig:
            out.append(f"```python\n{clean_sig}\n```\n\n")
        return "".join(out)


class DescContentNode(TranslationNode):
    """Body of a desc — prose paragraphs + an autodoc-style field list."""

    def render(self) -> str:
        prose_children: list[nodes.Node] = []
        field_list: nodes.Element | None = None
        for child in self.node.children:
            if isinstance(child, nodes.field_list) and field_list is None:
                field_list = child
                continue
            prose_children.append(child)

        out: list[str] = []
        out.append(self.render_docutils_nodes(prose_children))
        if field_list is not None:
            out.append(_render_autodoc_field_list(self, field_list))
        return "".join(out)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _lookup_return_type(signature: nodes.Element) -> str:
    """Pull the documented ``:rtype:`` from the sibling desc_content."""
    parent = signature.parent
    if not isinstance(parent, nodes.Element):
        return ""
    from sphinx import addnodes

    for content in parent.children:
        if not isinstance(content, addnodes.desc_content):
            continue
        for field_list in content.findall(nodes.field_list):
            for field in field_list.children:
                if not isinstance(field, nodes.field):
                    continue
                name_node = next(
                    (c for c in field.children if isinstance(c, nodes.field_name)),
                    None,
                )
                if name_node is None:
                    continue
                if name_node.astext().strip().lower() in {"return type", "rtype"}:
                    body_node = next(
                        (c for c in field.children if isinstance(c, nodes.field_body)),
                        None,
                    )
                    if body_node is not None:
                        return body_node.astext().strip()
    return ""


def _render_desc_as_field(host: TranslationNode, node: nodes.Element) -> str:
    """Render an attribute/property/data desc as a ``<ResponseField>`` block."""
    from sphinx import addnodes

    signature: nodes.Element | None = None
    content: nodes.Element | None = None
    for child in node.children:
        if isinstance(child, addnodes.desc_signature):
            signature = child
        elif isinstance(child, addnodes.desc_content):
            content = child
    if signature is None:
        return ""

    short_name = desc_short_name(signature)
    type_str = ""
    for child in signature.children:
        if isinstance(child, addnodes.desc_annotation):
            text = child.astext()
            if text.startswith(": "):
                type_str = text[2:].strip()
                break

    out: list[str] = []
    if host.ctx.builder.config.mintlify_emit_anchors:
        for sid in signature.get("ids") or []:
            out.append(f'<a id="{sid}"></a>\n')

    body = ""
    if content is not None:
        body = host.render_docutils_nodes(list(content.children)).strip("\n").strip()

    attrs = [f'name="{escape_attr(short_name)}"']
    if type_str:
        attrs.append(f'type="{escape_attr(type_str)}"')
    body_parts: list[str] = []
    type_links = link_types_in_string(type_str, host.ctx.builder.env)
    if type_links and "](" in type_links:
        body_parts.append(type_links)
    if body:
        body_parts.append(body)
    body = "\n\n".join(body_parts)
    if body:
        out.append(f"<ResponseField {' '.join(attrs)}>\n")
        out.append(body + "\n")
        out.append("</ResponseField>\n\n")
    else:
        out.append(f"<ResponseField {' '.join(attrs)} />\n\n")
    return "".join(out)


def _render_option_desc(host: TranslationNode, node: nodes.Element) -> str:
    r"""Render a ``.. option::`` / ``cmdoption`` desc as a definition block.

    Sphinx's std-domain ``option`` directive produces a ``desc`` with the
    same shape as a Python autodoc entry (signature + content) but the
    Python-style ``## name`` plus ```` ```python ```` -fenced signature
    that :class:`DescSignatureNode` emits is wrong for CLI options. We
    render it as a ``<dl>``::

        <a id="cmdoption-mycli-f"></a>
        <a id="cmdoption-mycli-file"></a>
        <dl>
          <dt>`-f`, `--file FILE`</dt>
          <dd>Path to the input file.</dd>
        </dl>
    """
    from sphinx import addnodes

    signature: nodes.Element | None = None
    content: nodes.Element | None = None
    for child in node.children:
        if isinstance(child, addnodes.desc_signature):
            signature = child
        elif isinstance(child, addnodes.desc_content):
            content = child
    if signature is None:
        return ""

    out: list[str] = []
    if host.ctx.builder.config.mintlify_emit_anchors:
        for sid in signature.get("ids") or []:
            out.append(f'<a id="{sid}"></a>\n')

    label = _format_option_signature(signature)
    body = ""
    if content is not None:
        body = host.render_docutils_nodes(list(content.children)).strip("\n").strip()

    out.append("<dl>\n")
    out.append(f"  <dt>{label}</dt>\n")
    if body:
        out.append(f"  <dd>\n{body}\n  </dd>\n")
    else:
        out.append("  <dd></dd>\n")
    out.append("</dl>\n\n")
    return "".join(out)


def _format_option_signature(signature: nodes.Element) -> str:
    """Reconstruct the option signature as a comma-joined list of code spans.

    Walks ``desc_signature`` children, wrapping each ``desc_name`` in
    backticks and concatenating ``desc_addname`` text (which carries
    separators and the argument metavar) verbatim. Falls back to a single
    code span around ``signature.astext()`` if the children don't fit the
    expected pattern.
    """
    from sphinx import addnodes

    parts: list[str] = []
    for child in signature.children:
        if isinstance(child, addnodes.desc_name):
            text = child.astext().strip()
            if text:
                parts.append(f"`{text}`")
        elif isinstance(child, addnodes.desc_addname):
            text = child.astext()
            if text:
                parts.append(text)
    label = "".join(parts).strip()
    if not label:
        label = f"`{signature.astext().strip()}`"
    return label


# Field-list categorisation for autodoc fields.
_AUTODOC_PARAM_KEYS = ("parameters", "params", "args", "arguments")
_AUTODOC_RETURN_KEYS = ("returns", "return")
_AUTODOC_YIELD_KEYS = ("yields", "yield")
_AUTODOC_RAISES_KEYS = ("raises", "raise", "except", "exceptions")
_AUTODOC_RTYPE_KEYS = ("return type", "rtype")
_AUTODOC_YTYPE_KEYS = ("yield type", "ytype")
_AUTODOC_HANDLED = frozenset(
    {
        *_AUTODOC_PARAM_KEYS,
        *_AUTODOC_RETURN_KEYS,
        *_AUTODOC_YIELD_KEYS,
        *_AUTODOC_RAISES_KEYS,
        *_AUTODOC_RTYPE_KEYS,
        *_AUTODOC_YTYPE_KEYS,
    }
)


def _render_autodoc_field_list(host: TranslationNode, node: nodes.Element) -> str:
    """Translate ``:param:`` / ``:returns:`` / ``:raises:`` blocks into MDX."""
    fields: dict[str, nodes.field_body] = {}
    order: list[str] = []
    for fld in node.children:
        if not isinstance(fld, nodes.field):
            continue
        name_text = ""
        body: nodes.field_body | None = None
        for child in fld.children:
            if isinstance(child, nodes.field_name):
                name_text = child.astext().strip().lower()
            elif isinstance(child, nodes.field_body):
                body = child
        if body is None or not name_text:
            continue
        if name_text not in fields:
            order.append(name_text)
        fields[name_text] = body

    def first_body(keys: tuple[str, ...]) -> nodes.field_body | None:
        for k in keys:
            if k in fields:
                return fields[k]
        return None

    def first_text(keys: tuple[str, ...]) -> str:
        for k in keys:
            if k in fields:
                return fields[k].astext().strip()
        return ""

    params_field = first_body(_AUTODOC_PARAM_KEYS)
    returns_field = first_body(_AUTODOC_RETURN_KEYS)
    yields_field = first_body(_AUTODOC_YIELD_KEYS)
    raises_field = first_body(_AUTODOC_RAISES_KEYS)
    return_type = first_text(_AUTODOC_RTYPE_KEYS)
    yield_type = first_text(_AUTODOC_YTYPE_KEYS)

    out: list[str] = []
    if params_field is not None or host.ctx.current_desc_params():
        out.append(_render_param_fields(host, params_field))
    if returns_field is not None or return_type:
        out.append(_render_response_field(host, returns_field, "returns", return_type))
    if yields_field is not None or yield_type:
        out.append(_render_response_field(host, yields_field, "yields", yield_type))
    if raises_field is not None:
        out.append(_render_raises_field(host, raises_field))
    for key in order:
        if key in _AUTODOC_HANDLED:
            continue
        out.append(f"**{key.title()}:** {fields[key].astext().strip()}\n\n")
    return "".join(out)


def _render_param_fields(host: TranslationNode, body: nodes.field_body | None) -> str:
    documented: dict[str, tuple[str, str]] = {}
    extra_order: list[str] = []
    if body is not None:
        items: list[nodes.Element] = []
        for child in body.children:
            if isinstance(child, nodes.bullet_list):
                for li in child.children:
                    if isinstance(li, nodes.Element):
                        items.append(li)
            elif isinstance(child, nodes.paragraph):
                items.append(child)
        for item in items:
            name, type_str = parse_param_head(item)
            desc = _render_after_dash(host, item)
            key = name.lstrip("*")
            if key in documented:
                continue
            documented[key] = (type_str, desc)
            extra_order.append(key)

    out: list[str] = []
    seen: set[str] = set()
    for sig_name, info in host.ctx.current_desc_params().items():
        key = sig_name.lstrip("*")
        seen.add(key)
        doc_type, doc_desc = documented.get(key, ("", ""))
        type_str = doc_type or (info.get("type", "") if isinstance(info, dict) else "")
        default = info.get("default", "") if isinstance(info, dict) else ""
        required = (
            bool(info.get("required", False)) if isinstance(info, dict) else False
        )
        out.append(
            _render_one_param_field(
                host, sig_name, type_str, default, required, doc_desc
            )
        )
    for key in extra_order:
        if key in seen:
            continue
        doc_type, doc_desc = documented[key]
        out.append(_render_one_param_field(host, key, doc_type, "", False, doc_desc))
    return "".join(out)


def _render_one_param_field(
    host: TranslationNode,
    name: str,
    type_str: str,
    default: str,
    required: bool,
    description: str,
) -> str:
    attrs: list[str] = [f'path="{escape_attr(name)}"']
    if type_str:
        attrs.append(f'type="{escape_attr(type_str)}"')
    if required:
        attrs.append("required")
    elif default:
        attrs.append(f'default="{escape_attr(default)}"')
    body_parts: list[str] = []
    type_links = link_types_in_string(type_str, host.ctx.builder.env)
    if type_links and "](" in type_links:
        body_parts.append(type_links)
    if description and description.strip():
        body_parts.append(description.strip())
    body = "\n\n".join(body_parts)
    if body:
        return "<ParamField " + " ".join(attrs) + ">\n" + body + "\n</ParamField>\n\n"
    return "<ParamField " + " ".join(attrs) + " />\n\n"


def _render_response_field(
    host: TranslationNode,
    body: nodes.field_body | None,
    label: str,
    type_str: str = "",
) -> str:
    rendered = ""
    if body is not None:
        rendered = host.render_docutils_nodes(list(body.children)).strip("\n").strip()
    attrs = [f'name="{escape_attr(label)}"']
    if type_str:
        attrs.append(f'type="{escape_attr(type_str)}"')
    body_parts: list[str] = []
    type_links = link_types_in_string(type_str, host.ctx.builder.env)
    if type_links and "](" in type_links:
        body_parts.append(type_links)
    if rendered:
        body_parts.append(rendered)
    rendered = "\n\n".join(body_parts)
    if rendered:
        return (
            "<ResponseField "
            + " ".join(attrs)
            + ">\n"
            + rendered
            + "\n</ResponseField>\n\n"
        )
    return "<ResponseField " + " ".join(attrs) + " />\n\n"


def _render_raises_field(host: TranslationNode, body: nodes.field_body) -> str:
    items: list[nodes.Element] = []
    for child in body.children:
        if isinstance(child, nodes.bullet_list):
            for li in child.children:
                if isinstance(li, nodes.Element):
                    items.append(li)
        elif isinstance(child, nodes.paragraph):
            items.append(child)
    out: list[str] = []
    for item in items:
        text = host.render_docutils_nodes(list(item.children)).strip("\n").strip()
        if text:
            out.append('<ResponseField name="raises">\n')
            out.append(text + "\n")
            out.append("</ResponseField>\n\n")
        else:
            out.append('<ResponseField name="raises" />\n\n')
    return "".join(out)


def _render_after_dash(host: TranslationNode, item: nodes.Element) -> str:
    """Render the description portion of a param item, preserving refs."""
    paragraph: nodes.Element = item
    if isinstance(item, nodes.list_item):
        for child in item.children:
            if isinstance(child, nodes.paragraph):
                paragraph = child
                break
    children = list(paragraph.children)
    cut = -1
    for idx, child in enumerate(children):
        text = child.astext() if isinstance(child, nodes.Node) else ""
        if any(d in text for d in PARAM_DASH_SEPARATORS):
            cut = idx
            break
    if cut == -1:
        return ""
    boundary = children[cut].astext()
    tail = ""
    for d in PARAM_DASH_SEPARATORS:
        if d in boundary:
            tail = boundary.split(d, 1)[1]
            break
    parts: list[str] = []
    if tail:
        parts.append(escape_mdx_text(tail))
    parts.append(host.render_docutils_nodes(children[cut + 1 :]))
    return "".join(parts).strip("\n").strip()
