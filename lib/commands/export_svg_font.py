"""Export SVG Font command — walks glyph layers and writes an SVG font file.

Dialog params:
- ``family``, ``copyright``, ``weight``, ``italic``: font metadata.
- ``default_advance``: ``horiz-adv-x`` for the font and missing-glyph.
- ``output_path``: where to write the SVG font file.

The effect():
1. Reads named guides via :func:`guides.read_named_guides` → baseline Y.
2. Computes ``scale = em_size / doc_height`` (defensively; usually 1.0).
3. For each layer whose name matches :func:`glyph_naming.is_glyph_layer`:
   - Collects child ``<path>`` elements whose ``inkscape:label != "template_base"``.
   - Concatenates their ``d`` attributes, transforms via
     :func:`path_transform.flip_and_scale`.
   - Builds a :class:`GlyphRecord` using
     :func:`glyph_naming.char_from_layer_name`.
4. Calls :func:`svgfont.build_svg_font`.
5. Writes the string to ``output_path``.

Thin glue — all real logic was tested in Steps 4 and 5.
"""

from pathlib import Path

from inkex import EffectExtension

from ..glyph_naming import char_from_layer_name, is_glyph_layer
from ..guides import read_named_guides
from ..path_transform import flip_and_scale
from ..svgfont import FontFaceAttrs, GlyphRecord, build_svg_font


class ExportSvgFont(EffectExtension):
    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--family", type=str, default="NewFont")
        self.arg_parser.add_argument("--copyright", type=str, default="")
        self.arg_parser.add_argument("--weight", type=str, default="regular")
        self.arg_parser.add_argument("--italic", type=bool, default=False)
        self.arg_parser.add_argument(
            "--default_advance", type=int, default=1000,
            help="Default horiz-adv-x (font units).",
        )
        self.arg_parser.add_argument(
            "--output_path", type=str, default="typeface.svg",
            help="Output SVG font file path.",
        )
        # em_size is read from the document, but we accept an override for
        # unusual cases.
        self.arg_parser.add_argument(
            "--em_size", type=int, default=0,
            help="Em size override (0 = read from document width).",
        )

    def effect(self):
        guides = read_named_guides(self.svg)
        if "baseline" not in guides:
            raise RuntimeError(
                "No 'baseline' guide found. Run 'Setup Canvas' first."
            )
        baseline_y = guides["baseline"][1]

        em = self.options.em_size or int(self.svg.viewbox_height) or 1000
        doc_height = self.svg.viewbox_height or em
        scale = em / doc_height if doc_height else 1.0

        records = []
        for layer in self.svg.findall("svg:g"):
            label = layer.get("inkscape:label")
            if not label or not is_glyph_layer(label):
                continue
            char = char_from_layer_name(label)
            if char is None:
                continue

            d_parts = []
            for path in layer.findall("svg:path"):
                if path.get("inkscape:label") == "template_base":
                    continue
                d = path.get("d")
                if d:
                    d_parts.append(flip_and_scale(d, baseline_y, scale))

            records.append(GlyphRecord(
                unicode=char,
                name=label[len("glyph_"):],
                d=" ".join(d_parts) if d_parts else None,
                advance=self.options.default_advance,
            ))

        ffa = FontFaceAttrs(
            font_family=self.options.family,
            units_per_em=em,
            font_weight=self.options.weight,
            font_style="italic" if self.options.italic else "normal",
            copyright=self.options.copyright or None,
        )
        font_xml = build_svg_font(records, ffa, self.options.default_advance)
        Path(self.options.output_path).write_text(font_xml, encoding="utf-8")