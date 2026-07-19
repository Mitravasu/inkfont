"""Map between characters and glyph layer names.

Layer naming scheme (Plan §8.2 / §8.4):
- ``glyph_<c>`` for ``A–Z a–z 0–9`` (the 62 alphanumerics).
- ``glyph_U+XXXX`` (4-hex, zero-padded, uppercase) for everything else.

Stdlib only. No inkex. Imports nothing from the project.
"""

import re

# Characters that get a readable ``glyph_<c>`` name.
_READABLE_RE = re.compile(r"[A-Za-z0-9]")

# Matches ``glyph_U+XXXX`` (4 hex digits, zero-padded).
_CODEPOINT_RE = re.compile(r"^glyph_U\+([0-9A-Fa-f]{4,6})$")


def layer_name_for_char(c: str) -> str:
    """Return the glyph layer name for a single character ``c``."""
    if len(c) != 1:
        raise ValueError(f"expected a single character, got {c!r}")
    if _READABLE_RE.fullmatch(c):
        return f"glyph_{c}"
    cp = ord(c)
    return f"glyph_U+{cp:04X}"


def char_from_layer_name(name: str):
    """Inverse of :func:`layer_name_for_char`.

    Returns the single character, or ``None`` if ``name`` is not a valid
    glyph layer name.
    """
    if not isinstance(name, str) or not name.startswith("glyph_"):
        return None
    rest = name[len("glyph_"):]
    if len(rest) == 1 and _READABLE_RE.fullmatch(rest):
        return rest
    m = _CODEPOINT_RE.match(name)
    if m:
        return chr(int(m.group(1), 16))
    return None


def is_glyph_layer(name: str) -> bool:
    """True iff ``name`` is a valid glyph layer name."""
    return char_from_layer_name(name) is not None