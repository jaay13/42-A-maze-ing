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


WALL_BITS = {"N": 1, "E": 2, "S": 4, "W": 8}


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
