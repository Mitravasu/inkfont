# InkFont — typeface construction tool for Inkscape

An Inkscape extension that turns Inkscape into a typeface construction tool.
Draw a base shape, scaffold one hidden layer per target character (each
preloaded with a copy of the base), build each letter with the shape-builder,
then export the whole set as an SVG font ready for FontForge to compile into
OTF/TTF.

```
[Setup Canvas] → [Create Glyph Layers] → draw each letter → [Export SVG Font] → FontForge → OTF/TTF
```

## Install

Copy `inkfont.py`, the three `.inx` files, and the `lib/` package directory
into your Inkscape extensions folder:

- **Linux:** `~/.config/inkscape/extensions/`
- **macOS:** `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/`
- **Windows:** `%APPDATA%\inkscape\extensions\`

Then restart Inkscape. The three commands appear under
**Extensions → InkFont →**.

Example (Linux), run from the repo root:

```sh
cp inkfont.py *.inx ~/.config/inkscape/extensions/
cp -r lib ~/.config/inkscape/extensions/
```

## The three commands

### 1. Setup Canvas

Sizes the document to an em square (default 1000×1000) and creates five
labeled horizontal guides: `ascender`, `cap-height`, `x-height`, `baseline`,
`descender`. The exporter reads the `baseline` guide by label to flip Y and
normalize to font units.

### 2. Create Glyph Layers

Scaffolds one hidden layer per character in the chosen preset, each preloaded
with a deep copy of your current selection tagged
`inkscape:label="template_base"`. Layer naming:

- `glyph_A` … `glyph_Z`, `glyph_a` … `glyph_z`, `glyph_0` … `glyph_9` for the
  62 alphanumerics.
- `glyph_U+XXXX` (4-hex, zero-padded) for everything else (e.g. `glyph_U+0020`
  for space, `glyph_U+00E9` for `é`).

Presets: `Uppercase`, `Lowercase`, `Digits`, `Coding — core`,
`Coding — extended`, `Custom` (free text).

### 3. Export SVG Font

Walks every `glyph_*` layer, collects every `<path>` whose
`inkscape:label != "template_base"`, concatenates their `d` data, Y-flips
each coordinate from Inkscape space (y-down, top-left origin) into font space
(y-up, baseline origin), and assembles a complete SVG font document. Write
the result to disk and import into FontForge via
**File → Import → SVG Font**.

## Workflow

1. **Extensions → InkFont → Setup Canvas** with the defaults
   (1000-unit em). Five named guides appear.
2. Draw a rectangle (or any shape) you want as your base primitive, select it.
3. **Extensions → InkFont → Create Glyph Layers**, pick a preset
   (e.g. `Uppercase`), leave "Copy current selection" on. You get 26 hidden
   `glyph_A`…`glyph_Z` layers, each containing a tagged copy of your shape.
4. Unhide one layer at a time, make it active, draw additional cutting shapes
   alongside the tagged base, and use Inkscape's shape-builder (boolean ops)
   to combine/subtract into the final letter. **Commit the shape** before
   switching layers (the in-progress shape isn't in the DOM until you do).
5. **Extensions → InkFont → Export SVG Font**, pick a family name
   and output path. You get an `.svg` font file.
6. In FontForge: **File → Import → SVG Font**, then tune metrics, hints, and
   kerning, and export OTF/TTF.

## Notes & gotchas

- **Always keep the `glyph_X` layer active while building that letter.** The
  exporter maps layer name → codepoint; the object's own name/ID is ignored.
- **Build a *new* shape from the base; don't reshape the base itself.** The
  tagged `template_base` copy is skipped on export — if you modify it in
  place, your changes won't appear in the font.
- **Multi-part glyphs** (`i`, `j`, `!`, `é`): the exporter concatenates the
  `d` of every non-template path in the layer, so multiple subpaths are fine.
- **Space** has no outline — leave its `glyph_U+0020` layer empty (only the
  template base, which is skipped) and you'll get
  `<glyph unicode=" " horiz-adv-x="..."/>` with no `d`.
- **Per-glyph advance width, kerning, combining marks, ligatures** are out of
  scope for v1 — FontForge is the right place for those.

## Development

Pure logic (no `inkex` dependency) is unit-tested:

```sh
pytest
```

The pure modules are `lib/charsets`, `lib/glyph_naming`, `lib/path_transform`,
`lib/svgfont`. Only `lib/guides.py` and `lib/commands/*` import `inkex`. Tests
run without Inkscape installed.

## Layout

```
inkfont.py                     # entry point: dispatches --command to Effect
setup_canvas.inx               # Inkscape descriptor: Setup Canvas
create_glyph_layers.inx        # Inkscape descriptor: Create Glyph Layers
export_svg_font.inx            # Inkscape descriptor: Export SVG Font
lib/
├── charsets.py                # preset character sets (pure data)
├── glyph_naming.py            # char ↔ layer name (pure)
├── guides.py                  # read/write named guides (inkex glue)
├── path_transform.py          # Y-flip + scale path d (pure)
├── svgfont.py                 # assemble <font> XML (pure)
└── commands/
    ├── setup_canvas.py        # Setup Canvas Effect
    ├── create_glyph_layers.py # Create Glyph Layers Effect
    └── export_svg_font.py     # Export SVG Font Effect
tests/
├── test_charsets.py
├── test_glyph_naming.py
├── test_path_transform.py
├── test_svgfont.py
├── test_integration_layers.py
├── test_export_end_to_end.py
└── fixtures/sample.svg
```