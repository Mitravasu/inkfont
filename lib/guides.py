"""Thin inkex-coupled helpers for reading/writing named guides.

Pure glue, no logic. ~30 lines. Not unit-tested in isolation (needs inkex +
a real SVG tree); exercised by the integration test in Step 9 and the
end-to-end exporter test in Step 10.

Guide labels are stored as the ``inkscape:label`` attribute on each
``<sodipodi:guide>``. Horizontal guides are identified by ``orientation``
with a zero x-component; we read their Y position via :pyattr:`Guide.position`
which already converts to the post-1.0 (y-down, top-left origin) coordinate
system that the rest of the codebase uses.
"""

from inkex import Guide


def create_named_guide(svg_root, label, orientation, position):
    """Add a labeled ``<sodipodi:guide>`` to the document's namedview.

    Args:
        svg_root: the SVG document root (an ``inkex.SvgDocumentElement``).
        label: human-readable name, e.g. ``"baseline"``.
        orientation: ``"horizontal"`` or ``"vertical"``.
        position: the guide offset in document units. For a horizontal guide
            this is the Y coordinate; for a vertical guide, the X coordinate.
            Coordinate system: y-down, origin top-left (Inkscape 1.x).

    Returns:
        The created ``Guide`` element.
    """
    namedview = svg_root.namedview
    orient = orientation == "horizontal"  # True -> horizontal, False -> vertical
    return namedview.add_guide(position, orient=orient, name=label)


def read_named_guides(svg_root):
    """Return ``{label: (x, y)}`` for every labeled guide in the document.

    Unlabeled guides are skipped. Coordinates are in the post-1.0 system
    (y-down, top-left origin) — the same system Inkscape uses for path data,
    so the Y can be fed straight into :func:`path_transform.flip_and_scale`.
    """
    out = {}
    for guide in svg_root.namedview.get_guides():
        label = guide.get("inkscape:label")
        if not label:
            continue
        pos = guide.position  # Vector2d in post-1.0 coords (y-down)
        out[label] = (float(pos.x), float(pos.y))
    return out