"""Animating the solution reveal (Person B / app layer)."""

import os
import sys
import time

from .display import maze_lines

DEFAULT_DELAY_MS = 30


def use_animation() -> bool:
    """Report whether frames may be drawn one after another.

    Deliberately not use_colour: NO_COLOR is a statement about colour,
    not about motion, so it is not tested here. Animation is a
    terminal capability, so a run whose stdout is redirected or piped
    draws nothing at all.

    Returns:
        True if stdout is a terminal that can show frames.
    """
    return sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def animate_path(
    grid: list[list[int]],
    config: dict,
    solution: list[str],
    pattern: frozenset[tuple[int, int]],
    colour_idx: int,
    delay_ms: int,
) -> None:
    """Draw the solution one cell at a time.

    Redraws the whole maze per frame, from the same maze_lines the
    static view uses, so the two cannot disagree about which renderer
    ran. Each frame passes a longer slice of the path: path_cells
    walks only the letters it is given, so a slice is a valid partial
    path and no renderer code changes.

    Frames overwrite each other in place: each one moves the cursor
    back up over the previous frame rather than clearing the screen.
    Clearing homes to the top of the *visible* window, which tears
    when the maze is taller than the terminal -- a 15x15 needs 40
    rows and most windows are 24.

    Stops one cell short and rewinds on the way out, so the caller's
    ordinary redraw paints the finished path and its footer over the
    last frame. Drawing the last cell here too would print it twice.

    Args:
        grid: The maze, as MazeGenerator.grid.
        config: The typed config dict.
        solution: Direction letters for the complete path.
        pattern: MazeGenerator.pattern_cells.
        colour_idx: Index into app.colour.PALETTE for the wall colour.
        delay_ms: Milliseconds to pause between frames.
    """
    lines: list[str] = []
    for k in range(len(solution)):
        if lines:
            print(f"\033[{len(lines)}A", end="")
        lines = maze_lines(
            grid, config, solution[:k], pattern, True, colour_idx
        )
        for line in lines:
            print(line)
        time.sleep(delay_ms / 1000)
    if lines:
        print(f"\033[{len(lines)}A", end="")
