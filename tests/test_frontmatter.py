"""Unit tests for YAML frontmatter value formatting."""

from __future__ import annotations

import pytest
import yaml

from sphinx_mintlify_output.frontmatter import format_yaml_value


def test_scalar_string_plain() -> None:
    assert format_yaml_value("hello") == "hello"


def test_scalar_string_needs_quoting() -> None:
    out = format_yaml_value("has: colon")
    assert out.startswith('"') and out.endswith('"')
    assert yaml.safe_load(out) == "has: colon"


def test_bool() -> None:
    assert format_yaml_value(True) == "true"
    assert format_yaml_value(False) == "false"


def test_int_and_float() -> None:
    assert format_yaml_value(42) == "42"
    assert format_yaml_value(3.5) == "3.5"


def test_none() -> None:
    assert format_yaml_value(None) == "null"


def test_list_of_strings_roundtrips() -> None:
    out = format_yaml_value(["python", "sphinx", "mintlify"])
    assert yaml.safe_load(out) == ["python", "sphinx", "mintlify"]


def test_dict_roundtrips() -> None:
    value = {"author": "Alice", "year": 2026}
    out = format_yaml_value(value)
    assert yaml.safe_load(out) == value


def test_nested_dict_in_list_roundtrips() -> None:
    value = [{"name": "Alice", "role": "author"}, {"name": "Bob"}]
    out = format_yaml_value(value)
    assert yaml.safe_load(out) == value


def test_tuple_renders_as_list() -> None:
    out = format_yaml_value(("a", "b"))
    assert yaml.safe_load(out) == ["a", "b"]


def test_unicode_preserved() -> None:
    out = format_yaml_value(["café", "naïve"])
    assert yaml.safe_load(out) == ["café", "naïve"]


@pytest.mark.parametrize(
    "ambiguous",
    [
        "true",
        "True",
        "TRUE",
        "false",
        "yes",
        "no",
        "on",
        "off",
        "y",
        "n",
        "null",
        "Null",
        "~",
        ".nan",
        ".inf",
        "-.inf",
    ],
)
def test_yaml_ambiguous_keyword_round_trips_as_string(ambiguous: str) -> None:
    out = format_yaml_value(ambiguous)
    assert yaml.safe_load(out) == ambiguous


@pytest.mark.parametrize(
    "numeric_like",
    ["1", "1.5", "-3", "+0", ".5", "1e10", "1.5e-2"],
)
def test_yaml_numeric_string_round_trips_as_string(numeric_like: str) -> None:
    out = format_yaml_value(numeric_like)
    assert yaml.safe_load(out) == numeric_like


def test_empty_string_quoted() -> None:
    out = format_yaml_value("")
    assert yaml.safe_load(out) == ""


def test_plain_word_stays_unquoted() -> None:
    # Sanity: non-ambiguous strings still emit without quotes.
    assert format_yaml_value("hello") == "hello"
    assert format_yaml_value("Some Title Here") == "Some Title Here"
