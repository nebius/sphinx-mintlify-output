"""URL construction for inter-page links, images and toctree cards.

Two modes, switched by a single :class:`contextvars.ContextVar`:

* **Relative** (default) — Sphinx-style. ``url_for("guide/setup", "intro")``
  returns ``../intro``; the browser resolves it against the current page
  the same way it does for any HTML site, so the build works under any
  deployment prefix without reconfiguration.
* **Absolute** — set by :class:`~sphinx_mintlify_output.builder.MintlifyBuilder`
  when ``mintlify_base_path`` is non-empty. ``url_for("guide/setup",
  "intro")`` returns ``/sandboxes/sdk/intro`` and every link is rooted
  at that prefix regardless of where the source doc lives.

Set the ``base_path`` context var once per build (in
``MintlifyBuilder.write_doc`` or earlier) — every call to
:func:`url_for` reads it without having to thread it through every
function parameter.
"""

from __future__ import annotations

import contextvars
import posixpath
from pathlib import PurePosixPath

base_path: contextvars.ContextVar[PurePosixPath | None] = contextvars.ContextVar(
    "mintlify_base_path", default=None
)


def url_for(from_doc: str, target: str) -> str:
    """Build a link from ``from_doc`` to ``target``.

    ``target`` is a docname-style path (``"intro"``, ``"guide/install"``)
    or an asset path (``"images/foo.png"``). Leading slashes are stripped
    so callers can hand in either form.

    With :data:`base_path` set, returns ``"{base}/{target}"`` — an
    absolute URL rooted at the configured mount-point.

    Without it, returns a relative path computed with
    :func:`posixpath.relpath` so the URL works regardless of where the
    docs end up deployed (same approach as Sphinx's HTML builder).
    """
    target_clean = target.lstrip("/")
    base = base_path.get()
    if base is not None:
        return str(base / target_clean)
    from_dir = posixpath.dirname(from_doc)
    rel = target_clean if not from_dir else posixpath.relpath(target_clean, from_dir)

    if not rel.startswith((".", "/")):
        rel = f"./{rel}"

    return rel
