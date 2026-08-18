"""Block rendering of a maze (Person B / app layer)."""

from .render import is_closed


def wall_map(grid: list[list[int]]) -> list[list[bool]]:
    """Turn a maze grid into a map of which positions are wall.

    The map is 2*height+1 rows by 2*width+1 columns, so every wall gets
    a position of its own between the two cells it separates:

        odd row, odd column    a cell, never a wall
        odd/even or even/odd   the wall between two cells
        even row, even column  a corner, always a wall

    Everything starts as wall and the open positions are cleared, so
    the outer border and the corners are walls simply by never being
    touched.

    Only the East and South walls of each cell are read. Every interior
    wall belongs to two cells, and MazeGenerator._open_wall clears the
    bit on both sides, so checking all four directions would ask the
    same question twice.

    Args:
        grid: The maze, as MazeGenerator.grid.

    Returns:
        A grid of booleans, True where a wall should be drawn.
    """
    height = len(grid)
    width = len(grid[0])

    canvas = [[True] * (2 * width + 1) for _ in range(2 * height + 1)]

    for y in range(height):
        for x in range(width):
            canvas[2 * y + 1][2 * x + 1] = False

            if x + 1 < width and not is_closed(grid[y][x], "E"):
                canvas[2 * y + 1][2 * x + 2] = False

            if y + 1 < height and not is_closed(grid[y][x], "S"):
                canvas[2 * y + 2][2 * x + 1] = False
    return canvas
