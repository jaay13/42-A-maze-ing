"""Block rendering of a maze (Person B / app layer)."""

from .render import is_closed, path_cells

CORRIDOR_CODE = 233
ENTRY_CODE = 163
EXIT_CODE = 196
PATH_CODE = 100
GLYPH_CODE = 244


def wall_map(grid: list[list[int]]) -> list[list[bool]]:
    """Turn a maze grid into a map of which positions are wall.

    The map is 2*height+1 by 2*width+1, so every wall gets a position
    between the two cells it separates: odd/odd is a cell, odd/even and
    even/odd are walls, even/even is a corner. Only the East and South
    walls of each cell are read, since the engine keeps both sides of a
    shared wall in agreement.

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


def render(
    grid: list[list[int]],
    entry: tuple[int, int],
    exit_coords: tuple[int, int],
    solution: list[str],
    pattern: frozenset[tuple[int, int]],
    show_path: bool,
    wall: int,
) -> list[str]:
    """Draw one maze as coloured blocks.

    Each position of the wall map becomes two spaces with a background
    colour, two because a terminal character is roughly twice as tall
    as it is wide. Unlike app.render the result is meaningless without
    a terminal, so the ASCII renderer stays as the fallback.

    Args:
        grid: The maze, as MazeGenerator.grid.
        entry: The (x, y) entry cell, from the config.
        exit_coords: The (x, y) exit cell, from the config.
        solution: Direction letters from a single solve() call.
        pattern: MazeGenerator.pattern_cells, empty if the maze is too
            small for the glyph.
        show_path: Whether to colour the solution.
        wall: The 256-colour index for walls, from app.colour.PALETTE.

    Returns:
        One string per row of the wall map, ready to print in order.

    Raises:
        RenderError: If the solution contains a letter that is not
            'N', 'E', 'S' or 'W'. Raised by path_cells.
    """
    pixels = wall_map(grid)
    solution_path = path_cells(entry, solution)
    empty_path: set[tuple[int, int]] = set()
    path = solution_path if show_path else empty_path
    lines = []

    for row_index, row in enumerate(pixels):
        parts = []
        for col_index, is_wall in enumerate(row):
            if is_wall:
                code = wall
            elif row_index % 2 == 1 and col_index % 2 == 1:
                # Entry and exit before path: the solution
                # starts and ends on them.
                cell = ((col_index - 1) // 2, (row_index - 1) // 2)
                if cell == entry:
                    code = ENTRY_CODE
                elif cell == exit_coords:
                    code = EXIT_CODE
                elif cell in path:
                    code = PATH_CODE
                elif cell in pattern:
                    code = GLYPH_CODE
                else:
                    code = CORRIDOR_CODE
            else:
                code = CORRIDOR_CODE
            parts.append(f"\033[48;5;{code}m  \033[0m")
        lines.append("".join(parts))

    return lines
