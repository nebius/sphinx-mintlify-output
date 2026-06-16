project = "E2E"
extensions = ["sphinx_mintlify_output"]
exclude_patterns = ["_build"]
master_doc = "index"

mintlify_static_path = ["_static"]
mintlify_docs_json = {
    "name": "E2E Docs",
    "logo": {"light": "static/favicon.ico"},
}
mintlify_frontmatter = {
    "icon": "book-open-cover",
}
