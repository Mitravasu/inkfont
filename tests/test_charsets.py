"""Tests for charsets.PRESETS."""

from lib.charsets import PRESETS


def test_coding_core_contains_key_chars():
    s = PRESETS["Coding — core"]
    for c in ("A", "a", "0", " ", "`", "_"):
        assert c in s, f"missing {c!r}"
    # every punctuation in the coding set
    for c in "~!@#$%^&*()-=+[]{}|\\;:'\",.<>/?":
        assert c in s, f"missing punct {c!r}"


def test_uppercase_exact():
    assert PRESETS["Uppercase"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def test_lowercase_exact():
    assert PRESETS["Lowercase"] == "abcdefghijklmnopqrstuvwxyz"


def test_digits_exact():
    assert PRESETS["Digits"] == "0123456789"


def test_no_preset_has_duplicates():
    for name, s in PRESETS.items():
        assert len(s) == len(set(s)), f"duplicate chars in preset {name!r}: {s!r}"