"""Terminal rendering of a maze (Person B / app layer).

Each cell of the grid is one integer 0-15 holding its four walls, as
defined by subject SS IV.5 and INTERFACE.md:

    bit 0 (value 1) = North
    bit 1 (value 2) = East
    bit 2 (value 4) = South
    bit 3 (value 8) = West

A bit that is SET means that wall is CLOSED; clear means open. So 15
(1111) is a fully enclosed cell, and 10 (1010) has its west and east
walls closed with north and south open.
"""

from .errors import RenderError

WALL_BITS = {"N": 1, "E": 2, "S": 4, "W": 8}

MOVES = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}


def is_closed(value: int, side: str) -> bool:
    """Report whether one wall of a cell is closed.

    Args:
        value: The cell's wall encoding, 0-15.
        side: Which wall to test: 'N', 'E', 'S' or 'W'.

    Returns:
        True if that wall is closed, False if it is open.

    Raises:
        KeyError: If side is not one of 'N', 'E', 'S', 'W'. This is a
            programming error rather than user input, so it is left to
            surface rather than being converted to an AppError.
    """
    return bool(value & WALL_BITS[side])


def path_cells(
        entry: tuple[int, int],
        solution: list[str],
) -> set[tuple[int, int]]:
    """Replay a solution path into the set of cells it visits.

    MazeGenerator.solve() returns directions rather than positions,
    which the output file can write as-is but the renderer cannot use:
    drawing asks 'is this cell on the path?' once per cell, and that
    question needs coordinates. Walking the letters once here turns
    the answer into a set lookup instead of a re-walk per cell.

    Never solves anything itself. The walk only follows the letters it
    is given and never looks at a wall, so a wrong path is reproduced
    faithfully rather than corrected.

    Args:
        entry: The (x, y) cell the path starts from, included in the
            result: the set is every cell the walk visits, and the
            walk starts before it has moved.
        solution: The path as single-letter directions ('N', 'E', 'S',
            'W'), as returned by MazeGenerator.solve().

    Returns:
        Every cell the walk visits, entry included. An empty solution
        gives just the entry.

    Raises:
        RenderError: If a letter is not one of 'N', 'E', 'S', 'W'.
            Unlike is_closed's KeyError this is bad engine data rather
            than a mistake in app code, and it would otherwise reach
            the terminal as a traceback.
    """
    ret = {entry}
    x, y = entry
    for index, letter in enumerate(solution):
        if letter not in MOVES:
            raise RenderError(
                "[RENDER_ERROR] the engine returned an invalid direction "
                f"'{letter}' at step {index}"
            )
        dx, dy = MOVES[letter]
        x += dx
        y += dy
        ret.add((x, y))
    return ret
