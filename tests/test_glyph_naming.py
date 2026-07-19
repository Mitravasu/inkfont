"""Tests for glyph_naming (pure, no inkex)."""

from lib.charsets import PRESETS
from lib.glyph_naming import (
    char_from_layer_name,
    is_glyph_layer,
    layer_name_for_char,
)


def test_readable_names():
    assert layer_name_for_char("A") == "glyph_A"
    assert layer_name_for_char("z") == "glyph_z"
    assert layer_name_for_char("0") == "glyph_0"


def test_codepoint_names():
    assert layer_name_for_char(" ") == "glyph_U+0020"
    assert layer_name_for_char("é") == "glyph_U+00E9"
    assert layer_name_for_char("\n") == "glyph_U+000A"


def test_round_trip_coding_core():
    for c in PRESETS["Coding — core"]:
        assert char_from_layer_name(layer_name_for_char(c)) == c


def test_round_trip_non_ascii_samples():
    for c in ("é", "€", " ", "\n", "–", "“", "¿"):
        assert char_from_layer_name(layer_name_for_char(c)) == c


def test_is_glyph_layer():
    assert is_glyph_layer("glyph_A") is True
    assert is_glyph_layer("glyph_z") is True
    assert is_glyph_layer("glyph_U+00E9") is True
    assert is_glyph_layer("Layer 1") is False
    assert is_glyph_layer("not_a_glyph") is False
    assert is_glyph_layer("glyph_") is False
    assert is_glyph_layer("") is False


def test_char_from_layer_name_invalid():
    assert char_from_layer_name("not_a_glyph") is None
    assert char_from_layer_name("glyph_AB") is None  # two chars, not codepoint
    assert char_from_layer_name("glyph_U+XYZ") is None


def test_single_char_only():
    import pytest

    with pytest.raises(ValueError):
        layer_name_for_char("ab")