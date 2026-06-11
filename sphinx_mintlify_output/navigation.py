"""Generate Mintlify docs.json from a Sphinx toctree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from docutils import nodes
from sphinx.addnodes import toctree
from sphinx.util import logging

from sphinx_mintlify_output.toctree import doc_title

if TYPE_CHECKING:
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)

# Hard cap on how deeply nested a resolved toctree we'll walk before
# bailing out. Real Sphinx projects rarely exceed 5-6 levels; this
# guard exists to keep a pathological project from blowing the Python
# recursion limit. The ``visited`` set already prevents cycles, so this
# only fires on genuinely deep nesting.
_MAX_TOCTREE_DEPTH = 32


def build_docs_json(env: BuildEnvironment, config: Config) -> dict[str, Any]:
    """Build a Mintlify docs.json structure from the resolved toctree."""

    master_doc = config.master_doc
    groups: list[dict[str, Any]] = []
    pages: list[Any] = []
    visited: set[str] = set()

    if master_doc in env.tocs:
        collect_toctree_entries(
            env, env.tocs[master_doc], groups, pages, visited, depth=0
        )

    navigation: dict[str, Any] = {}
    promoted = [p for p in pages if isinstance(p, dict) and "group" in p]
    bare_pages = [p for p in pages if not (isinstance(p, dict) and "group" in p)]
    combined_groups = groups + promoted
    if combined_groups and not bare_pages:
        navigation["groups"] = combined_groups
    elif bare_pages and not combined_groups:
        navigation["pages"] = bare_pages
    elif combined_groups and bare_pages:
        navigation["pages"] = [*bare_pages, *combined_groups]

    project_name = getattr(config, "project", "Documentation")
    result: dict[str, Any] = {
        "$schema": "https://mintlify.com/docs.json",
        "theme": "mint",
        "name": project_name,
        "navigation": navigation,
    }

    user_extra = dict(config.mintlify_docs_json or {})
    user_nav = user_extra.pop("navigation", None)
    result.update(user_extra)
    if user_nav is not None:
        result["navigation"] = user_nav
    return result


def collect_toctree_entries(
    env: BuildEnvironment,
    node: nodes.Element,
    groups: list[dict[str, Any]],
    pages: list[Any],
    visited: set[str],
    depth: int,
) -> None:
    if depth >= _MAX_TOCTREE_DEPTH:
        logger.warning(
            "toctree depth exceeds %d levels at %r; truncating navigation",
            _MAX_TOCTREE_DEPTH,
            node.source or "<unknown>",
        )
        return
    for child in node.children:
        if isinstance(child, toctree):
            handle_toctree(env, child, groups, pages, visited, depth=depth)
        elif isinstance(child, nodes.Element):
            collect_toctree_entries(env, child, groups, pages, visited, depth=depth)


def handle_toctree(
    env: BuildEnvironment,
    node: toctree,
    groups: list[dict[str, Any]],
    pages: list[Any],
    visited: set[str],
    depth: int,
) -> None:
    caption = node.get("caption")
    entries = node.get("entries") or []
    group_pages: list[Any] = []
    for _title, docname in entries:
        if not docname:
            continue
        if docname in visited:
            continue
        visited.add(docname)
        page_entry = page_for_doc(env, docname, visited, depth=depth + 1)
        group_pages.append(page_entry)
    if caption:
        groups.append({"group": caption, "pages": group_pages})
    else:
        pages.extend(group_pages)


def page_for_doc(
    env: BuildEnvironment,
    docname: str,
    visited: set[str],
    depth: int,
) -> Any:
    sub_groups: list[dict[str, Any]] = []
    sub_pages: list[Any] = []
    if docname in env.tocs:
        collect_toctree_entries(
            env, env.tocs[docname], sub_groups, sub_pages, visited, depth=depth
        )
    if not sub_groups and not sub_pages:
        return docname
    title = doc_title(env, docname) or docname
    if sub_groups and not sub_pages:
        return {"group": title, "pages": [docname, *sub_groups]}
    if sub_pages and not sub_groups:
        return {"group": title, "pages": [docname, *sub_pages]}
    return {"group": title, "pages": [docname, *sub_pages, *sub_groups]}
