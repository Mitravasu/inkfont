"""Setup Canvas command — sizes the document and creates named guides.

Dialog params: ``em_size``, ``cap_height``, ``x_height``, ``ascender``,
``descender`` (all in font units = SVG user units). The document is sized to
``em_size × em_size`` and five labeled horizontal guides are added.
Optionally two vertical side-bearing guides are added at ``left_bearing``
and ``em_size - right_bearing`` (default 100 from each edge).

Guide Y positions (Inkscape y-down, origin top-left). We anchor the descender
line at the bottom of the em square; everything else follows from the
baseline::

    baseline_y   = em_size - descender
    descender_y  = em_size
    x_height_y   = baseline_y - x_height
    cap_height_y = baseline_y - cap_height
    ascender_y   = baseline_y - ascender

Thin: no math beyond computing guide positions from inputs. Tested via the
Step 9 integration test (fixture recreates the post-Setup-Canvas shape).
"""

from inkex import Boolean, EffectExtension

from ..guides import create_named_guide


class SetupCanvas(EffectExtension):
    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument(
            "--em_size", type=int, default=1000,
            help="Em size in font units (also the document width/height).",
        )
        self.arg_parser.add_argument(
            "--cap_height", type=int, default=700,
            help="Cap height above baseline (font units).",
        )
        self.arg_parser.add_argument(
            "--x_height", type=int, default=500,
            help="x-height above baseline (font units).",
        )
        self.arg_parser.add_argument(
            "--ascender", type=int, default=800,
            help="Ascender height above baseline (font units).",
        )
        self.arg_parser.add_argument(
            "--descender", type=int, default=200,
            help="Descender depth below baseline (font units, positive).",
        )
        self.arg_parser.add_argument(
            "--left_bearing", type=int, default=100,
            help="Left side bearing (font units from the left edge).",
        )
        self.arg_parser.add_argument(
            "--right_bearing", type=int, default=100,
            help="Right side bearing (font units from the right edge).",
        )
        self.arg_parser.add_argument(
            "--add_side_guides", type=Boolean, default=True,
            help="If true, add left/right side-bearing vertical guides.",
        )

    def effect(self):
        em = self.options.em_size
        baseline_y = em - self.options.descender

        # Resize the document to an em square.
        self.svg.set("width", f"{em}")
        self.svg.set("height", f"{em}")
        self.svg.set("viewBox", f"0 0 {em} {em}")

        # Five horizontal labeled guides. Y in Inkscape's y-down system.
        create_named_guide(self.svg, "ascender", "horizontal", baseline_y - self.options.ascender)
        create_named_guide(self.svg, "cap-height", "horizontal", baseline_y - self.options.cap_height)
        create_named_guide(self.svg, "x-height", "horizontal", baseline_y - self.options.x_height)
        create_named_guide(self.svg, "baseline", "horizontal", baseline_y)
        create_named_guide(self.svg, "descender", "horizontal", float(em))

        if self.options.add_side_guides:
            create_named_guide(self.svg, "left-bearing", "vertical", float(self.options.left_bearing))
            create_named_guide(
                self.svg, "right-bearing", "vertical",
                float(em - self.options.right_bearing),
            )