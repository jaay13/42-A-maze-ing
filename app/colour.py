"""ANSI colour for the ASCII maze renderer (Person B / app layer)."""

PALETTE = (39, 208, 42, 170, 245)
"""256-colour wall indices, ordered so consecutive rotations jump
across the colour wheel rather than between neighbouring hues."""

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

    Resetting per character rather than per line means a render cut
    short cannot leave the terminal stuck in a colour.

    Args:
        char: The character to wrap.
        code: SGR parameters without the escape or trailing 'm', for
            example '38;5;208', '48;5;240' or '1;38;5;82'.

    Returns:
        The character with the colour applied and reset after it.
    """
    return f"\033[{code}m{char}{RESET}"


def colourise(lines: list[str], wall: int) -> list[str]:
    """Add colour to one rendered maze.

    Walls take the rotating palette colour, the '42' a background fill,
    and the symbols fixed foreground colours. Spaces are passed through
    untouched, since a foreground colour on a space is invisible.

    Args:
        lines: A rendered maze from render(), one string per row.
        wall: The 256-colour index to draw walls in, from PALETTE.

    Returns:
        A new list with escape sequences added. Each line keeps the
        visible width of its input.
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
