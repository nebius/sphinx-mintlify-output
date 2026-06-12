"""Externalize and write image assets referenced from raw HTML blocks.

Sphinx output can embed images two ways the translator has to handle:

* Inline ``<svg>...</svg>`` markup (e.g. from sphinxcontrib-svgbob).
* Base64 ``data:image/<mime>;base64,...`` URIs.

Both forms inflate the page and can break MDX parsing. The functions
here write the payload to ``<outdir>/<image_dir>/raw-<sha>.<ext>`` and
rewrite the HTML to reference the file instead. Asset writes are
idempotent: identical payloads share a single file.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import posixpath
import re

from sphinx_mintlify_output.urls import url_for

SVG_BLOCK_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.DOTALL | re.IGNORECASE)
DATA_URI_RE = re.compile(
    r"data:image/(?P<mime>png|jpeg|jpg|gif|svg\+xml|webp);base64,"
    r"(?P<data>[A-Za-z0-9+/=\s]+?)(?=[\"')\s])",
    re.IGNORECASE,
)
MIME_EXT: dict[str, str] = {
    "png": "png",
    "jpeg": "jpg",
    "jpg": "jpg",
    "gif": "gif",
    "svg+xml": "svg",
    "webp": "webp",
}


def externalize_inline_assets(
    html: str,
    *,
    outdir: str,
    image_dir: str,
    from_doc: str,
) -> str:
    """Replace inline SVG and base64 data: URIs with file references.

    Standalone ``<svg>…</svg>`` blocks are written as ``.svg`` files and
    replaced with ``<img>`` tags. ``data:image/<mime>;base64,…`` payloads
    inside larger HTML (typically inside ``<img src="…">``) are written
    using the inferred extension and only the URI is replaced. Other HTML
    passes through untouched. URLs are produced via
    :func:`~sphinx_mintlify_output.urls.url_for` so they respect the
    relative/absolute mode for the current build.
    """

    def replace_svg_block(match: re.Match[str]) -> str:
        svg = match.group(0)
        rel = write_asset_file(
            svg.encode("utf-8"),
            ext="svg",
            outdir=outdir,
            image_dir=image_dir,
            from_doc=from_doc,
        )
        return f'<img src="{rel}" />'

    def replace_data_uri(match: re.Match[str]) -> str:
        mime = match.group("mime").lower()
        raw = re.sub(r"\s+", "", match.group("data"))
        ext = MIME_EXT.get(mime, "bin")
        try:
            payload = base64.b64decode(raw, validate=True)
        except (binascii.Error, ValueError):
            return match.group(0)
        rel = write_asset_file(
            payload,
            ext=ext,
            outdir=outdir,
            image_dir=image_dir,
            from_doc=from_doc,
        )
        return rel

    html = SVG_BLOCK_RE.sub(replace_svg_block, html)
    html = DATA_URI_RE.sub(replace_data_uri, html)
    return html


def write_asset_file(
    content: bytes,
    *,
    ext: str,
    outdir: str,
    image_dir: str,
    from_doc: str,
) -> str:
    """Write ``content`` to ``<outdir>/<image_dir>/raw-<hash>.<ext>``."""
    digest = hashlib.sha256(content).hexdigest()[:16]
    filename = f"raw-{digest}.{ext}"
    target_dir = os.path.join(outdir, image_dir)
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, filename)
    if not os.path.exists(target):
        with open(target, "wb") as fp:
            fp.write(content)
    return url_for(from_doc, posixpath.join(image_dir, filename))
