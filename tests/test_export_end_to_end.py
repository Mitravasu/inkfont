"""End-to-end exporter test: runs the real pure modules against the fixture.

This mirrors what :mod:`commands.export_svg_font` does, but using ``lxml``
instead of ``inkex`` so it runs in CI without Inkscape installed. It exercises
:mod:`path_transform`, :mod:`svgfont`, and :mod:`glyph_naming` on the real
``tests/fixtures/sample.svg`` and asserts the resulting SVG font document is
shaped correctly.
"""

from pathlib import Path

from lxml import etree

from lib.glyph_naming import char_from_layer_name, is_glyph_layer
from lib.path_transform import flip_and_scale
from lib.svgfont import FontFaceAttrs, GlyphRecord, build_svg_font

FIXTURE = Path(__file__).parent / "fixtures" / "sample.svg"

INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SVG_NS = "http://www.w3.org/2000/svg"
NS = f"{{{SVG_NS}}}"
INK = f"{{{INK_NS}}}"


def _read_baseline_y(root):
    """Replicate guides.read_named_guides for the fixture (lxml, no inkex)."""
    # Inkscape sodipodi:guide position is stored pre-1.0: y is from the BOTTOM
    # of the viewbox. inkex's Guide.position flips it back to y-down-from-top.
    viewbox_h = float(root.get("viewBox").split()[3])
    # The fixture may use either of two sodipodi namespace URIs; accept both.
    for uri in (
        "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd",
    ):
        for guide in root.iter(f"{{{uri}}}guide"):
            label = guide.get(f"{INK}label")
            if not label:
                continue
            x, y = [float(v) for v in guide.get("position").split(",")]
            # sodipodi position y is measured from the BOTTOM (pre-1.0).
            y_down = viewbox_h - y
            if label == "baseline":
                return y_down
    raise AssertionError("no baseline guide in fixture")


def _collect_records(root, baseline_y, scale=1.0):
    records = []
    for layer in root.iter(f"{NS}g"):
        label = layer.get(f"{INK}label")
        if not label or not is_glyph_layer(label):
            continue
        char = char_from_layer_name(label)
        if char is None:
            continue
        d_parts = []
        for path in layer.findall(f"{NS}path"):
            if path.get(f"{INK}label") == "template_base":
                continue
            d = path.get("d")
            if d:
                d_parts.append(flip_and_scale(d, baseline_y, scale))
        records.append(GlyphRecord(
            unicode=char,
            name=label[len("glyph_"):],
            d=" ".join(d_parts) if d_parts else None,
            advance=1000,
        ))
    return records


def test_export_end_to_end():
    root = etree.parse(str(FIXTURE)).getroot()
    baseline_y = _read_baseline_y(root)
    records = _collect_records(root, baseline_y, scale=1.0)

    font_xml = build_svg_font(
        records,
        FontFaceAttrs(font_family="Test", units_per_em=1000),
        default_advance=1000,
    )

    out_root = etree.fromstring(font_xml.encode("utf-8"))
    glyphs = out_root.findall(f"./{NS}font/{NS}glyph")
    by_char = {g.get("unicode"): g for g in glyphs}

    # Both glyphs present
    assert "A" in by_char, font_xml
    assert "i" in by_char, font_xml

    # A glyph: Y-flipped version of the fixture's A path.
    # Fixture A: "M 100 800 L 200 100 L 300 800 Z M 150 500 L 250 500"
    # baseline_y=800, scale=1: font_y = 800 - svg_y.
    #   (100,800)->(100,0) (200,100)->(200,700) (300,800)->(300,0)
    #   (150,500)->(150,300) (250,500)->(250,300)
    expected_a = "M 100 0 L 200 700 L 300 0 Z M 150 300 L 250 300"
    assert by_char["A"].get("d") == expected_a, by_char["A"].get("d")

    # i glyph: stem + dot subpaths concatenated.
    d_i = by_char["i"].get("d")
    assert d_i is not None
    # Stem from (460,300)-(540,800); dot from (460,100)-(540,200).
    # After flip with baseline 800:
    #   stem: y=300->500, y=800->0
    #   dot : y=100->700, y=200->600
    assert "460 500" in d_i and "540 0" in d_i, d_i  # stem corners
    assert "460 700" in d_i and "540 600" in d_i, d_i  # dot corners
    # Both subpaths should be present (two M commands).
    assert d_i.count("M") >= 2

    # No template_base data leaked: the original rect's coords are
    #   M 0 0 L 500 0 L 500 1000 L 0 1000 Z -> would contain "500 1000" raw
    #   (which would flip to "500 -200"). The rect path is square at origin;
    #   its signature corner is "500 1000" pre-flip -> "500 -200" post-flip.
    #   Neither glyph should contain that signature.
    assert "500 -200" not in by_char["A"].get("d", "")
    assert "500 -200" not in by_char["i"].get("d", "")


def test_export_empty_glyph_has_no_d():
    """A glyph layer with only a template_base produces a glyph with no d."""
    # Build a synthetic record list mirroring what the exporter would emit
    # for an empty layer (e.g. space).
    records = [GlyphRecord(unicode=" ", name="space", d=None, advance=500)]
    font_xml = build_svg_font(
        records, FontFaceAttrs(font_family="T", units_per_em=1000),
        default_advance=1000,
    )
    root = etree.fromstring(font_xml.encode("utf-8"))
    glyphs = root.findall(f"./{NS}font/{NS}glyph")
    space = [g for g in glyphs if g.get("unicode") == " "][0]
    assert "d" not in space.attrib