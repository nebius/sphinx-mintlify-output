"""Integration test: every internal URL emitted by the builder resolves.

What this actually verifies
---------------------------

For every ``.mdx`` page in a built test root, we extract:

* Markdown link targets   — ``[text](target)``
* Markdown image targets  — ``![alt](target)``
* JSX ``href="..."``      — toctree cards, references emitted as JSX
* JSX ``src="..."``       — ``<img>`` sized images and externalised SVG

then simulate the browser's URL resolution: treating the page's URL as
``/<docname>``, we :func:`urllib.parse.urljoin` each link's target
against it. The resulting absolute URL must point at a real file in
the output tree — either an ``<x>.mdx`` (for page slugs) or an asset
file (for images / static).

Why this is worth doing
-----------------------

Golden-byte comparison catches *changes* in rendering, but it doesn't
catch a class of bug where every rendered file looks fine in isolation
yet the cross-page links collectively don't resolve when the site is
actually served — e.g. nested page using the wrong relative depth, or
an absolute path that drops the configured base prefix. This is the
test that would have caught a "linkrot at build time" regression.

The walk runs in both URL modes:

* default (``mintlify_base_path = ""``) — relative links from each page.
* ``mintlify_base_path = "/sandboxes/sdk"`` — absolute prefixed links.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pytest

# Markdown link or image: [text](target) / ![alt](target). Strip the
# leading ``!`` if present and capture the target.
_MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
# JSX href / src attribute values. Restricted to double-quoted form,
# which is what the builder emits.
_JSX_ATTR_RE = re.compile(r'\b(?:href|src)="([^"]+)"')


def _page_url(docname: str, base_path: str = "") -> str:
    """The URL a Mintlify-served ``.mdx`` page lives at.

    ``base_path`` is prepended so this matches whatever the builder
    emitted as link targets.
    """
    base = base_path.rstrip("/")
    return f"{base}/{docname}" if base else f"/{docname}"


def _extract_targets(text: str) -> list[str]:
    """Pull every internal URL emitted in an MDX page."""
    out: list[str] = []
    out.extend(_MD_LINK_RE.findall(text))
    out.extend(_JSX_ATTR_RE.findall(text))
    return out


_EXTERNAL_SCHEMES = frozenset({"http", "https", "ftp", "data", "javascript"})


def _is_internal(target: str) -> bool:
    """Is this a link we should resolve against the output tree?"""
    if not target or target.startswith(("#", "mailto:", "tel:")):
        return False
    return urlparse(target).scheme not in _EXTERNAL_SCHEMES


def _resolved_path(
    page_url: str, target: str, *, base_path: str
) -> tuple[str, str | None]:
    """Resolve ``target`` against ``page_url`` and strip base_path.

    Returns ``(absolute_url, outdir_relative_path)`` where the second
    item is the path the resolved URL should map to inside the build
    output. Drops the ``#fragment``.
    """
    absolute = urljoin(page_url, target).split("#", 1)[0]
    if not absolute:
        return absolute, None
    if base_path:
        prefix = base_path.rstrip("/")
        if not absolute.startswith(prefix + "/") and absolute != prefix:
            # Absolute URL outside our base — link is broken or pointing
            # somewhere we don't manage.
            return absolute, None
        return absolute, absolute[len(prefix) :].lstrip("/")
    return absolute, absolute.lstrip("/")


def _exists_in_outdir(outdir: Path, rel_path: str) -> bool:
    """Does ``rel_path`` correspond to a real file in the build output?

    A page slug ``intro`` resolves to ``intro.mdx``; an asset like
    ``images/logo.png`` resolves to itself.
    """
    if not rel_path:
        # Empty path = the index page.
        return (outdir / "index.mdx").exists()
    direct = outdir / rel_path
    if direct.exists():
        return True
    # Try .mdx suffix for page slugs.
    return direct.with_suffix(".mdx").exists()


def _collect_broken_links(outdir: Path, *, base_path: str = "") -> list[str]:
    """For every .mdx in ``outdir``, return broken internal link descriptors."""
    broken: list[str] = []
    for mdx in sorted(outdir.rglob("*.mdx")):
        docname = mdx.relative_to(outdir).with_suffix("").as_posix()
        page = _page_url(docname, base_path=base_path)
        text = mdx.read_text(encoding="utf-8")
        for target in _extract_targets(text):
            if not _is_internal(target):
                continue
            absolute, rel = _resolved_path(page, target, base_path=base_path)
            if rel is None:
                broken.append(
                    f"{docname}.mdx: target {target!r} → {absolute!r} "
                    "is outside the configured base_path"
                )
                continue
            if not _exists_in_outdir(outdir, rel):
                broken.append(
                    f"{docname}.mdx: target {target!r} → {absolute!r} "
                    f"(expected {rel} or {rel}.mdx in outdir)"
                )
    return broken


# ---------------------------------------------------------------------------
# Default relative mode
# ---------------------------------------------------------------------------


@pytest.mark.sphinx("mintlify", testroot="relative-urls")
def test_links_resolve_in_relative_mode(app) -> None:
    """Every internal link/image/href/src resolves to an existing file."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx("mintlify", testroot="links")
def test_links_resolve_in_links_testroot(app) -> None:
    """The richer links testroot — multiple pages, images, nested doc."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx("mintlify", testroot="e2e")
def test_links_resolve_in_e2e_testroot(app) -> None:
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx("mintlify", testroot="navigation")
def test_links_resolve_in_navigation_testroot(app) -> None:
    """Toctree-driven navigation — card href targets must resolve."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx("mintlify", testroot="navigation-mixed")
def test_links_resolve_in_navigation_mixed_testroot(app) -> None:
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx("mintlify", testroot="raw-assets")
def test_links_resolve_in_raw_assets_testroot(app) -> None:
    """Externalised inline SVG / base64 must produce a working ``src``."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir))
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


# ---------------------------------------------------------------------------
# Absolute base_path mode
# ---------------------------------------------------------------------------


@pytest.mark.sphinx("mintlify", testroot="base-path")
def test_links_resolve_under_base_path(app) -> None:
    """Every link is rooted under ``/sandboxes/sdk`` and resolves there."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir), base_path="/sandboxes/sdk")
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


@pytest.mark.sphinx(
    "mintlify",
    testroot="links",
    confoverrides={"mintlify_base_path": "/embedded/here"},
)
def test_links_resolve_under_base_path_override(app) -> None:
    """The same links testroot, but built under an override prefix."""
    app.build()
    broken = _collect_broken_links(Path(app.outdir), base_path="/embedded/here")
    assert not broken, "broken internal links:\n  " + "\n  ".join(broken)


# ---------------------------------------------------------------------------
# Sanity tests for the resolver itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "page,target,expected",
    [
        ("/index", "intro", "/intro"),
        ("/index", "guide/setup", "/guide/setup"),
        ("/guide/setup", "../intro", "/intro"),
        ("/guide/setup", "../images/foo.png", "/images/foo.png"),
        ("/guide/sub/page", "../../intro", "/intro"),
        ("/index", "/absolute/path", "/absolute/path"),
    ],
)
def test_urljoin_matches_browser_behaviour(
    page: str, target: str, expected: str
) -> None:
    """Sanity-check the resolver against known browser/HTML spec behaviour."""
    assert urljoin(page, target) == expected
