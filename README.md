# sphinx-mintlify-output

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Sphinx](https://img.shields.io/badge/sphinx-7.0%2B-green.svg)](https://www.sphinx-doc.org/)

Sphinx builder that turns reST / MyST sources into a deploy-ready
[Mintlify](https://mintlify.com) project: `.mdx` pages with YAML
frontmatter, copied static assets, and a `docs.json` navigation
manifest.

Useful when your source of truth is reST/MyST (autodoc, intersphinx,
sphinx-design) and you want to ship it through Mintlify without
rewriting in MDX.

## Install

```sh
pip install sphinx-mintlify-output
# or
uv add --dev sphinx-mintlify-output
```

## Quickstart

In `conf.py`:

```python
extensions = ["sphinx_mintlify_output"]

mintlify_docs_json = {
    "name": "My Docs",
    "theme": "mint",
    "colors": {"primary": "#0d9373"},
}
```

Build:

```sh
sphinx-build -b mintlify docs out/mintlify
```

Point Mintlify at `out/mintlify`. Done.

## Configuration

| Key | Default | Purpose |
|-----|---------|---------|
| `mintlify_docs_json` | `{}` | Merged into the generated `docs.json` |
| `mintlify_static_path` | `[]` | Directories copied into `out/static/` |
| `mintlify_image_dir` | `"images"` | Where images land relative to outdir |
| `mintlify_frontmatter` | `{}` | Default frontmatter merged into every page |
| `mintlify_component_map` | `{}` | Override admonition → component mappings |
| `mintlify_emit_anchors` | `True` | Emit `<a id>` anchors before headings |
| `mintlify_externalize_assets` | `True` | Pull inline SVG / base64 image URIs into `images/` and reference them by path |

## What's translated

- **reST / MyST core** — headings, paragraphs, lists, code blocks, block
  quotes, transitions.
- **Tables** — GFM by default; falls back to `<table>` HTML for
  rowspan / colspan / multi-line cells.
- **Admonitions** — `note` / `tip` / `warning` / ... → Mintlify
  `<Note>` / `<Tip>` / `<Warning>` / `<Info>` / `<Danger>`. Use the
  directive's `:class:` option to pick `<Check>`, `<Steps>` /
  `<Step>`, or `<Callout>`.
- **sphinx-design** — `card` → `<Card>`, `tab-set` → `<Tabs>` (or
  `<CodeGroup>` when every tab is a single code block), `dropdown` →
  `<Accordion>`, grids → `<Columns cols={N}>`.
- **Cross-references** — `:doc:` / `:ref:` become relative links;
  footnotes and citations become `[^id]` with matching definitions;
  abbreviations become `<Tooltip>`.
- **Images and figures** — copied to `images/`; sized images switch to
  `<img>`; `figure` becomes `<Frame caption=…>` (short caption) or
  `<Frame>` with a rendered caption.
- **Autodoc** — Python signatures as anchored heading + fenced code
  block; `:param:` → `<ParamField>`; `:returns:` / `:yields:` /
  `:raises:` → `<ResponseField>`. Classes group their attributes and
  methods into a styled block.
- **CLI options** — `.. option::` / `cmdoption` render as a `<dl>` with
  backticked signature.
- **Math** — inline `$…$` and block `$$…$$`.
- **Raw HTML / MDX** — passed through; inline `<svg>` and base64 data
  URIs optionally externalised as files.
- **Navigation** — `docs.json` built from the toctree; mixed top-level
  captioned + uncaptioned toctrees are handled. Override the result via
  `mintlify_docs_json["navigation"]`.

Unknown nodes are skipped with a Sphinx warning rather than silently
dropped.

## Development

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv).

```sh
uv sync
uv run pytest
uv run mypy sphinx_mintlify_output
uv run ruff check .
```

`tests/golden/` is a byte-exact corpus that pins the rendered output;
`uv run python tests/capture_golden.py` refreshes it after an
intentional change.

To add support for a new docutils node: write a `TranslationNode`
subclass under `sphinx_mintlify_output/nodes/`, register it in the
`NODE_REGISTRY` dict in `nodes/__init__.py`, and drop a fixture
under `tests/roots/test-<name>/`.

## Status

Alpha. Feature-complete for the use cases above; API and config keys
may shift before 1.0 — pin a version if you depend on the output
layout.

## Copyright

Nebius B.V. 2026, licensed under the Apache License, Version 2.0 (see
[LICENSE](LICENSE)).
