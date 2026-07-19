"""Assemble an SVG font document from glyph records.

Stdlib only (``xml.etree.ElementTree``). No inkex. Imports nothing from the
project.

The output is a complete ``<svg>`` document containing a single ``<font>``
element, as consumed by FontForge's ``File → Import → SVG Font``.
"""

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

# SVG font namespace. ElementTree will prefix it as ``ns0`` by default; we
# rewrite those prefixes to the conventional ones below.
_SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NS)


@dataclass
class GlyphRecord:
    """One glyph's worth of data for the assembler.

    - ``unicode``: the single character this glyph represents (e.g. ``"A"``).
    - ``name``: the glyph-name attribute (often the same as ``unicode`` for
      ASCII, or a descriptive name).
    - ``d``: the path data, or ``None``/empty for a space/empty glyph.
    - ``advance``: ``horiz-adv-x`` in font units.
    """
    unicode: str
    name: str
    d: str | None = None
    advance: int = 1000


@dataclass
class FontFaceAttrs:
    """Attributes for the ``<font-face>`` element. All optional except
    ``font_family`` and ``units_per_em``.
    """
    font_family: str = "NewFont"
    units_per_em: int = 1000
    ascent: int | None = None
    descent: int | None = None
    cap_height: int | None = None
    x_height: int | None = None
    font_weight: str | None = None
    font_style: str | None = None
    copyright: str | None = None


def build_svg_font(records, font_face_attrs, default_advance) -> str:
    """Build a complete SVG font document string.

    - ``records``: iterable of :class:`GlyphRecord`.
    - ``font_face_attrs``: :class:`FontFaceAttrs`.
    - ``default_advance``: ``horiz-adv-x`` for the ``<font>`` element and the
      ``<missing-glyph>`` fallback.
    """
    if isinstance(font_face_attrs, dict):
        font_face_attrs = FontFaceAttrs(**font_face_attrs)

    svg = ET.Element("svg", xmlns=_SVG_NS)

    font = ET.SubElement(svg, "font", {
        "id": font_face_attrs.font_family or "font",
        "horiz-adv-x": str(default_advance),
    })

    face_attrs = {
        "font-family": font_face_attrs.font_family,
        "units-per-em": str(font_face_attrs.units_per_em),
    }
    if font_face_attrs.ascent is not None:
        face_attrs["ascent"] = str(font_face_attrs.ascent)
    if font_face_attrs.descent is not None:
        face_attrs["descent"] = str(font_face_attrs.descent)
    if font_face_attrs.cap_height is not None:
        face_attrs["cap-height"] = str(font_face_attrs.cap_height)
    if font_face_attrs.x_height is not None:
        face_attrs["x-height"] = str(font_face_attrs.x_height)
    if font_face_attrs.font_weight is not None:
        face_attrs["font-weight"] = str(font_face_attrs.font_weight)
    if font_face_attrs.font_style is not None:
        face_attrs["font-style"] = str(font_face_attrs.font_style)
    ET.SubElement(font, "font-face", face_attrs)

    ET.SubElement(font, "missing-glyph", {"horiz-adv-x": str(default_advance)})

    for rec in records:
        glyph_attrs = {
            "unicode": rec.unicode,
            "glyph-name": rec.name,
            "horiz-adv-x": str(rec.advance),
        }
        if rec.d:
            glyph_attrs["d"] = rec.d
        ET.SubElement(font, "glyph", glyph_attrs)

    # Pretty-ish indent and serialize.
    _indent(svg)
    body = ET.tostring(svg, encoding="unicode")
    return '<?xml version="1.0" standalone="no"?>\n' + body + "\n"


def _indent(elem, level=0):
    """In-place pretty-print indent (stdlib doesn't ship one before 3.9)."""
    pad = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = pad + "  "
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = pad
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = pad