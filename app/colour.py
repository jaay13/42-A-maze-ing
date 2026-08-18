"""ANSI colour for the ASCII maze renderer (Person B / app layer)."""

PALETTE = (39, 208, 42, 170, 245)
"""256-colour indices for the walls, in rotation order.

Ordered so that consecutive presses of the menu's colour option jump
across the colour wheel rather than between neighbouring hues, since
two similar colours in a row make the option look like it did nothing.
The caller owns the rotation and wraps with len(PALETTE); this module
never decides which colour comes next.
"""

WALL_CHARS = "+-|"

SYMBOL_CODES = {
    "S": "1;38;5;82",
    "E": "1;38;5;196",
    "*": "38;5;226",
}

PATTERN_CODE = "48;5;240"

RESET = "\033[0m"


def paint(char: str, code: str) -> str:
    """Wrap one character in an ANSI code and reset straight after.

    Resetting per character rather than once per line costs bytes but
    means no output can leave the terminal stuck in a colour. A render
    cut short by Ctrl-C, a pager, or a truncated pipe still closes
    every span it opened.

    Args:
        char: The character to wrap.
        code: SGR parameters without the leading escape or trailing
            'm' -- for example '38;5;208' (foreground), '48;5;240'
            (background) or '1;38;5;82' (bold foreground).

    Returns:
        The character with the colour applied and reset after it.
    """
    return f"\033[{code}m{char}{RESET}"


def colourise(lines: list[str], wall: int) -> list[str]:
    """Add colour to one rendered maze.

    Walls take the rotating palette colour, the '42' glyph takes a
    background fill, and the three symbols take fixed foreground
    colours. Spaces are passed through untouched: they are over half
    of a rendered maze and a foreground colour on a space is
    invisible, so colouring them would double the escape sequences for
    no visible effect.

    The '42' uses a background rather than a foreground because the
    walls rotate through most of the colour wheel, so no single
    foreground stays distinct from every wall colour. A fill is immune
    to that, and matches the subject's p.12 screenshot where the glyph
    reads as solid blocks.

    Symbol colours can sit close to a wall colour on some rotations.
    That is tolerated because shape already tells them apart: 'S', 'E'
    and '*' are not wall glyphs, so they stay legible in a similar
    colour. Colour reinforces this render, it does not carry it --
    the same reason the uncoloured output has to stand on its own.

    Args:
        lines: A rendered maze from render(), one string per row.
            Must be uncoloured; existing escapes are not stripped.
        wall: The 256-colour index to draw walls in, from PALETTE.
            The caller owns the rotation, so this module never decides
            which colour comes next.

    Returns:
        A new list with escape sequences added. Each line keeps the
        visible width of its input, so stripping the escapes returns
        the original render character for character.
    """
    wall_code = f"38;5;{wall}"
    coloured = []

    for line in lines:
        pieces = []

        for char in line:
            if char in WALL_CHARS:
                pieces.append(paint(char, wall_code))
            elif char == "#":
                pieces.append(paint(char, PATTERN_CODE))
            elif char in SYMBOL_CODES:
                pieces.append(paint(char, SYMBOL_CODES[char]))
            else:
                pieces.append(char)

        coloured.append("".join(pieces))
    return coloured
