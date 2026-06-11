project = "Misc"
extensions = ["sphinx_mintlify_output", "sphinx.ext.intersphinx", "myst_parser"]
exclude_patterns = ["_build"]
master_doc = "index"
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
myst_enable_extensions = ["colon_fence", "dollarmath"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

rst_epilog = """
.. |project| replace:: My Project
"""
