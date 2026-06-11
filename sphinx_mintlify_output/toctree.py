"""Document title/summary lookup helpers.

Single source of truth for "what is page X's title?" and "does it have
a summary?" — used both when rendering toctree directives as card
groups and when building ``docs.json`` navigation.
"""

from __future__ import annotations

from typing import Any


def doc_title(env: Any, docname: str) -> str | None:
    """Return the raw title text for ``docname``, or ``None`` if unset."""
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
