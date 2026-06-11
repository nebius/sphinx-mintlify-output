"""Helpers for rendering Sphinx ``desc`` (autodoc) nodes as MDX.

Covers:

* Signature reconstruction (:func:`build_clean_signature`,
  :func:`decorate_signature`).
* Heading and label formatting (:func:`format_desc_label`).
* Parameter parsing for ``Parameters`` field lists
  (:func:`parse_param_item`, :func:`parse_param_head`,
  :func:`extract_param_info`).
* Type-aware cross-referencing of strings like ``list[int] | None``
  (:func:`link_types_in_string`, :func:`lookup_python_object`).
"""

from __future__ import annotations

import re
from typing import Any

from docutils import nodes

from sphinx_mintlify_output.state import ParamInfo


def desc_short_name(signature: nodes.Element) -> str:
    """Return the leaf name of a desc_signature (last ``desc_name`` found)."""
    from sphinx import addnodes

    short = ""
    for descendant in signature.findall(condition=addnodes.desc_name):
        short = descendant.astext().strip()
    return short


def decorate_signature(sig: str, desctype: str, return_type: str = "") -> str:
    """Massage a captured desc signature into a Python-like declaration."""
    sig = sig.strip()
    if desctype in {"function", "method", "staticmethod", "classmethod"}:
        if sig.startswith("async "):
            sig = "async def " + sig[len("async ") :]
        elif sig.startswith("classmethod "):
            sig = "@classmethod def " + sig[len("classmethod ") :]
        elif sig.startswith("staticmethod "):
            sig = "@staticmethod def " + sig[len("staticmethod ") :]
        elif sig.startswith("abstractmethod "):
            sig = "@abstractmethod def " + sig[len("abstractmethod ") :]
        else:
            sig = "def " + sig
        if return_type and " -> " not in sig:
            sig = f"{sig} -> {return_type}"
    return sig


def _collect_signature_metadata(
    signature: nodes.Element,
    short_name: str,
) -> tuple[str, str, bool, str]:
    """Pull (full_name, annotation, has_paramlist, inline_return) from a sig."""
    from sphinx import addnodes

    full_name = short_name
    annotation = ""
    has_paramlist = False
    inline_return = ""
    for child in signature.children:
        if isinstance(child, addnodes.desc_addname):
            full_name = child.astext().strip() + short_name
        elif isinstance(child, addnodes.desc_annotation):
            text = child.astext()
            if text.startswith(": "):
                continue
            annotation = text.strip()
        elif isinstance(child, addnodes.desc_parameterlist):
            has_paramlist = True
        elif isinstance(child, addnodes.desc_returns):
            text = child.astext().strip()
            if text.startswith("->"):
                text = text[2:].strip()
            elif text.startswith("→"):
                text = text[1:].strip()
            inline_return = text
    return full_name, annotation, has_paramlist, inline_return


def _collect_param_names(signature: nodes.Element) -> list[str]:
    """Extract parameter names from the first parameterlist of ``signature``."""
    from sphinx import addnodes

    param_names: list[str] = []
    for plist in signature.findall(condition=addnodes.desc_parameterlist):
        for param in plist.findall(condition=addnodes.desc_parameter):
            text = param.astext().strip()
            if text in {"/", "*"}:
                param_names.append(text)
                continue
            match = SIGNATURE_PARAM_RE.match(text)
            if match:
                param_names.append(match.group("name"))
            else:
                param_names.append(text.split(":", 1)[0].split("=", 1)[0])
        break
    return param_names


def _build_class_signature(
    desctype: str, full_name: str, param_names: list[str]
) -> str:
    return f"{desctype} {full_name}({', '.join(param_names)})"


def _build_callable_signature(
    desctype: str,
    full_name: str,
    annotation: str,
    param_names: list[str],
    return_type: str,
) -> str:
    prefix = ""
    async_kw = ""
    if annotation == "async":
        async_kw = "async "
    elif annotation == "classmethod":
        prefix = "@classmethod\n"
    elif annotation == "staticmethod":
        prefix = "@staticmethod\n"
    elif annotation == "abstractmethod":
        prefix = "@abstractmethod\n"
    if desctype == "classmethod" and "@classmethod" not in prefix:
        prefix = "@classmethod\n"
    elif desctype == "staticmethod" and "@staticmethod" not in prefix:
        prefix = "@staticmethod\n"
    body = f"{async_kw}def {full_name}({', '.join(param_names)})"
    if return_type:
        body = f"{body} -> {return_type}"
    return prefix + body


def _build_property_signature(full_name: str, return_type: str) -> str:
    body = f"@property\ndef {full_name}()"
    if return_type:
        body = f"{body} -> {return_type}"
    return body


def build_clean_signature(
    signature: nodes.Element,
    desctype: str,
    short_name: str,
    return_type: str = "",
) -> str:
    """Reconstruct a parameter-name-only signature with decorators."""
    full_name, annotation, has_paramlist, inline_return = _collect_signature_metadata(
        signature, short_name
    )
    if inline_return and not return_type:
        return_type = inline_return
    param_names = _collect_param_names(signature) if has_paramlist else []

    if desctype in {"class", "exception"}:
        return _build_class_signature(desctype, full_name, param_names)
    if desctype in {"function", "method", "staticmethod", "classmethod"}:
        return _build_callable_signature(
            desctype, full_name, annotation, param_names, return_type
        )
    if desctype == "property":
        return _build_property_signature(full_name, return_type)
    return full_name


