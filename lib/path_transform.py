"""Y-flip + scale an SVG path ``d`` string into font-space coordinates.

Inkscape uses Y-down with origin at the top-left. Fonts use Y-up with origin
at the baseline. For every coordinate::

    font_x = svg_x * scale
    font_y = (baseline_y - svg_y) * scale

Relative deltas flip the sign of dy and scale both::

    dx_font = dx_svg * scale
    dy_font = dy_svg * -scale

Stdlib only. No inkex. Imports nothing from the project.

Supported commands: ``M m L l H h V v C c S s Q q T t Z z``.
The arc commands ``A a`` are NOT supported (rarely emitted by Inkscape;
their flags/angles need special handling) — they raise ``ValueError`` so we
catch them loudly instead of silently corrupting a glyph.
"""

import re

# Commands we know how to transform.
_COMMANDS = set("MmLlHhVvCcSsQqTtZz")
# Commands that take coordinate pairs (x, y).
_PAIR_COMMANDS = set("MmLlCcSsQqTt")
# Commands that take a single X.
_X_COMMANDS = set("Hh")
# Commands that take a single Y.
_Y_COMMANDS = set("Vv")
# Close path.
_CLOSE_COMMANDS = set("Zz")

# A token is either a single command letter or a number (int/float/sci).
_TOKEN_RE = re.compile(
    r"([MmLlHhVvCcSsQqTtZzAa])"                     # command letter
    r"|([+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)"  # number
)


def _tokenize(d: str):
    """Yield ('cmd', letter) and ('num', float) tokens from ``d``."""
    for m in _TOKEN_RE.finditer(d):
        letter, number = m.group(1), m.group(2)
        if letter is not None:
            yield ("cmd", letter)
        elif number is not None:
            yield ("num", float(number))
        # whitespace / commas between tokens are skipped by the regex.


def _fmt(v: float) -> str:
    """Compact number formatting: integers without trailing .0."""
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return f"{v:g}"


def flip_and_scale(d: str, baseline_y: float, scale: float = 1.0) -> str:
    """Transform path ``d`` from SVG space to font space.

    See module docstring for the transform. Raises ``ValueError`` on an
    unsupported command (e.g. ``A``) or malformed input.
    """
    if not isinstance(d, str):
        raise ValueError(f"d must be a string, got {type(d).__name__}")

    out = []
    cur_cmd = None
    # Current position in SVG and font spaces (kept in sync).
    svg_x = svg_y = 0.0
    fnt_x = fnt_y = 0.0
    # Start-of-subpath position (for Z, which returns to last moveto).
    start_svg_x = start_svg_y = 0.0
    start_fnt_x = start_fnt_y = 0.0

    nums = []  # numbers accumulated for the current command repetition

    def flush(cmd):
        """Emit ``cmd`` with its already-collected numeric args."""
        nonlocal svg_x, svg_y, fnt_x, fnt_y
        nonlocal start_svg_x, start_svg_y, start_fnt_x, start_fnt_y
        if cmd in _CLOSE_COMMANDS:
            if nums:
                raise ValueError(f"Z must take no coordinates, got {nums}")
            out.append(cmd.upper() if cmd.isupper() else cmd)
            svg_x, svg_y = start_svg_x, start_svg_y
            fnt_x, fnt_y = start_fnt_x, start_fnt_y
            return

        is_abs = cmd.isupper()
        c = cmd.upper()
        i = 0
        first = True
        while i < len(nums):
            if c in _PAIR_COMMANDS:
                if i + 1 >= len(nums):
                    raise ValueError(f"{cmd} needs pairs, got {nums}")
                dx, dy = nums[i], nums[i + 1]
                i += 2
                if is_abs:
                    nx, ny = dx, dy
                    fx, fy = nx * scale, (baseline_y - ny) * scale
                    out_cmd = cmd
                else:
                    nx, ny = svg_x + dx, svg_y + dy
                    # Emit relative deltas in font space: dx*scale, dy*-scale.
                    fx, fy = dx * scale, -dy * scale
                    out_cmd = cmd
                # For moveto, also update subpath start.
                if c == "M":
                    start_svg_x, start_svg_y = nx, ny
                    start_fnt_x, start_fnt_y = (nx * scale, (baseline_y - ny) * scale)
                # Subsequent moveto groups are linetos per SVG spec.
                if c == "M" and not first:
                    out_cmd = "L" if is_abs else "l"
                out.append(out_cmd)
                out.append(_fmt(fx))
                out.append(_fmt(fy))
                svg_x, svg_y = nx, ny
            elif c in _X_COMMANDS:
                dx = nums[i]
                i += 1
                if is_abs:
                    nx = dx
                    out_val = nx * scale
                    out.append(cmd)
                    out.append(_fmt(out_val))
                else:
                    nx = svg_x + dx
                    out_val = dx * scale
                    out.append(cmd)
                    out.append(_fmt(out_val))
                svg_x = nx
            elif c in _Y_COMMANDS:
                dy = nums[i]
                i += 1
                if is_abs:
                    ny = dy
                    out_val = (baseline_y - ny) * scale
                    out.append(cmd)
                    out.append(_fmt(out_val))
                else:
                    ny = svg_y + dy
                    out_val = -dy * scale
                    out.append(cmd)
                    out.append(_fmt(out_val))
                svg_y = ny
            else:
                raise ValueError(f"unhandled command {cmd!r}")
            first = False
        nums.clear()

    for kind, val in _tokenize(d):
        if kind == "cmd":
            if val in ("A", "a"):
                raise ValueError("arc command A/a is not supported")
            # A new command letter flushes any pending repeated args.
            if cur_cmd is not None and (nums or cur_cmd in _CLOSE_COMMANDS):
                flush(cur_cmd)
            cur_cmd = val
            if val in _CLOSE_COMMANDS:
                flush(val)
                cur_cmd = None
        else:  # number
            if cur_cmd is None:
                raise ValueError(f"number {val} with no active command")
            nums.append(val)

    if cur_cmd is not None and (nums or cur_cmd in _CLOSE_COMMANDS):
        flush(cur_cmd)

    return " ".join(out)