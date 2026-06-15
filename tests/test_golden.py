"""Byte-for-byte regression check: compare every test root's build output
against the captured corpus under ``tests/golden/``.

The corpus is the contract. Anything that changes the rendered MDX or
``docs.json`` must either be intentional (refresh via
``uv run python tests/capture_golden.py``) or a bug.

Skip a test root from the diff by adding it to ``SKIP_ROOTS`` with a
reason — e.g. when iterating on the new translator and a particular
testroot isn't yet at parity.
"""

from __future__ import annotations

from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"
ROOTS_DIR = Path(__file__).parent / "roots"

# Map: <testroot-name> -> reason. Anything listed here is xfail/skipped
# during the new-translator transition; entries must be removed before
# the migration is considered done.
SKIP_ROOTS: dict[str, str] = {}


def _testroots() -> list[str]:
    return sorted(
        p.name.removeprefix("test-")
        for p in ROOTS_DIR.iterdir()
        if p.is_dir() and p.name.startswith("test-")
    )


def _iter_relative(out_dir: Path) -> list[Path]:
    """List output files relative to ``out_dir``, skipping Sphinx caches."""
    out: list[Path] = []
    for p in out_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(out_dir)
        if any(part == ".doctrees" for part in rel.parts):
            continue
        out.append(rel)
    return sorted(out)


def _diff(actual: Path, expected: Path) -> str:
    """Return a one-line summary of how ``actual`` differs from ``expected``."""
    if not expected.exists():
        return f"unexpected new file: {actual.name}"
    a = actual.read_bytes()
    b = expected.read_bytes()
    if a == b:
        return ""
    if not a:
        return "actual is empty"
    if not b:
        return "expected is empty"
    # Find first differing line for a readable failure.
    a_lines = a.decode("utf-8", errors="replace").splitlines()
    b_lines = b.decode("utf-8", errors="replace").splitlines()
    for idx, (al, bl) in enumerate(zip(a_lines, b_lines, strict=False), start=1):
        if al != bl:
            return f"line {idx}: actual={al!r} expected={bl!r}"
    return (
        f"length mismatch: actual={len(a_lines)} lines, expected={len(b_lines)} lines"
    )


@pytest.fixture(params=_testroots(), ids=lambda p: p)
def testroot(request: pytest.FixtureRequest) -> str:
    name = request.param
    if name in SKIP_ROOTS:
        pytest.skip(f"{name}: {SKIP_ROOTS[name]}")
    return name


@pytest.mark.sphinx("mintlify")
def test_golden_corpus_matches(
    testroot: str,
    make_app: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    from sphinx.testing.fixtures import SphinxTestApp

    src = ROOTS_DIR / f"test-{testroot}"
    if (src / "docs").is_dir() and (src / "docs" / "conf.py").is_file():
        src = src / "docs"
    out = tmp_path / "build"
    app = SphinxTestApp(buildername="mintlify", srcdir=src, builddir=out)  # type: ignore[arg-type]
    try:
        app.build()
    finally:
        app.cleanup()

    expected_root = GOLDEN_DIR / f"test-{testroot}"
    actual_root = Path(app.outdir)

    expected_files = set(_iter_relative(expected_root))
    actual_files = set(_iter_relative(actual_root))

    missing = expected_files - actual_files
    extra = actual_files - expected_files
    assert not missing, f"missing files vs golden: {sorted(missing)}"
    assert not extra, f"extra files not in golden: {sorted(extra)}"

    mismatches: list[str] = []
    for rel in sorted(expected_files):
        diff = _diff(actual_root / rel, expected_root / rel)
        if diff:
            mismatches.append(f"  {rel}: {diff}")
    assert not mismatches, "\n" + "\n".join(mismatches)