def format_desc_label(desctype: str, short_name: str) -> str:
    """Return the heading label for a desc node, with type prefix when useful."""
    if not short_name:
        return desctype or "object"
    if desctype == "class":
        return f"`class {short_name}`"
    if desctype == "exception":
        return f"`exception {short_name}`"
    if desctype in {"function", "method", "staticmethod", "classmethod"}:
        return f"`{short_name}()`"
    return f"`{short_name}`"


# Matches a single token from a Sphinx ``desc_parameterlist`` —
# ``name``, ``name: type``, ``name = default``, ``name: type = default``,
# ``*args`` / ``**kwargs``.
SIGNATURE_PARAM_RE = re.compile(
    r"^(?P<name>\*{0,2}\w+)"
    r"\s*(?::\s*(?P<type>[^=]+?))?"
    r"\s*(?:=\s*(?P<default>.+))?$",
    re.DOTALL,
)


def extract_param_info(desc_node: nodes.Element) -> dict[str, ParamInfo]:
    """Pull per-parameter type/default/required info from a desc node."""
    from sphinx import addnodes

    info: dict[str, ParamInfo] = {}
    for plist in desc_node.findall(condition=addnodes.desc_parameterlist):
        for param in plist.findall(condition=addnodes.desc_parameter):
            text = param.astext().strip()
            if text in {"/", "*"}:
                continue
            match = SIGNATURE_PARAM_RE.match(text)
            if match is None:
                continue
            name = (match.group("name") or "").strip()
            if not name:
                continue
            type_str = (match.group("type") or "").strip()
            default = (match.group("default") or "").strip()
            is_varargs = name.startswith("*")
            info[name] = {
                "type": type_str,
                "default": default,
                "required": not default and not is_varargs,
            }
        break
    return info


EN_DASH = chr(0x2013)
EM_DASH = chr(0x2014)
PARAM_DASH_SEPARATORS = (f" {EN_DASH} ", f" {EM_DASH} ", " -- ")
PARAM_DASH_CLASS = "[-" + EN_DASH + EM_DASH + "]+"
# Matches one rendered docstring param line — ``name(type) -- description``
# or any of the dash variants. Used by :func:`parse_param_item` to peel
# ``:param X: text`` items rendered by Sphinx into the body field list.
DOCSTRING_PARAM_RE = re.compile(
    "^\\s*(?P<name>\\S+?)\\s*(?:\\((?P<type>[^)]*)\\))?\\s*"
    + PARAM_DASH_CLASS
    + "\\s*(?P<desc>.*)$",
    re.DOTALL,
)


TYPE_TOKEN_RE = re.compile(r"([A-Za-z_][\w.]*)")


def lookup_python_object(env: Any, name: str) -> tuple[str, str] | None:
    """Find a Python-domain class/exception/function by short or full name.

    Returns ``(docname, anchor)`` or ``None`` when nothing matches.
    """
    try:
        domain = env.get_domain("py")
    except Exception:
        return None
    objects = getattr(domain, "objects", None)
    if not objects:
        return None
    entry = objects.get(name)
    if entry is not None:
        objtype = getattr(entry, "objtype", "")
        if objtype in {"class", "exception", "function", "method"}:
            return getattr(entry, "docname", ""), getattr(entry, "node_id", "")
    suffix = "." + name
    for fullname, found in objects.items():
        if fullname == name or fullname.endswith(suffix):
            objtype = getattr(found, "objtype", "")
            if objtype in {"class", "exception", "function", "method"}:
                return getattr(found, "docname", ""), getattr(found, "node_id", "")
    return None


def link_types_in_string(type_str: str, env: Any) -> str:
    """Wrap recognised class names inside a type expression with markdown links."""
    if not type_str:
        return ""

    def replace(match: re.Match[str]) -> str:
        token = match.group(1)
        if token in BUILTIN_TYPE_NAMES:
            return token
        ref = lookup_python_object(env, token)
        if ref is None:
            return token
        docname, anchor = ref
        href = "/" + docname
        if anchor:
            href = href + "#" + anchor
        return f"[`{token}`]({href})"

    return TYPE_TOKEN_RE.sub(replace, type_str)


BUILTIN_TYPE_NAMES: frozenset[str] = frozenset(
    {
        "Any",
        "Awaitable",
        "Callable",
        "ClassVar",
        "Dict",
        "Final",
        "Generator",
        "Iterable",
        "Iterator",
        "List",
        "Literal",
        "Mapping",
        "None",
        "Optional",
        "Path",
        "PurePosixPath",
        "Sequence",
        "Set",
        "Tuple",
        "Type",
        "TypeVar",
        "Union",
        "UUID",
        "bool",
        "bytes",
        "datetime",
        "dict",
        "float",
        "frozenset",
        "int",
        "list",
        "object",
        "set",
        "str",
        "timedelta",
        "tuple",
        "type",
    }
)


def parse_param_item(item: nodes.Element) -> tuple[str, str, str]:
    """Extract (name, type, description) from a Sphinx autodoc param item."""
    text = item.astext().strip()
    match = DOCSTRING_PARAM_RE.match(text)
    if match:
        return (
            match.group("name"),
            (match.group("type") or "").strip(),
            (match.group("desc") or "").strip(),
        )
    parts = text.split(None, 1)
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return text, "", ""


def parse_param_head(item: nodes.Element) -> tuple[str, str]:
    """Extract only (name, type) from a Sphinx autodoc param item."""
    name, type_str, _ = parse_param_item(item)
    return name, type_str
