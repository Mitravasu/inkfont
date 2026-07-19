"""Preset character sets for Typeface Builder.

Pure data module. One dict ``PRESETS`` mapping preset name → string of
characters. No deduplication; callers dedup if they care.

Presets (locked in Plan §8.2):
- Coding — core: alphanumerics + space + common coding punctuation
- Coding — extended: core + typographic punctuation
- Uppercase: A–Z
- Lowercase: a–z
- Digits: 0–9

``Custom`` is handled at the command layer (free-text input), so it has no
entry here.
"""

PRESETS = {
    "Coding — core": (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " "  # space
        "`~!@#$%^&*()-=+[\\]{}|;:'\",.<>/?_"  # coding punctuation
        "\n\t"  # newline/tab placeholders
    ),
    "Coding — extended": (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789"
        " "
        "`~!@#$%^&*()-=+[\\]{}|;:'\",.<>/?_"
        "\n\t"
        "°§µ•…—–‘’“”«»¿¡"
    ),
    "Uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "Lowercase": "abcdefghijklmnopqrstuvwxyz",
    "Digits": "0123456789",
}