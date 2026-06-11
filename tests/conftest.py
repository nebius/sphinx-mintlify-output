"""Pytest fixtures for sphinx-mintlify-output tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest_plugins = ("sphinx.testing.fixtures",)


@pytest.fixture(scope="session")
def rootdir() -> Path:
    return Path(__file__).parent / "roots"


@pytest.fixture(autouse=True)
def clear_build_dir(request):
    """Ensure each Sphinx test starts with an empty _build directory."""
    yield
    marker = request.node.get_closest_marker("sphinx")
    if marker is None:
        return
    app = request.node.funcargs.get("app")
    if app is None:
        return
    outdir = Path(app.outdir)
    if outdir.exists():
        shutil.rmtree(outdir, ignore_errors=True)
    doctreedir = Path(app.doctreedir)
    if doctreedir.exists():
        shutil.rmtree(doctreedir, ignore_errors=True)
