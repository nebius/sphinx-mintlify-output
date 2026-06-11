import os
import sys

sys.path.insert(0, os.path.abspath("."))

project = "Autodoc"
extensions = ["sphinx_mintlify_output", "sphinx.ext.autodoc"]
exclude_patterns = ["_build"]
master_doc = "index"

autodoc_typehints = "signature"
