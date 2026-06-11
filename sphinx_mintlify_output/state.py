"""Typed value objects shared across the renderer.

* :class:`TableCell` / :class:`TableState` — accumulated rows for the
  current table, produced by
  :class:`~sphinx_mintlify_output.nodes.tables.TableNode` and consumed
  by :func:`sphinx_mintlify_output.tables.render_table`.
* :class:`ParamInfo` — per-parameter metadata extracted from a Sphinx
  signature by :func:`sphinx_mintlify_output.autodoc.extract_param_info`,
  read by the autodoc ``<ParamField>`` renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class ParamInfo(TypedDict, total=False):
    """Per-parameter metadata extracted from a Sphinx signature.

    Keys are optional —
    :func:`sphinx_mintlify_output.autodoc.extract_param_info` only sets
    the fields it can derive from the doctree.
    """

    type: str
    default: str
    required: bool


@dataclass(slots=True)
class TableCell:
    text: str
    morerows: int = 0
    morecols: int = 0


@dataclass(slots=True)
class TableState:
    title: str = ""
    head: list[list[TableCell]] = field(default_factory=list)
    body: list[list[TableCell]] = field(default_factory=list)
    current_group: str = "body"
    current_row: list[TableCell] | None = None
    complex: bool = False
