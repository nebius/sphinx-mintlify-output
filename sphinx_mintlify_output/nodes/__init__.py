"""Per-node MDX translation classes.

The package exports :class:`TranslationNode` (base class, dispatcher,
context object) and the :data:`NODE_REGISTRY` mapping that
:meth:`TranslationNode.from_docutils` consults to pick the right
subclass for a given docutils node.

The registry is keyed by docutils class name; ``from_docutils`` walks
``type(node).__mro__`` so subclasses like
``sphinx.addnodes.literal_strong`` (descends from ``nodes.strong``)
dispatch to the same handler as their base.

To add a new node type, write a :class:`TranslationNode` subclass in
the matching module (or create a new one) and add an entry to
:data:`NODE_REGISTRY` at the bottom of this file. There are no
import-time side effects in the leaf modules — registration happens
in one place.
"""

from __future__ import annotations

from sphinx_mintlify_output.components import ADMONITION_TO_COMPONENT
from sphinx_mintlify_output.nodes.admonitions import (
    AdmonitionNode,
    AdmonitionTitleNode,
    VersionModifiedNode,
)
from sphinx_mintlify_output.nodes.autodoc import (
    DescContentNode,
    DescNode,
    DescSignatureNode,
)
from sphinx_mintlify_output.nodes.base import (
    DocumentNode,
    PassthroughNode,
    TranslationContext,
    TranslationNode,
)
from sphinx_mintlify_output.nodes.block import (
    BlockQuoteNode,
    LiteralBlockNode,
    MermaidNode,
    ParagraphNode,
    SectionNode,
    TitleNode,
    TransitionNode,
)
from sphinx_mintlify_output.nodes.definitions import (
    ClassifierNode,
    DefinitionListNode,
    DefinitionNode,
    FieldBodyNode,
    FieldListNode,
    FieldNameNode,
    FieldNode,
    TermNode,
)
from sphinx_mintlify_output.nodes.footnotes import (
    CitationNode,
    CitationReferenceNode,
    FootnoteNode,
    FootnoteReferenceNode,
    LabelNode,
)
from sphinx_mintlify_output.nodes.images import CaptionNode, FigureNode, ImageNode
from sphinx_mintlify_output.nodes.inline import (
    AbbreviationNode,
    EmphasisNode,
    LiteralNode,
    StrongNode,
    SubscriptNode,
    SuperscriptNode,
    TextNode,
)
from sphinx_mintlify_output.nodes.links import ReferenceNode, TargetNode
from sphinx_mintlify_output.nodes.lists import (
    BulletListNode,
    EnumeratedListNode,
    ListItemNode,
)
from sphinx_mintlify_output.nodes.math import MathBlockNode, MathNode
from sphinx_mintlify_output.nodes.raw import CommentNode, RawNode
from sphinx_mintlify_output.nodes.sphinx_design import ContainerNode
from sphinx_mintlify_output.nodes.sphinx_inline_tabs import TabContainerNode
from sphinx_mintlify_output.nodes.tables import TableNode
from sphinx_mintlify_output.nodes.toctree import CompoundNode, ToctreeNode

__all__ = [
    "NODE_REGISTRY",
    "AdmonitionTitleNode",
    "PassthroughNode",
    "TranslationContext",
    "TranslationNode",
]


NODE_REGISTRY: dict[str, type[TranslationNode]] = {
    # Document root + structural blocks
    "document": DocumentNode,
    "section": SectionNode,
    "title": TitleNode,
    "paragraph": ParagraphNode,
    "block_quote": BlockQuoteNode,
    "transition": TransitionNode,
    "literal_block": LiteralBlockNode,
    "mermaid": MermaidNode,
    # Inline text formatting
    "Text": TextNode,
    "emphasis": EmphasisNode,
    "strong": StrongNode,
    "literal": LiteralNode,
    "subscript": SubscriptNode,
    "superscript": SuperscriptNode,
    "abbreviation": AbbreviationNode,
    # Lists
    "bullet_list": BulletListNode,
    "enumerated_list": EnumeratedListNode,
    "list_item": ListItemNode,
    # Definition / field lists
    "definition_list": DefinitionListNode,
    "term": TermNode,
    "classifier": ClassifierNode,
    "definition": DefinitionNode,
    "field_list": FieldListNode,
    "field": FieldNode,
    "field_name": FieldNameNode,
    "field_body": FieldBodyNode,
    # Tables
    "table": TableNode,
    # Math + raw passthrough
    "math": MathNode,
    "math_block": MathBlockNode,
    "raw": RawNode,
    "comment": CommentNode,
    # Links, anchors, media
    "reference": ReferenceNode,
    "target": TargetNode,
    "image": ImageNode,
    "figure": FigureNode,
    "caption": CaptionNode,
    # Footnotes and citations
    "footnote": FootnoteNode,
    "footnote_reference": FootnoteReferenceNode,
    "citation": CitationNode,
    "citation_reference": CitationReferenceNode,
    "label": LabelNode,
    # Toctree and its post-resolution wrapper
    "toctree": ToctreeNode,
    "compound": CompoundNode,
    # Sphinx admonitions and sphinx-design containers
    "versionmodified": VersionModifiedNode,
    "deprecated": VersionModifiedNode,
    "container": ContainerNode,
    "TabContainer": TabContainerNode,
    # Autodoc
    "desc": DescNode,
    "desc_signature": DescSignatureNode,
    "desc_content": DescContentNode,
}

# All admonition kinds dispatch to the generic AdmonitionNode; the component
# (Note / Tip / Warning / ...) is picked from ADMONITION_TO_COMPONENT at
# render time.
for _name in ADMONITION_TO_COMPONENT:
    NODE_REGISTRY[_name] = AdmonitionNode
del _name
