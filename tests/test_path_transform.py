"""Tests for path_transform.flip_and_scale (pure)."""

import pytest

from lib.path_transform import flip_and_scale


def _nums(s: str):
    """Return the list of numeric tokens in a d-string (ignoring letters)."""
    import re

    return [float(m) for m in re.findall(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)", s)]


def test_square_above_baseline_stays_above_baseline():
    # 100x100 square sitting from y=100 to y=200 (above baseline at 800).
    d = "M 0 100 L 100 100 L 100 200 L 0 200 Z"
    out = flip_and_scale(d, baseline_y=800, scale=1.0)
    ys = [y for i, y in enumerate(_nums(out)) if i % 2 == 1]
    # After flip: font_y = 800 - svg_y, so y=100 -> 700, y=200 -> 600.
    assert sorted(ys) == [600.0, 600.0, 700.0, 700.0]


def test_scale_doubles_coordinates():
    d = "M 10 20 L 30 40"
    out = flip_and_scale(d, baseline_y=1000, scale=2.0)
    xs = [x for i, x in enumerate(_nums(out)) if i % 2 == 0]
    ys = [y for i, y in enumerate(_nums(out)) if i % 2 == 1]
    # x: 10->20, 30->60 ; y: 1000-20=980 *2=1960 ; 1000-40=960 *2=1920
    assert xs == [20.0, 60.0]
    assert ys == [1960.0, 1920.0]


def test_known_input_known_output():
    # Simple line: M 0 100 L 50 100 with baseline 800, scale 1.
    out = flip_and_scale("M 0 100 L 50 100", baseline_y=800, scale=1.0)
    assert out == "M 0 700 L 50 700"


def test_horizontal_and_vertical_commands():
    # H/V get x scaled, y flipped.
    out = flip_and_scale("M 0 100 H 200 V 300", baseline_y=800, scale=1.0)
    # M 0 100 -> M 0 700 ; H 200 -> H 200 ; V 300 -> V 500
    assert out == "M 0 700 H 200 V 500"


def test_relative_pair():
    # m 10 20: relative move emits dx*scale, -dy*scale (sign-flipped dy).
    out = flip_and_scale("m 10 20", baseline_y=800, scale=1.0)
    assert out == "m 10 -20"


def test_relative_h_v():
    # M 0 100 then h 50 (dx=50) then v 20 (dy=20)
    out = flip_and_scale("M 0 100 h 50 v 20", baseline_y=800, scale=1.0)
    # M -> M 0 700 ; h 50 -> +50 x = 50 ; v 20 -> svg_y=120 -> font 680
    assert out == "M 0 700 h 50 v -20"


def test_z_returns_to_start():
    # After Z, current position returns to last moveto.
    d = "M 0 100 L 100 100 Z L 200 200"
    out = flip_and_scale(d, baseline_y=800, scale=1.0)
    # M 0 700 L 100 700 Z L 200 600
    assert out == "M 0 700 L 100 700 Z L 200 600"


def test_multiple_moveto_groups_become_linetos():
    # After the first M coordinate pair, subsequent pairs are linetos.
    d = "M 0 100 50 100 100 200"
    out = flip_and_scale(d, baseline_y=800, scale=1.0)
    assert out == "M 0 700 L 50 700 L 100 600"


def test_arc_command_raises():
    with pytest.raises(ValueError):
        flip_and_scale("M 0 0 A 50 50 0 0 1 100 100", baseline_y=800)


def test_number_without_command_raises():
    with pytest.raises(ValueError):
        flip_and_scale("100 200", baseline_y=800)