"""Writing the maze output file (Person B / app layer).

Implements the output format from subject SS IV.5: the hex grid, a
blank line, then the entry coordinates, the exit coordinates and the
shortest path. Formatting is kept separate from writing so the format
can be tested without touching the disk.
"""

from .errors import OutputError


def format_output(
    rows: list[str],
    entry: tuple[int, int],
    exit_coords: tuple[int, int],
    solution: list[str],
) -> str:
    """Build the complete contents of the maze output file.

    The layout is the one required by subject SS IV.5: every grid row
    on its own line, a single blank line, then three lines holding the
    entry coordinates, the exit coordinates and the solution path.
    Coordinates are written as 'x,y' with no parentheses, and the path
    letters are separated by spaces. Every line is terminated with
    '\\n', including the last one.

    The letters are written unchanged rather than as coordinates: the
    file and the terminal render are two views of the same solve()
    result, and app.render.path_cells converts the same letters into
    the cells it draws. Both therefore describe one path, which the
    evaluation cross-checks (split.md:112).

    Performs no I/O, so the format can be checked in isolation.

    Args:
        rows: One string of hexadecimal wall digits per grid row, as
            returned by MazeGenerator.to_rows().
        entry: The (x, y) entry cell.
        exit_coords: The (x, y) exit cell.
        solution: The shortest path as single-letter directions
            ('N', 'E', 'S', 'W'), as returned by MazeGenerator.solve().

    Returns:
        The full file contents as one newline-terminated string.
    """
    entry_str = f"{entry[0]},{entry[1]}"

    exit_str = f"{exit_coords[0]},{exit_coords[1]}"

    solution_str = " ".join(solution)

    ret = rows + ["", entry_str, exit_str, solution_str]

    return "\n".join(ret) + "\n"


def write_output(
    path: str,
    rows: list[str],
    entry: tuple[int, int],
    exit_coords: tuple[int, int],
    solution: list[str],
) -> None:
    """Write the maze to *path*, creating or overwriting the file.

    Formats the maze with format_output and writes it in one go, using
    a context manager so the handle is closed even if the write fails.

    Args:
        path: Destination file, from the config's OUTPUT_FILE key. An
            existing file is overwritten.
        rows: One string of hexadecimal wall digits per grid row.
        entry: The (x, y) entry cell.
        exit_coords: The (x, y) exit cell.
        solution: The shortest path as single-letter directions.

    Raises:
        OutputError: If the file cannot be written — no such directory,
            permission denied, the path is a directory, and so on.
    """
    output_str = format_output(rows, entry, exit_coords, solution)
    try:
        with open(path, "w") as f:
            f.write(output_str)

    except OSError as e:
        raise OutputError(f"[OUTPUT_ERROR] {e.strerror}: '{path}'") from e
