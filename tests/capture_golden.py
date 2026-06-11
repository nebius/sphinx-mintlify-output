"""One-shot script: snapshot every test root's MDX output as golden files.

Run after a change in the translator that's known-good, to refresh the
golden corpus that ``tests/test_golden.py`` diffs against.

    uv run python tests/capture_golden.py

Idempotent — overwrites everything under ``tests/golden/``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
GOLDEN_DIR = ROOT / "golden"
ROOTS_DIR = ROOT / "roots"


def list_test_roots() -> list[Path]:
    return sorted(
        p for p in ROOTS_DIR.iterdir() if p.is_dir() and p.name.startswith("test-")
    )


def build_one(src: Path, dst: Path) -> None:
    name = src.name
    with tempfile.TemporaryDirectory(prefix=f"mintlify-golden-{name}-") as tmp:
        out = Path(tmp) / "build"
        result = subprocess.run(
            [
                "uv",
                "run",
                "sphinx-build",
                "-b",
                "mintlify",
                "-q",
                str(src),
                str(out),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(f"\n[capture] {name} FAILED\n")
            sys.stderr.write(result.stderr)
            sys.exit(result.returncode)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(
            out, dst, ignore=shutil.ignore_patterns(".doctrees", "*.pickle")
        )


def main() -> None:
    roots = list_test_roots()
    GOLDEN_DIR.mkdir(exist_ok=True)
    for src in roots:
        dst = GOLDEN_DIR / src.name
        print(f"[capture] {src.name} -> {dst.relative_to(ROOT.parent)}")
        build_one(src, dst)
    print(f"[capture] done, {len(roots)} test roots captured")


if __name__ == "__main__":
    main()
