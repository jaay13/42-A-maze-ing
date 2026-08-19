"""Choosing and building the maze view (Person B / app layer)."""

from typing import Any

from . import block_render
from .colour import PALETTE, colourise, use_colour
from .render import render


def maze_lines(
    grid: list[list[int]],
    config: dict[str, Any],
    solution: list[str],
    pattern: frozenset[tuple[int, int]],
    show_path: bool,
    colour_idx: int,
) -> list[str]:
    """Build the current maze as the lines to print.

    Picks the renderer: coloured blocks when stdout is a terminal and
    RENDERER asks for them, plain ASCII otherwise. RENDERER is only a
    preference -- a run whose stdout is not a terminal falls back to
    ASCII whatever it says, so redirected output never carries escape
    sequences.

    Takes the maze as plain data rather than a MazeGenerator, so no
    module in app/ depends on the engine's interface -- the same rule
    app.output follows.

    Args:
        grid: The maze, as MazeGenerator.grid.
        config: The typed config dict, read for ENTRY, EXIT and
            RENDERER. RENDERER defaults to blocks when absent.
        solution: Direction letters from the generate_maze call that
            produced the current maze.
        pattern: MazeGenerator.pattern_cells; empty if the maze is too
            small for the glyph.
        show_path: Whether to draw the solution as '*'.
        colour_idx: Index into app.colour.PALETTE for the wall colour.

    Returns:
        One string per canvas row, ready to print in order.

    Raises:
        RenderError: If the solution contains a direction letter that
            is not 'N', 'E', 'S' or 'W'. Raised by render.
    """
    coloured = use_colour()

    if coloured and config.get("RENDERER", "blocks") == "blocks":
        lines = block_render.render(
            grid,
            config["ENTRY"],
            config["EXIT"],
            solution,
            pattern,
            show_path,
            PALETTE[colour_idx],
        )
    else:
        lines = render(
            grid,
            config["ENTRY"],
            config["EXIT"],
            solution,
            pattern,
            show_path,
        )
        if coloured:
            lines = colourise(lines, PALETTE[colour_idx])
    return lines
