"""End-to-end tests against a live ``mintlify dev`` server.

Opt-in. Run with::

    uv run pytest -m integration

Skipped automatically when ``npx`` is not on ``PATH`` (we can't spawn
the Mintlify CLI without Node.js installed). Tests issue real HTTP
requests to a subprocess that picks up the build output, so they
validate the full pipeline — MDX syntactic correctness, ``docs.json``
schema acceptance, navigability, and that emitted asset paths
actually resolve when a browser fetches them.

The fixture is module-scoped (one server per parametrize iteration)
and parametrized over the two URL modes:

* ``""`` (default, relative) — links work out of the box on ``mint dev``.
* ``"/sandboxes/sdk"`` (absolute prefix) — ``mint dev`` serves under
  ``/``, so links pointing at ``/sandboxes/sdk/...`` 404 when navigated.
  The fixture still starts a server in this mode to validate that the
  MDX itself parses (catching syntax errors introduced by the prefix
  pipeline); tests that depend on link navigation skip themselves.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        shutil.which("npx") is None,
        reason="npx not installed; install Node.js to run this suite",
    ),
]


@dataclass(frozen=True)
class MintSession:
    base_url: str
    base_path: str
    outdir: Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def free_port_factory():
    """Callable returning a fresh unused TCP port on each call.

    A factory (session-scoped) rather than a plain fixture because
    :func:`mint_session` is module-scoped + parametrized and needs a
    different port for every parametrize iteration; a fixture caching
    the value would reuse the same port across both servers.
    """

    def make() -> int:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    return make


def _wait_for_url(url: str, *, timeout: float) -> None:
    """Block until ``url`` returns any HTTP response, or raise on timeout."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except urllib.error.HTTPError:
            # Any HTTP status from the server means it's accepting requests.
            return
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            last_err = exc
        time.sleep(0.1)
    raise RuntimeError(f"server at {url} did not respond within {timeout}s: {last_err}")


