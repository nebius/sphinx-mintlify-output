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
            env, env.tocs[master_doc], groups, pages, visited, master_doc, depth=0
        )

    promoted = [p for p in pages if isinstance(p, dict) and "group" in p]
    bare_pages = [p for p in pages if not (isinstance(p, dict) and "group" in p)]
    nav_pages = (
        [master_doc, *bare_pages, *groups, *promoted]
        if master_doc
        else [
            *bare_pages,
            *groups,
            *promoted,
        ]
    )
    navigation: dict[str, Any] = {}
    if nav_pages:
        navigation["pages"] = nav_pages

    project_name = getattr(config, "project", "Documentation")
    # Mintlify's docs.json schema requires `colors` (with at least a
    # `primary` value) and `name`/`navigation`. Provide neutral defaults
    # so `mintlify dev` accepts the build out of the box; user overrides
    # from `mintlify_docs_json` take precedence below.
    result: dict[str, Any] = {
        "$schema": "https://mintlify.com/docs.json",
        "theme": "mint",
        "name": project_name,
        "colors": {"primary": "#0d9373"},
        "navigation": navigation,
    }

    user_extra = dict(config.mintlify_docs_json or {})
    user_nav = user_extra.pop("navigation", None)
    user_colors = user_extra.pop("colors", None)
    result.update(user_extra)
    if user_colors is not None:
        # Merge so a user supplying only e.g. `{"primary": "#abc"}` still
        # keeps any other defaults rather than wiping the section.
        merged_colors = dict(result["colors"])
        merged_colors.update(user_colors)
        result["colors"] = merged_colors
    if user_nav is not None:
        result["navigation"] = user_nav
    return result


def collect_toctree_entries(
    env: BuildEnvironment,
    node: nodes.Element,
    groups: list[dict[str, Any]],
    pages: list[Any],
    visited: set[str],
    master_doc: str,
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
            handle_toctree(env, child, groups, pages, visited, master_doc, depth=depth)
        elif isinstance(child, nodes.Element):
            collect_toctree_entries(
                env, child, groups, pages, visited, master_doc, depth=depth
            )


def handle_toctree(
    env: BuildEnvironment,
    node: toctree,
    groups: list[dict[str, Any]],
    pages: list[Any],
    visited: set[str],
    master_doc: str,
    depth: int,
) -> None:
    caption = node.get("caption")
    entries = node.get("entries") or []
    group_pages: list[Any] = []
    for _title, docname in entries:
        if not docname or docname == master_doc:
            continue
        if docname in visited:
            continue
        visited.add(docname)
        page_entry = page_for_doc(env, docname, visited, master_doc, depth=depth + 1)
        group_pages.append(page_entry)
    if caption:
        groups.append({"group": caption, "pages": group_pages})
    else:
        pages.extend(group_pages)


def page_for_doc(
    env: BuildEnvironment,
    docname: str,
    visited: set[str],
    master_doc: str,
    depth: int,
) -> Any:
    sub_groups: list[dict[str, Any]] = []
    sub_pages: list[Any] = []
    if docname in env.tocs:
        collect_toctree_entries(
            env,
            env.tocs[docname],
            sub_groups,
            sub_pages,
            visited,
            master_doc,
            depth=depth,
        )
    if not sub_groups and not sub_pages:
        return docname
    title = doc_title(env, docname) or docname
    if sub_groups and not sub_pages:
        return {"group": title, "pages": [docname, *sub_groups]}
    if sub_pages and not sub_groups:
        return {"group": title, "pages": [docname, *sub_pages]}
    return {"group": title, "pages": [docname, *sub_pages, *sub_groups]}
