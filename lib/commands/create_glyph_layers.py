"""Create Glyph Layers command — one hidden layer per target character.

Dialog params:
- ``preset`` (dropdown): one of the keys in :data:`charsets.PRESETS`, or
  ``Custom``.
- ``custom_chars`` (free text): used only when ``preset == "Custom"``.
- ``copy_base`` (bool, default True): deep-copy the current selection into
  each new layer, tagged ``inkscape:label="template_base"``.

For each character in the resolved set, creates a layer::

    <g inkscape:groupmode="layer" inkscape:label="glyph_A" style="display:none">
      ... (optional tagged copies of the selection) ...
    </g>

All layers start hidden; the user unhides one at a time while building that
letter. Tested via the Step 9 integration test.
"""

import inkex

from ..charsets import PRESETS
from ..glyph_naming import layer_name_for_char


class CreateGlyphLayers(inkex.EffectExtension):
    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument(
            "--preset", type=str, default="Uppercase",
            help="Character set preset name, or 'Custom'.",
        )
        self.arg_parser.add_argument(
            "--custom_chars", type=str, default="",
            help="Custom characters (used only when preset is 'Custom').",
        )
        self.arg_parser.add_argument(
            "--copy_base", type=inkex.Boolean, default=True,
            help="Copy current selection into each layer as a tagged template.",
        )

    def effect(self):
        chars = self._resolve_chars()
        if not chars:
            raise inkex.AbortExtension("No characters to create layers for.")

        selection = list(self.svg.selected) if self.options.copy_base else []
        if self.options.copy_base and not selection:
            raise inkex.AbortExtension("Select your base shape first.")

        # De-dup while preserving order so we don't stack two glyph_A layers.
        seen = set()
        for c in chars:
            if c in seen:
                continue
            seen.add(c)
            self._create_layer(c, selection)

    def _resolve_chars(self):
        if self.options.preset == "Custom":
            return self.options.custom_chars
        if self.options.preset in PRESETS:
            return PRESETS[self.options.preset]
        raise inkex.AbortExtension(
            f"Unknown preset: {self.options.preset!r}. "
            f"Known: {', '.join(sorted(PRESETS))}, Custom."
        )

    def _create_layer(self, char, selection):
        name = layer_name_for_char(char)
        layer = inkex.Layer.new(name)
        layer.set("style", "display:none")
        # Tag the layer as an Inkscape layer.
        layer.set("inkscape:groupmode", "layer")
        layer.set("inkscape:label", name)
        self.svg.add(layer)

        for elem in selection:
            copy = elem.copy()
            copy.set("inkscape:label", "template_base")
            layer.add(copy)