"""Tests for sphinxcontrib.mermaid ``mermaid`` node → Mintlify fence."""

from __future__ import annotations

from unittest.mock import MagicMock

from docutils import nodes

from sphinx_mintlify_output.nodes.base import TranslationContext
from sphinx_mintlify_output.nodes.block import MermaidNode


class mermaid(nodes.General, nodes.Element):
    """Minimal stand-in for ``sphinxcontrib.mermaid.mermaid`` (same class name)."""


def test_mermaid_node_renders_mintlify_fence() -> None:
    node = mermaid()
    node["code"] = "flowchart LR\n    A[import_image] --> B[Base Image]"
    ctx = TranslationContext(builder=MagicMock(), docname="index")
    text = MermaidNode(node, None, ctx).render()
    assert text == (
        "```mermaid\nflowchart LR\n    A[import_image] --> B[Base Image]\n```\n\n"
    )


def test_mermaid_node_picked_by_registry() -> None:
    from sphinx_mintlify_output.nodes import TranslationNode

    node = mermaid()
    node["code"] = "flowchart LR\n    A --> B"
    ctx = TranslationContext(builder=MagicMock(), docname="index")
    handler = TranslationNode.from_docutils(node, None, ctx)
    assert isinstance(handler, MermaidNode)