def _build_docs(src: Path, out: Path, *, base_path: str) -> None:
    """Run ``sphinx-build`` to produce a Mintlify project under ``out``."""
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "build",
        "-b",
        "mintlify",
        "-q",
        str(src),
        str(out),
    ]
    if base_path:
        cmd += ["-D", f"mintlify_base_path={base_path}"]
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(
    scope="module",
    params=["", "/sandboxes/sdk"],
    ids=["root", "prefixed"],
)
def mint_session(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    free_port_factory,
) -> MintSession:
    base_path: str = request.param
    workdir = tmp_path_factory.mktemp(f"mint-{base_path.replace('/', '_') or 'root'}")
    docs = workdir / "docs"
    src = Path(__file__).parent / "roots" / "test-relative-urls"

    _build_docs(src, docs, base_path=base_path)
    assert (docs / "docs.json").exists(), "builder must emit docs.json"

    # ``--port`` picks an unused TCP port so parallel runs and rerun-after-
    # crashed-previous don't fight over 3000. ``--no-open`` suppresses the
    # auto-launch of a browser tab — annoying on a dev machine, broken on
    # CI. ``-t false`` opts out of telemetry so test runs aren't recorded.
    port = free_port_factory()
    proc = subprocess.Popen(
        [
            "npx",
            "--yes",
            "mintlify",
            "dev",
            "--port",
            str(port),
            "--no-open",
            "-t",
            "false",
        ],
        cwd=docs,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # BROWSER=none belt-and-braces for any sub-process that uses the
        # `open` npm package instead of mintlify's own flag.
        env={**os.environ, "BROWSER": "none", "CI": "true"},
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_url(f"{base_url}/", timeout=240)
    except Exception:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise

    try:
        yield MintSession(base_url=base_url, base_path=base_path, outdir=docs)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes


def _get(url: str) -> Response:
    """Issue a GET; return :class:`Response` even on 4xx/5xx."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return Response(
                status=int(resp.status),
                content_type=resp.headers.get("Content-Type", ""),
                body=resp.read(),
            )
    except urllib.error.HTTPError as exc:
        return Response(
            status=int(exc.code),
            content_type=exc.headers.get("Content-Type", "") if exc.headers else "",
            body=exc.read() if exc.fp else b"",
        )


def _all_docnames(outdir: Path) -> list[str]:
    """Every page docname (sans extension) the builder produced."""
    return sorted(
        p.relative_to(outdir).with_suffix("").as_posix() for p in outdir.rglob("*.mdx")
    )


_FRONTMATTER_TITLE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)


def _frontmatter_title(outdir: Path, docname: str) -> str:
    """Pull the page title out of the .mdx frontmatter (``title: X``)."""
    mdx = outdir / f"{docname}.mdx"
    match = _FRONTMATTER_TITLE_RE.search(mdx.read_text(encoding="utf-8"))
    assert match, f"{docname}.mdx has no title in frontmatter"
    return match.group(1).strip().strip("\"'")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_server_started(mint_session: MintSession) -> None:
    """The dev server replied — MDX + docs.json parsed without errors."""
    response = _get(f"{mint_session.base_url}/")
    assert response.status < 500, f"server returned {response.status} on /"


def test_index_page_serves(mint_session: MintSession) -> None:
    """``/`` returns 200 with HTML content carrying the index page title."""
    response = _get(f"{mint_session.base_url}/")
    assert response.status == 200, f"expected 200, got {response.status}"
    assert response.content_type.startswith("text/html"), response.content_type
    expected = _frontmatter_title(mint_session.outdir, "index")
    body = response.body.decode("utf-8", errors="replace")
    assert f"<title>{expected}" in body, (
        f"index HTML missing <title>{expected}…</title> "
        f"(server returned a {len(response.body)}-byte body)"
    )


def test_every_page_in_docs_json_serves(mint_session: MintSession) -> None:
    """Every page slug listed in ``docs.json`` returns 200."""
    data = json.loads((mint_session.outdir / "docs.json").read_text("utf-8"))

    def walk(node: object) -> list[str]:
        if isinstance(node, str):
            return [node]
        if isinstance(node, list):
            return [s for n in node for s in walk(n)]
        if isinstance(node, dict):
            out: list[str] = []
            for key in ("pages", "groups", "tabs"):
                if key in node:
                    out.extend(walk(node[key]))
            return out
        return []

    slugs = walk(data.get("navigation", {})) or _all_docnames(mint_session.outdir)
    assert slugs, "no pages discovered for verification"
    failures: list[str] = []
    for slug in slugs:
        response = _get(f"{mint_session.base_url}/{slug}")
        if response.status != 200:
            failures.append(f"  /{slug} → {response.status}")
    assert not failures, "pages did not serve:\n" + "\n".join(failures)


def test_every_built_page_renders_its_title(mint_session: MintSession) -> None:
    """For every built ``.mdx``, the served HTML carries that page's title.

    Catches the "next.js returns a 200 SPA shell that doesn't actually
    contain page content" pseudo-success failure mode — the body must
    have ``<title>{title}…`` from the page's own frontmatter, not the
    project-level fallback or a blank shell.
    """
    failures: list[str] = []
    for docname in _all_docnames(mint_session.outdir):
        response = _get(f"{mint_session.base_url}/{docname}")
        if response.status != 200:
            failures.append(f"  /{docname} → status {response.status}")
            continue
        expected = _frontmatter_title(mint_session.outdir, docname)
        body = response.body.decode("utf-8", errors="replace")
        if f"<title>{expected}" not in body:
            failures.append(f"  /{docname} → 200 but no <title>{expected}…</title>")
    assert not failures, "page content checks failed:\n" + "\n".join(failures)


def test_static_assets_match_source_bytes(mint_session: MintSession) -> None:
    """Each file under ``images/`` is served byte-identical with image MIME.

    Catches the "static path is rewritten to an HTML 404 page that still
    returns 200" failure mode — content-type must say ``image/`` and
    the bytes must exactly match what the builder wrote on disk.
    """
    images_dir = mint_session.outdir / "images"
    if not images_dir.exists():
        pytest.skip("test root has no images/ subdirectory")
    files = sorted(p for p in images_dir.iterdir() if p.is_file())
    assert files, "test root should ship at least one image"
    failures: list[str] = []
    for path in files:
        response = _get(f"{mint_session.base_url}/images/{path.name}")
        if response.status != 200:
            failures.append(f"  /images/{path.name} → status {response.status}")
            continue
        if not response.content_type.startswith("image/"):
            failures.append(
                f"  /images/{path.name} → Content-Type {response.content_type!r}"
                " (expected image/*)"
            )
        expected = path.read_bytes()
        if response.body != expected:
            failures.append(
                f"  /images/{path.name} → body mismatch "
                f"({len(response.body)}B served vs {len(expected)}B source)"
            )
    assert not failures, "asset content checks failed:\n" + "\n".join(failures)


def test_relative_links_navigate_to_target_page(mint_session: MintSession) -> None:
    """Follow each link and verify the fetched page is the target page.

    Resolves every ``[text](url)`` / ``![alt](url)`` / JSX ``href`` /
    ``src`` to an absolute URL the way a browser would, GETs it, and
    asserts the response carries the title of the *target* page (for
    HTML links) or an ``image/*`` content type (for asset links). Mere
    200 wouldn't catch a router that returns the index page for every
    unknown URL.

    Only valid in the default URL mode — under
    ``mintlify_base_path`` the emitted links live under the configured
    prefix while ``mint dev`` serves at ``/``, so navigation would 404
    by design.
    """
    if mint_session.base_path:
        pytest.skip(
            "absolute base_path mode: mint dev serves under / not under the prefix"
        )

    md_link = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
    jsx_attr = re.compile(r'\b(?:href|src)="([^"]+)"')
    external = frozenset({"http", "https", "mailto", "tel", "ftp", "data"})

    failures: list[str] = []
    for mdx in mint_session.outdir.rglob("*.mdx"):
        docname = mdx.relative_to(mint_session.outdir).with_suffix("").as_posix()
        page_url = f"{mint_session.base_url}/{docname}"
        body = mdx.read_text(encoding="utf-8")
        targets = set(md_link.findall(body)) | set(jsx_attr.findall(body))
        for target in targets:
            if not target or target.startswith("#"):
                continue
            if urlparse(target).scheme in external:
                continue
            absolute = urljoin(page_url, target).split("#", 1)[0]
            response = _get(absolute)
            if response.status != 200:
                failures.append(
                    f"  {docname}.mdx → {target!r} ({absolute}) → "
                    f"status {response.status}"
                )
                continue
            # Page target: verify the rendered HTML actually loaded the
            # intended page, not the index/404 fallback.
            if response.content_type.startswith("text/html"):
                target_docname = absolute[len(mint_session.base_url) :].lstrip("/")
                if not target_docname:
                    target_docname = "index"
                if (mint_session.outdir / f"{target_docname}.mdx").exists():
                    expected = _frontmatter_title(mint_session.outdir, target_docname)
                    text = response.body.decode("utf-8", errors="replace")
                    if f"<title>{expected}" not in text:
                        failures.append(
                            f"  {docname}.mdx → {target!r} loaded HTML but"
                            f" no <title>{expected}…</title> (got "
                            f"{len(response.body)}B; possible SPA-fallback?)"
                        )
            elif response.content_type.startswith("image/"):
                if not response.body:
                    failures.append(
                        f"  {docname}.mdx → {target!r} image had empty body"
                    )
    assert not failures, "link follow-through failed:\n" + "\n".join(failures)
