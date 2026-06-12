"""Sphinx builder that emits Mintlify-compatible MDX output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sphinx_mintlify_output.builder import MintlifyBuilder

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"

__all__ = ["MintlifyBuilder", "__version__", "setup"]


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_builder(MintlifyBuilder)
    app.add_config_value("mintlify_docs_json", {}, "env")
    app.add_config_value("mintlify_static_path", [], "env")
    app.add_config_value("mintlify_image_dir", "images", "env")
    app.add_config_value("mintlify_frontmatter", {}, "env")
    app.add_config_value("mintlify_component_map", {}, "env")
    app.add_config_value("mintlify_emit_anchors", True, "env")
    app.add_config_value("mintlify_externalize_assets", True, "env")
    app.add_config_value("mintlify_base_path", "", "env")
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
