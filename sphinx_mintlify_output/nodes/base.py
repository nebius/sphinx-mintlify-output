"""Base class and shared context for the per-node MDX renderers.

Every concrete node in :mod:`sphinx_mintlify_output.nodes` inherits from
:class:`TranslationNode`. The factory :meth:`TranslationNode.from_docutils`
consults :data:`sphinx_mintlify_output.nodes.NODE_REGISTRY` to pick the
right subclass for a given docutils node — walking the MRO of the
docutils class so subclasses (e.g. ``sphinx.addnodes.literal_strong``)
dispatch to their base handler without an explicit entry.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from docutils import nodes
from sphinx.util import logging

if TYPE_CHECKING:
    from sphinx_mintlify_output.builder import MintlifyBuilder

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TranslationContext:
    """Shared, mutable state threaded through the whole render tree.

    * ``builder`` / ``docname`` — entry points to Sphinx config, env,
      and image registry.
    * ``frontmatter`` — accumulated YAML frontmatter for the page; the
      top-level title is captured here instead of emitting a heading.
    * ``section_level`` — current heading depth, mutated by section
      nodes while their body renders so titles know what ``#`` prefix
      to use.
    * ``title_captured`` — guard so we don't promote a second top-level
      title into frontmatter on multi-section pages.
    * ``desc_depth`` / ``signature_depth`` — autodoc nesting counters
      used to pick the heading level and to disable MDX escaping
      inside a Python signature.
    * ``desc_param_stack`` — innermost desc's parameter info (read by
      ``ParamField`` rendering); pushed on enter and popped on leave.
    """

    builder: MintlifyBuilder
    docname: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    section_level: int = 0
    title_captured: bool = False
    desc_depth: int = 0
    signature_depth: int = 0
    desc_param_stack: list[dict[str, Any]] = field(default_factory=list)
    # Refids that point to a ``citation`` block — populated by
    # :class:`DocumentNode` so :class:`ReferenceNode` can render a
    # resolved citation reference as ``[^id]`` rather than as a regular
    # markdown link.
    citation_ids: set[str] = field(default_factory=set)

    def current_desc_params(self) -> dict[str, Any]:
        return self.desc_param_stack[-1] if self.desc_param_stack else {}


class TranslationNode:
    """Base class for every per-node MDX translator.

    ``node`` is typed as :class:`docutils.nodes.Element` because nearly
    every subclass reads attributes that only ``Element`` exposes
    (``.get()``, ``.children``). The single leaf case —
    :class:`~sphinx_mintlify_output.nodes.inline.TextNode` — wraps a
    :class:`docutils.nodes.Text` and is the only path that ignores
    ``Element``-only API; it's safe because ``.astext()`` is defined
    on the common :class:`docutils.nodes.Node` base.
    """

    __slots__ = ("ctx", "node", "parent")

    node: nodes.Element

    def __init__(
        self,
        node: nodes.Node,
        parent: TranslationNode | None,
        ctx: TranslationContext,
    ) -> None:
        # Stored as Node at runtime; the cast tells mypy to treat the
        # attribute as Element in subclasses without runtime cost.
        # TextNode (the only Text-wrapping subclass) re-annotates the
        # attribute to nodes.Text and bypasses Element-only API.
        self.node = cast("nodes.Element", node)
        self.parent = parent
        self.ctx = ctx

    @classmethod
    def from_docutils(
        cls,
        node: nodes.Node,
        parent: TranslationNode | None,
        ctx: TranslationContext,
    ) -> TranslationNode:
        """Pick the registered :class:`TranslationNode` for ``node``.

        Walks ``type(node).__mro__`` so a subclass like
        ``sphinx.addnodes.literal_strong`` (descends from ``nodes.strong``)
        dispatches to the same handler as its base without an explicit
        registry entry. Block-level nodes with no registered handler log
        a warning so silent content loss is visible in CI output.
        """
        # Local import: NODE_REGISTRY lives in the package's __init__
        # and is populated after the leaf modules finish loading.
        from sphinx_mintlify_output.nodes import NODE_REGISTRY

        for klass in type(node).__mro__:
            handler = NODE_REGISTRY.get(klass.__name__)
            if handler is not None:
                return handler(node, parent, ctx)
        if not isinstance(node, nodes.Inline | nodes.Text):
            source = node.source or "<unknown>"
            line = node.line or 0
            logger.warning(
                "skipping unknown node %s (no MDX mapping registered)",
                type(node).__name__,
                location=f"{source}:{line}" if line else source,
            )
        return PassthroughNode(node, parent, ctx)

    # -- child iteration ----------------------------------------------------

    def child_nodes(self) -> list[TranslationNode]:
        """Wrap every docutils child in its registered translator."""
        if not isinstance(self.node, nodes.Element):
            return []
        return [
            TranslationNode.from_docutils(child, self, self.ctx)
            for child in self.node.children
        ]

    def render_children(self) -> str:
        """Render every child and concatenate the output."""
        return "".join(c.render() for c in self.child_nodes())

    def render_docutils_nodes(self, items: Iterable[nodes.Node]) -> str:
        """Render an arbitrary list of docutils nodes as children of *self*."""
        return "".join(
            TranslationNode.from_docutils(c, self, self.ctx).render() for c in items
        )

    def render(self) -> str:
        """Produce the MDX for this node. Default: passthrough children."""
        return self.render_children()

    # -- ancestor lookup ----------------------------------------------------

    def find_ancestor(self, *types: type[TranslationNode]) -> TranslationNode | None:
        """Walk up the chain of :class:`TranslationNode` parents."""
        node = self.parent
        while node is not None:
            if isinstance(node, types):
                return node
            node = node.parent
        return None


class PassthroughNode(TranslationNode):
    """Default for unhandled docutils types — render children, emit nothing else."""


class DocumentNode(TranslationNode):
    """Top of the doctree — drives the whole page render."""

    def render(self) -> str:
        # Pre-scan citations so resolved citation references (which
        # docutils rewrites to plain `reference` nodes) can be rendered
        # as `[^id]` instead of regular markdown links.
        for citation in self.node.findall(nodes.citation):
            for cid in citation.get("ids") or []:
                self.ctx.citation_ids.add(cid)

        body = self.render_children().strip("\n")
        from sphinx_mintlify_output.frontmatter import render_frontmatter

        frontmatter = render_frontmatter(
            self.ctx.frontmatter, self.ctx.builder.config.mintlify_frontmatter
        )
        if frontmatter and body:
            return f"{frontmatter}\n\n{body}\n"
        if frontmatter:
            return f"{frontmatter}\n"
        return body + "\n" if body else ""
