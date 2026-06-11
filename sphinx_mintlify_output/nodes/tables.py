"""Table rendering — wraps the existing :mod:`tables` renderers in a node."""

from __future__ import annotations

from docutils import nodes

from sphinx_mintlify_output.nodes.base import TranslationNode
from sphinx_mintlify_output.state import TableCell, TableState
from sphinx_mintlify_output.tables import render_table


class TableNode(TranslationNode):
    """Walks its own children (tgroup/thead/tbody/row/entry) into a TableState."""

    def render(self) -> str:
        state = TableState()
        for child in self.node.children:
            if isinstance(child, nodes.title):
                state.title = child.astext()
            elif isinstance(child, nodes.tgroup):
                self._collect_tgroup(child, state)
        return render_table(state) + "\n\n"

    def _collect_tgroup(self, tgroup: nodes.Element, state: TableState) -> None:
        for child in tgroup.children:
            if isinstance(child, nodes.thead):
                self._collect_rows(child, state, head=True)
            elif isinstance(child, nodes.tbody):
                self._collect_rows(child, state, head=False)
            elif isinstance(child, nodes.row):
                # Simple tables sometimes skip thead/tbody wrappers.
                self._collect_row(child, state, head=False)

    def _collect_rows(
        self, group: nodes.Element, state: TableState, *, head: bool
    ) -> None:
        for row in group.children:
            if isinstance(row, nodes.row):
                self._collect_row(row, state, head=head)

    def _collect_row(
        self, row: nodes.Element, state: TableState, *, head: bool
    ) -> None:
        cells: list[TableCell] = []
        for entry in row.children:
            if isinstance(entry, nodes.entry):
                cells.append(self._make_cell(entry, state))
        (state.head if head else state.body).append(cells)

    def _make_cell(self, entry: nodes.Element, state: TableState) -> TableCell:
        morerows = int(entry.get("morerows", 0))
        morecols = int(entry.get("morecols", 0))
        if morerows or morecols:
            state.complex = True
        text = self.render_docutils_nodes(list(entry.children)).strip("\n").strip()
        if "\n\n" in text or (
            "\n" in text and ("```" in text or text.startswith("- "))
        ):
            state.complex = True
        return TableCell(text=text, morerows=morerows, morecols=morecols)
