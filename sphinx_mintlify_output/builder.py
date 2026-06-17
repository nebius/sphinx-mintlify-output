"""Mintlify builder."""

from __future__ import annotations

import json
import os
import posixpath
import shutil
from os import path
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, ClassVar

from docutils import nodes
from sphinx.builders import Builder
from sphinx.util import logging
from sphinx.util.osutil import ensuredir

from sphinx_mintlify_output import urls
from sphinx_mintlify_output.navigation import build_docs_json
from sphinx_mintlify_output.nodes import TranslationContext, TranslationNode

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


def inject_hidden_toctrees(
    builder: Builder, docname: str, doctree: nodes.document
) -> None:
    """No-op: hidden toctrees drive ``docs.json`` navigation only.

    Sphinx resolves hidden toctrees into ``env.tocs`` for navigation but
    strips them from the page body. We do not re-inject them for MDX
    rendering — ``:hidden:`` means the sidebar/cards should not appear
    on the page itself (use sphinx-design grids or a visible toctree
    when you want in-page card navigation).
    """
    return


class MintlifyBuilder(Builder):
    name = "mintlify"
    format = "mdx"
    epilog = "Mintlify MDX pages were written to %(outdir)s."
    out_suffix = ".mdx"
    allow_parallel = True
    supported_image_types: ClassVar[list[str]] = [
        "image/svg+xml",
        "image/png",
        "image/gif",
        "image/jpeg",
        "image/webp",
    ]
    supported_remote_images = True

    def init(self) -> None:
        self.images: dict[str, str] = {}
        self.docwriter_settings: dict[str, Any] = {}

    def get_outdated_docs(self) -> Iterator[str]:
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            target = path.join(self.outdir, docname + self.out_suffix)
            try:
                target_mtime = path.getmtime(target)
            except OSError:
                target_mtime = 0
            try:
                source_mtime = path.getmtime(self.env.doc2path(docname))
            except OSError:
                source_mtime = 0
            if source_mtime > target_mtime:
                yield docname

    def get_target_uri(self, docname: str, typ: str | None = None) -> str:
        base = self.base_path
        if base is not None:
            return str(base / docname)
        return docname

    def get_relative_uri(self, from_: str, to: str, typ: str | None = None) -> str:
        base = self.base_path
        if base is not None:
            return str(base / to)
        from_dir = posixpath.dirname(from_)
        rel = to if not from_dir else posixpath.relpath(to, from_dir)
        if not rel.startswith((".", "/")):
            rel = f"./{rel}"
        return rel

    @property
    def base_path(self) -> PurePosixPath | None:
        """Mount-point for generated URLs (``mintlify_base_path``).

        ``None`` (default) → emit Sphinx-style relative links that work
        under any deployment prefix.

        ``PurePosixPath("/sandboxes/sdk")`` → emit absolute links
        rooted at that prefix; useful when the build embeds into a
        larger Mintlify site that uses absolute paths elsewhere.
        """
        raw = self.config.mintlify_base_path or ""
        if not raw.strip():
            return None
        return PurePosixPath("/", raw)

    def prepare_writing(self, docnames: set[str]) -> None:
        return None

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        self.post_process_images(doctree)
        inject_hidden_toctrees(self, docname, doctree)
        ctx = TranslationContext(builder=self, docname=docname)
        # Publish base_path on the contextvar so url_for() throughout
        # the node tree picks the right mode without needing the
        # builder threaded through every helper.
        token = urls.base_path.set(self.base_path)
        try:
            root = TranslationNode.from_docutils(doctree, parent=None, ctx=ctx)
            body = root.render()
        finally:
            urls.base_path.reset(token)
        outfilename = path.join(self.outdir, docname + self.out_suffix)
        ensuredir(path.dirname(outfilename))
        # Fail loud: a missing/half-written page is a build error, not a
        # warning. Otherwise Sphinx exits 0 with an incomplete site.
        with open(outfilename, "w", encoding="utf-8") as out:
            out.write(body)

    def copy_image_files(self) -> None:
        if not self.images:
            return
        image_dir = self.config.mintlify_image_dir
        target_root = path.join(self.outdir, image_dir)
        ensuredir(target_root)
        for src, target_name in self.images.items():
            source = path.join(self.srcdir, src)
            destination = path.join(target_root, target_name)
            ensuredir(path.dirname(destination))
            try:
                with (
                    open(source, "rb") as fp_in,
                    open(destination, "wb") as fp_out,
                ):
                    fp_out.write(fp_in.read())
            except OSError as exc:
                logger.warning("cannot copy image %s: %s", source, exc)

    def copy_static_files(self) -> None:
        static_paths = list(self.config.mintlify_static_path)
        if not static_paths:
            return
        target_root = path.join(self.outdir, "static")
        ensuredir(target_root)
        for entry in static_paths:
            source = path.join(self.confdir, entry)
            if not path.isdir(source):
                continue
            for root, _dirs, files in os.walk(source):
                rel = path.relpath(root, source)
                target_dir = target_root if rel == "." else path.join(target_root, rel)
                ensuredir(target_dir)
                for name in files:
                    if name.endswith(".css"):
                        continue
                    src_file = path.join(root, name)
                    dst_file = path.join(target_dir, name)
                    try:
                        with (
                            open(src_file, "rb") as fp_in,
                            open(dst_file, "wb") as fp_out,
                        ):
                            fp_out.write(fp_in.read())
                    except OSError as exc:
                        logger.warning("cannot copy static file %s: %s", src_file, exc)

    def write_docs_json(self) -> None:
        data = build_docs_json(self.env, self.config)
        target = path.join(self.outdir, "docs.json")
        ensuredir(path.dirname(target))
        with open(target, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
            fp.write("\n")

    def _cleanup_build_artifacts(self) -> None:
        """Drop intermediate files that should not ship with Mintlify output."""
        self._cleanup_html_extension_static()
        self._cleanup_in_tree_doctrees()

    def _cleanup_html_extension_static(self) -> None:
        """Drop CSS/JS trees written by HTML-only extensions (e.g. sphinx-design).

        Those extensions hook ``builder-inited`` and copy assets into
        ``outdir`` for HTML rendering. The Mintlify builder translates
        their directives to MDX components instead, so the files are
        unused noise in the published output.
        """
        try:
            entries = os.listdir(self.outdir)
        except OSError:
            return
        for name in entries:
            if not (name.startswith("_sphinx_") and name.endswith("_static")):
                continue
            target = path.join(self.outdir, name)
            if path.isdir(target):
                shutil.rmtree(target)

    def _cleanup_in_tree_doctrees(self) -> None:
        """Remove pickled doctrees when Sphinx stores them under ``outdir``.

        The default ``sphinx-build`` layout places ``.doctrees`` inside
        ``outdir``. That cache is build-only; Mintlify deploys should not
        include it. When ``-d`` points outside ``outdir``, leave it alone
        so incremental rebuilds keep their cache.
        """
        doctreedir = path.abspath(self.doctreedir)
        outdir = path.abspath(self.outdir)
        if doctreedir != outdir and not doctreedir.startswith(outdir + path.sep):
            return
        if path.isdir(doctreedir):
            shutil.rmtree(doctreedir)

    def finish(self) -> None:
        self.copy_image_files()
        self.copy_static_files()
        self.write_docs_json()
        self._cleanup_build_artifacts()
