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


def draw_walls(grid: list[list[int]]) -> list[list[str]]:
    """Draw the maze's walls onto a fresh character canvas.

    The canvas is 2*height+1 rows by 4*width+1 columns, because n cells
    have n interiors but n+1 lines between and around them. Cell (x, y)
    is the box spanning rows 2*y to 2*y+2 and columns 4*x to 4*x+4, so
    rows are always derived from y and columns always from x: a row
    index built from x, or a column index from y, is a bug.

    Every interior wall is shared by two cells, which the engine keeps
    in agreement (see MazeGenerator._open_wall). Each wall is therefore
    drawn by exactly one owner: a cell draws its own north and west
    walls, and the two outer edges that no cell owns are drawn last.
    That is why the E and S bits are only read along the border even
    though is_closed supports all four sides. Reading all four instead
    would draw every interior wall twice and let a future engine bug
    show up as one cell contradicting its neighbour.

    Returns a mutable list of lists rather than finished strings so
    place_symbols can write single characters at known positions;
    strings would have to be rebuilt piecewise since they cannot be
    assigned into.

    Args:
        grid: The maze as returned by MazeGenerator.grid, where
            grid[y][x] holds one cell's wall bits. Must have at least
            one row and one column; WIDTH and HEIGHT are validated in
            app.config, so no guard is repeated here.

    Returns:
        The canvas as rows of single characters, walls drawn and every
        cell interior still blank.
    """
    height = len(grid)
    width = len(grid[0])

    canvas = [[" "] * (4 * width + 1) for _ in range(2 * height + 1)]

    for row in range(0, 2 * height + 1, 2):
        for col in range(0, 4 * width + 1, 4):
            canvas[row][col] = "+"

    for y in range(height):
        for x in range(width):
            if is_closed(grid[y][x], "N"):
                for col in range(4 * x + 1, 4 * x + 4):
                    canvas[2 * y][col] = "-"

    for y in range(height):
        for x in range(width):
            if is_closed(grid[y][x], "W"):
                canvas[2 * y + 1][4 * x] = "|"

    for x in range(width):
        if is_closed(grid[height - 1][x], "S"):
            for col in range(4 * x + 1, 4 * x + 4):
                canvas[2 * height][col] = "-"

    for y in range(height):
        if is_closed(grid[y][width - 1], "E"):
            canvas[2 * y + 1][4 * width] = "|"
    return canvas
