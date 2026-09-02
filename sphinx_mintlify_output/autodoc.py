"""Helpers for rendering Sphinx ``desc`` (autodoc) nodes as MDX.

Covers:

* Signature reconstruction (:func:`build_clean_signature`,
  :func:`decorate_signature`), styled per Sphinx domain via
  :class:`SignatureStyle` / :data:`SIGNATURE_STYLES`.
* Heading and label formatting (:func:`format_desc_label`).
* Parameter parsing for ``Parameters`` field lists
  (:func:`parse_param_item`, :func:`parse_param_head`,
  :func:`extract_param_info`).
* Type-aware cross-referencing of strings like ``list[int] | None``
  (:func:`link_types_in_string`, :func:`lookup_python_object`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from docutils import nodes

from sphinx_mintlify_output.state import ParamInfo
from sphinx_mintlify_output.urls import url_for


@dataclass(frozen=True)
class SignatureStyle:
    """Per-domain rendering rules for ``desc`` signatures.

    ``async_kw`` is a plain prefix composed with the declaration keyword
    (``async `` + ``def `` for Python, ``async `` + ``function `` for JS);
    an empty string drops the async marker for domains without one.
    ``returns`` is a format string receiving the return type as ``{t}``.
    """

    fence: str
    function_kw: str = ""
    method_kw: str = ""
    async_kw: str = ""
    class_kw: str = ""
    returns: str = ""
    py_decorators: bool = False


PYTHON_STYLE = SignatureStyle(
    fence="python",
    function_kw="def ",
    method_kw="def ",
    async_kw="async ",
    class_kw="class ",
    returns=" -> {t}",
    py_decorators=True,
)

FALLBACK_STYLE = SignatureStyle(fence="text")

# ``ts`` fence for the js domain on purpose: generics
# (``Promise<FileResponse>``) and optional params (``options?``) only
# highlight correctly in the TypeScript lexer.
SIGNATURE_STYLES: dict[str, SignatureStyle] = {
    "py": PYTHON_STYLE,
    "js": SignatureStyle(
        fence="ts",
        function_kw="function ",
        async_kw="async ",
        class_kw="class ",
        returns=": {t}",
    ),
    "ts": SignatureStyle(
        fence="ts",
        function_kw="function ",
        async_kw="async ",
        class_kw="class ",
        returns=": {t}",
    ),
    # C/C++/C# signatures already carry parameter and return types —
    # no prefixes or suffixes, just the right fence.
    "c": SignatureStyle(fence="c"),
    "cpp": SignatureStyle(fence="cpp", class_kw="class "),
    "cs": SignatureStyle(fence="csharp", async_kw="async ", class_kw="class "),
    "go": SignatureStyle(
        fence="go",
        function_kw="func ",
        method_kw="func ",
        class_kw="type ",
        returns=" {t}",
    ),
    "rs": SignatureStyle(
        fence="rust",
        function_kw="fn ",
        method_kw="fn ",
        async_kw="async ",
        class_kw="struct ",
        returns=" -> {t}",
    ),
    "rb": SignatureStyle(fence="ruby", function_kw="def ", method_kw="def "),
    "php": SignatureStyle(
        fence="php",
        function_kw="function ",
        method_kw="function ",
        returns=": {t}",
    ),
    "lua": SignatureStyle(fence="lua", function_kw="function ", method_kw="function "),
    "std": FALLBACK_STYLE,
}


def signature_style(domain: str) -> SignatureStyle:
    """Look up the :class:`SignatureStyle` for a Sphinx domain name.

    An empty domain means a synthetic/legacy node — treated as Python to
    preserve historical output; unknown domains fall back to a bare
    ``text`` fence.
    """
    return SIGNATURE_STYLES.get(domain or "py", FALLBACK_STYLE)


def desc_short_name(signature: nodes.Element) -> str:
    """Return the leaf name of a desc_signature (last ``desc_name`` found)."""
    from sphinx import addnodes

    short = ""
    for descendant in signature.findall(condition=addnodes.desc_name):
        short = descendant.astext().strip()
    return short


def decorate_signature(
    sig: str,
    desctype: str,
    return_type: str = "",
    style: SignatureStyle = PYTHON_STYLE,
) -> str:
    """Massage a captured desc signature into a domain-styled declaration."""
    sig = sig.strip()
    if not style.py_decorators:
        return decorate_foreign_signature(sig, desctype, return_type, style)
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


def decorate_foreign_signature(
    sig: str,
    desctype: str,
    return_type: str,
    style: SignatureStyle,
) -> str:
    """Prefix a non-Python signature per its domain style.

    The captured signature text is kept as-is (domains like C/C++ already
    embed parameter and return types); only the declaration keyword, the
    async marker, and the documented return type are layered on top —
    and only when the style defines them.
    """
    sig = sig.strip()
    is_async = False
    if sig.startswith("async "):
        is_async = True
        sig = sig[len("async ") :].lstrip()
    is_class = desctype in {"class", "exception"}
    if is_class:
        keyword = style.class_kw
    elif desctype == "function":
        keyword = style.function_kw
    elif desctype in {"method", "staticmethod", "classmethod"}:
        keyword = style.method_kw
    else:
        keyword = ""
    if keyword and not sig.startswith(keyword):
        sig = keyword + sig
    if is_async and style.async_kw:
        sig = style.async_kw + sig
    if return_type and style.returns and not is_class:
        suffix = style.returns.format(t=return_type)
        if not sig.endswith(suffix):
            sig = sig + suffix
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


def desc_annotation_type(signature: nodes.Element) -> str:
    """Return the type from a Python attribute signature annotation."""
    from sphinx import addnodes

    for child in signature.children:
        if not isinstance(child, addnodes.desc_annotation):
            continue
        text = str(child.astext()).strip()
        if text.startswith(":"):
            return text[1:].strip()
    return ""


def _collect_class_attributes(signature: nodes.Element) -> list[tuple[str, str]]:
    """Collect direct class attributes as ``(name, type)`` pairs."""
    from sphinx import addnodes

    parent = signature.parent
    if not isinstance(parent, nodes.Element):
        return []
    attributes: list[tuple[str, str]] = []
    for content in parent.children:
        if not isinstance(content, addnodes.desc_content):
            continue
        for member in content.children:
            if not isinstance(member, addnodes.desc):
                continue
            if member.get("desctype") not in {"attribute", "data"}:
                continue
            member_signature = next(
                (
                    child
                    for child in member.children
                    if isinstance(child, addnodes.desc_signature)
                ),
                None,
            )
            if member_signature is None:
                continue
            name = desc_short_name(member_signature)
            if name:
                attributes.append((name, desc_annotation_type(member_signature)))
        break
    return attributes


def _build_python_class_signature(
    full_name: str,
    param_names: list[str],
    attributes: list[tuple[str, str]],
) -> str:
    header = _build_class_signature("class", full_name, param_names) + ":"
    if not attributes:
        return f"{header}\n    ..."
    declarations = [
        f"    {name}: {type_str}" if type_str else f"    {name} = ..."
        for name, type_str in attributes
    ]
    return "\n".join([header, *declarations])


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


def _python_module_name(
    signature: nodes.Element,
    full_name: str,
    short_name: str,
) -> str:
    """Return the importable module for a qualified Python object."""
    module_name = str(signature.get("module") or "").strip()
    if module_name:
        return module_name
    display_module, separator, object_name = full_name.rpartition(".")
    if separator and object_name == short_name:
        return display_module
    return ""


def _prepend_python_import(module_name: str, name: str, declaration: str) -> str:
    return f"from {module_name} import {name}\n\n\n{declaration}"


def build_clean_signature(
    signature: nodes.Element,
    desctype: str,
    short_name: str,
    return_type: str = "",
    style: SignatureStyle = PYTHON_STYLE,
) -> str:
    """Reconstruct a domain-styled signature for a ``desc_signature``.

    Python keeps the historical parameter-name-only reconstruction with
    ``@classmethod``/``@staticmethod``/``@property`` decorators. Other
    domains keep the signature text Sphinx produced (types included) and
    only get keyword/async/return decoration per their style.
    """
    if not style.py_decorators:
        text = " ".join(signature.astext().split())
        return decorate_foreign_signature(text, desctype, return_type, style)

    full_name, annotation, has_paramlist, inline_return = _collect_signature_metadata(
        signature, short_name
    )
    if inline_return and not return_type:
        return_type = inline_return
    param_names = _collect_param_names(signature) if has_paramlist else []

    module_name = _python_module_name(signature, full_name, short_name)

    if desctype in {"class", "exception"}:
        class_name = short_name if module_name else full_name
        class_sig = _build_python_class_signature(
            class_name,
            param_names,
            _collect_class_attributes(signature),
        )
        if module_name:
            return f"from {module_name} import {short_name}\n\n{class_sig}"
        return class_sig
    if desctype == "function":
        if module_name:
            callable_sig = _build_callable_signature(
                desctype, short_name, annotation, param_names, return_type
            )
            return _prepend_python_import(module_name, short_name, callable_sig)
        return _build_callable_signature(
            desctype, full_name, annotation, param_names, return_type
        )
    if desctype in {"method", "staticmethod", "classmethod"}:
        return _build_callable_signature(
            desctype, full_name, annotation, param_names, return_type
        )
    if desctype == "property":
        return _build_property_signature(full_name, return_type)
    return full_name


def format_desc_label(
    desctype: str,
    short_name: str,
    style: SignatureStyle = PYTHON_STYLE,
) -> str:
    """Return the heading label for a desc node, with type prefix when useful."""
    if not short_name:
        return desctype or "object"
    if desctype == "class":
        return f"`class {short_name}`"
    if desctype == "exception" and style.py_decorators:
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


def link_types_in_string(type_str: str, from_doc: str, env: Any) -> str:
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
        href = url_for(from_doc, docname)
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
