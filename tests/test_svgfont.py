"""Tests for svgfont.build_svg_font (pure, stdlib only)."""

from xml.etree import ElementTree as ET

from lib.svgfont import (
    FontFaceAttrs,
    GlyphRecord,
    build_svg_font,
)

NS = "{http://www.w3.org/2000/svg}"


def _parse(svg_str):
    return ET.fromstring(svg_str)


def test_build_font_valid_xml():
    out = build_svg_font(
        records=[GlyphRecord(unicode="A", name="A", d="M0 0", advance=1000)],
        font_face_attrs=FontFaceAttrs(font_family="Test", units_per_em=1000),
        default_advance=1000,
    )
    _parse(out)  # raises on invalid XML


def test_font_has_correct_horiz_adv_x():
    out = build_svg_font([], FontFaceAttrs(font_family="T"), default_advance=750)
    font = _parse(out).find(f"{NS}font")
    assert font.get("horiz-adv-x") == "750"


def test_font_face_attributes():
    ffa = FontFaceAttrs(
        font_family="MyFont",
        units_per_em=1000,
        ascent=800,
        descent=-200,
        cap_height=700,
        x_height=500,
        font_weight="regular",
        font_style="normal",
    )
    out = build_svg_font([], ffa, default_advance=1000)
    face = _parse(out).find(f"{NS}font/{NS}font-face")
    assert face.get("font-family") == "MyFont"
    assert face.get("units-per-em") == "1000"
    assert face.get("ascent") == "800"
    assert face.get("descent") == "-200"
    assert face.get("cap-height") == "700"
    assert face.get("x-height") == "500"
    assert face.get("font-weight") == "regular"
    assert face.get("font-style") == "normal"


def test_glyphs_have_correct_attributes():
    records = [
        GlyphRecord(unicode="A", name="A", d="M0 0 L1 1", advance=1000),
        GlyphRecord(unicode="B", name="B", d=None, advance=500),  # empty
        GlyphRecord(unicode=" ", name="space", d="", advance=250),  # space
    ]
    out = build_svg_font(records, FontFaceAttrs(), default_advance=1000)
    glyphs = _parse(out).findall(f"{NS}font/{NS}glyph")
    assert len(glyphs) == 3
    a, b, space = glyphs
    assert a.get("unicode") == "A"
    assert a.get("glyph-name") == "A"
    assert a.get("horiz-adv-x") == "1000"
    assert a.get("d") == "M0 0 L1 1"
    assert "d" not in b.attrib
    assert b.get("horiz-adv-x") == "500"
    assert "d" not in space.attrib
    assert space.get("unicode") == " "
    assert space.get("horiz-adv-x") == "250"


def test_missing_glyph_present():
    out = build_svg_font([], FontFaceAttrs(), default_advance=1000)
    root = _parse(out)
    mg = root.find(f"{NS}font/{NS}missing-glyph")
    assert mg is not None
    assert mg.get("horiz-adv-x") == "1000"