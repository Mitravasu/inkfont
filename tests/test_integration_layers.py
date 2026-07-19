"""Integration test: validate the post-Create-Glyph-Layers document shape.

Loads ``tests/fixtures/sample.svg`` with ``lxml`` (CI-friendly; inkex is not
on PyPI). Walks the tree with :func:`glyph_naming.is_glyph_layer` and asserts
the *shape* of a document that the user has built a couple of letters in:
two glyph layers, each containing a ``template_base`` child plus at least one
non-template path. This validates Steps 7 & 8 without invoking Inkscape.
"""

from pathlib import Path

from lxml import etree

from lib.glyph_naming import is_glyph_layer

FIXTURE = Path(__file__).parent / "fixtures" / "sample.svg"

INK_NS = "http://www.inkscape.org/namespaces/inkscape"
SVG_NS = "http://www.w3.org/2000/svg"
SODIPODI_NS_CANDIDATES = (
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd",
)
NSMAP = {"svg": SVG_NS, "ink": INK_NS}


def _load_layers():
    tree = etree.parse(str(FIXTURE))
    root = tree.getroot()
    layers = []
    for g in root.iterfind(f"{{{SVG_NS}}}g"):
        label = g.get(f"{{{INK_NS}}}label")
        if label and is_glyph_layer(label):
            layers.append((label, g))
    return layers


def test_two_glyph_layers_present():
    layers = _load_layers()
    assert {name for name, _ in layers} == {"glyph_A", "glyph_i"}


def test_each_layer_has_template_base_and_built_path():
    for name, layer in _load_layers():
        paths = layer.findall(f"{{{SVG_NS}}}path")
        assert paths, f"layer {name} has no paths"

        template = [p for p in paths if p.get(f"{{{INK_NS}}}label") == "template_base"]
        built = [p for p in paths if p.get(f"{{{INK_NS}}}label") != "template_base"]
        assert template, f"layer {name} missing template_base child"
        assert built, f"layer {name} has no built (non-template) path"