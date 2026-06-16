"""Document title/summary lookup helpers.

Single source of truth for "what is page X's title?" and "does it have
a summary?" — used both when rendering toctree directives as card
groups and when building ``docs.json`` navigation.
"""

from __future__ import annotations

import posixpath
from typing import Any

from sphinx_mintlify_output.urls import base_path


def doc_title(env: Any, docname: str) -> str | None:
    """Return the raw title text for ``docname``, or ``None`` if unset."""
    metadata = getattr(env, "metadata", {}) or {}
    meta = metadata.get(docname) or {}
    if "title" in meta:
        return str(meta["title"]).strip() or None

    titles = getattr(env, "titles", {}) or {}
    node = titles.get(docname)
    if node is None:
        return None
    text = str(node.astext()).strip()
    return text or None


def doc_title_or_slug(env: Any, docname: str) -> str:
    """Return the page title, falling back to a humanised slug.

    Used for toctree card labels where we always need a human-readable
    string, even for docs with no title node yet (e.g. partial builds).
    """
    title = doc_title(env, docname)
    if title:
        return title
    return docname.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").title()


def doc_summary(env: Any, docname: str) -> str:
    """Return the page's ``description``/``summary`` metadata, or ``""``."""
    metadata = getattr(env, "metadata", {}) or {}
    meta = metadata.get(docname) or {}
    description = (meta.get("description") or meta.get("summary") or "").strip()
    return description


def doc_icon(env: Any, docname: str) -> str:
    """Return the page's ``icon`` metadata, or ``""``."""
    metadata = getattr(env, "metadata", {}) or {}
    meta = metadata.get(docname) or {}
    return str(meta.get("icon", "")).strip()


def docname_from_refuri(from_doc: str, refuri: str) -> str | None:
    """Map a resolved toctree ``refuri`` back to a Sphinx docname."""
    if not refuri:
        return None
    if refuri.startswith(("#", "mailto:", "tel:")):
        return None
    if refuri.startswith(("http://", "https://")):
        return None
    path, _sep, _fragment = refuri.partition("#")
    mount = base_path.get()
    if path.startswith("/"):
        if mount is not None:
            prefix = str(mount).rstrip("/")
            if path.startswith(prefix + "/"):
                path = path[len(prefix) + 1 :]
            elif path.startswith(prefix):
                path = path[len(prefix) :].lstrip("/")
        else:
            path = path.lstrip("/")
    else:
        from_dir = posixpath.dirname(from_doc)
        path = posixpath.normpath(posixpath.join(from_dir, path))
    return path or None
