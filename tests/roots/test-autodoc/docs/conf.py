import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

project = "Autodoc"
extensions = ["sphinx_mintlify_output", "sphinx.ext.autodoc", "sphinx_inline_tabs"]
exclude_patterns = ["_build"]
master_doc = "index"

autodoc_typehints = "signature"
