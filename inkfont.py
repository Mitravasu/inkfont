#!/usr/bin/env python3
"""Typeface Builder — Inkscape extension entry point.

Inkscape invokes this script once per menu command, passing the SVG on stdin
and the dialog params as argv. Each ``.inx`` descriptor passes a hidden
``--command`` argument that selects which Effect subclass to run. We read
that and dispatch.

This file is intentionally tiny: it only wires the dialog to the right
:class:`inkex.EffectExtension` subclass. All real logic lives in the pure
modules (charsets, glyph_naming, path_transform, svgfont) and the command
modules under :mod:`commands`.
"""

import argparse
import os
import sys

# Inkscape puts the script's own directory on sys.path. We add it here too
# as a safety net for when the script is run from elsewhere (e.g. tests).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def main():
    # inkex.EffectExtension parses argv itself; we only need to peek at
    # --command first. We use a parser that ignores unknown args so the rest
    # can be consumed by the Effect subclass's own arg_parser.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--command", default="setup_canvas")
    known, remaining = pre.parse_known_args()

    sys.argv = [sys.argv[0]] + remaining

    if known.command == "setup_canvas":
        from lib.commands.setup_canvas import SetupCanvas
        SetupCanvas().run()
    elif known.command == "create_glyph_layers":
        from lib.commands.create_glyph_layers import CreateGlyphLayers
        CreateGlyphLayers().run()
    elif known.command == "export_svg_font":
        from lib.commands.export_svg_font import ExportSvgFont
        ExportSvgFont().run()
    else:
        raise SystemExit(f"Unknown command: {known.command!r}")


if __name__ == "__main__":
    main()