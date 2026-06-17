"""Tests for Stage 4 — admonitions and sphinx-design containers."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_note_warning_tip(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Note>\nA note body.\n</Note>" in text
    assert "<Tip>\nA tip body.\n</Tip>" in text
    assert "<Warning>\nA warning body.\n</Warning>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_hint_aliases_to_tip(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Tip>\nA hint body.\n</Tip>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_caution_attention_important(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Warning>\nPay attention.\n</Warning>" in text
    assert "<Warning>\nBe careful.\n</Warning>" in text
    assert "<Info>\nImportant matter.\n</Info>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_danger_error(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Danger>\nDanger ahead.\n</Danger>" in text
    assert "<Danger>\nError case.\n</Danger>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_seealso(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Info>\nSee the other page.\n</Info>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_generic_admonition_with_title(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert '<Note title="Custom Title">' in text
    assert "Generic body." in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_versionmodified_deprecated(app) -> None:
    app.build()
    text = (Path(app.outdir) / "index.mdx").read_text("utf-8")
    assert "<Info>" in text
    assert "<Warning>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_design_card(app) -> None:
    app.build()
    text = (Path(app.outdir) / "design.mdx").read_text("utf-8")
    assert '<Card title="Card title">' in text
    assert "Card body paragraph." in text
    assert "</Card>" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_design_tab_set(app) -> None:
    app.build()
    text = (Path(app.outdir) / "design.mdx").read_text("utf-8")
    assert "<Tabs sync={false}>" in text
    assert '<Tab title="Python">' in text
    assert "Python content." in text
    assert '<Tab title="TypeScript">' in text
    assert "</Tabs>" in text
    assert "<CodeGroup sync={false}>" in text
    assert "```bash bash" in text
    assert "echo hi" in text


@pytest.mark.sphinx("mintlify", testroot="admonitions")
def test_design_dropdown(app) -> None:
    app.build()
    text = (Path(app.outdir) / "design.mdx").read_text("utf-8")
    assert '<Accordion title="Hidden details">' in text
    assert "Some details." in text
    assert "</Accordion>" in text
