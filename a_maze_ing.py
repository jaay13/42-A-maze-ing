"""Entry point for A-Maze-ing.

Reads a KEY=VALUE configuration file, generates a maze with the mazegen
engine, displays it, and offers an interactive menu. No traceback ever
reaches the terminal: anything that stops the run is one clean message
on stderr and exit 1.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
from typing import Any

from app.animate import DEFAULT_DELAY_MS, animate_path, use_animation
from app.colour import PALETTE
from app.config import load_config, parse_config
from app.display import maze_lines
from app.errors import AppError
from app.output import write_output
from mazegen import MazeGenerator, MazegenError


def get_config_path() -> str:
    """Return the config file path named on the command line.

    Exactly one argument is required (subject SS IV.2: "config.txt is
    the only argument"). A wrong invocation is not a config-file
    problem, so this prints usage to stderr and exits 1 directly rather
    than raising ConfigError.

    Returns:
        The path passed as the single command-line argument.
    """
    if len(sys.argv) != 2:
        print(
            "[USAGE_ERROR] Please specify a config file: "
            "python3 a_maze_ing.py <config_file>, nothing more or less",
            file=sys.stderr,
        )
        sys.exit(1)
    return sys.argv[1]


def generate_maze(
    generator: MazeGenerator,
    config: dict[str, Any],
) -> list[str]:
    """Generate a maze and write it to the output file.

    Paired with display_maze, which draws the result: this half changes
    the world, that half only describes it, and the menu needs them
    apart so showing or hiding the path can redraw an unchanged maze
    without regenerating it or rewriting OUTPUT_FILE. The file always
    describes the current maze, which is not the same as matching the
    screen.

    Args:
        generator: The generator to (re)run. Modified in place.
        config: The typed config dict, read for OUTPUT_FILE, ENTRY and
            EXIT.

    Returns:
        The solution as direction letters, from the single solve()
        call, so the file and the screen show the same path.

    Raises:
        MazegenError: If the maze cannot be generated or solved.
        OutputError: If the output file cannot be written.
    """
    generator.generate()

    if not generator.has_pattern:
        print(
            "[PATTERN_ERROR] the maze is too small to fit the '42' "
            "pattern, so it was left out",
            file=sys.stderr,
        )

    solution = generator.solve()
    write_output(
        config["OUTPUT_FILE"],
        generator.to_rows(),
        config["ENTRY"],
        config["EXIT"],
        solution,
    )
    return solution


def display_maze(
    generator: MazeGenerator,
    config: dict[str, Any],
    solution: list[str],
    show_path: bool,
    colour_idx: int,
) -> None:
    """Draw the current maze to stdout.

    Reads the generator and prints; changes nothing. That is what lets
    the menu redraw the same maze with a different view. The lines
    come from maze_lines, so both halves cannot disagree about which
    renderer ran.

    Args:
        generator: The generator holding the maze.
        config: The typed config dict, read for ENTRY and EXIT here
            and for RENDERER by maze_lines.
        solution: Direction letters from the generate_maze call that
            produced the current maze.
        show_path: Whether to draw the solution as '*'.
        colour_idx: Index into app.colour.PALETTE for the wall colour.

    Raises:
        RenderError: If the solution contains a direction letter that
            is not 'N', 'E', 'S' or 'W'. Raised by maze_lines.
    """
    lines = maze_lines(
        generator.grid,
        config,
        solution,
        generator.pattern_cells,
        show_path,
        colour_idx,
    )
    for line in lines:
        print(line)

    print(f"\nentry={config['ENTRY']} exit={config['EXIT']}\n")


def main() -> None:
    """Load and validate the config, build a maze, and drive the CLI loop.

    Loops on the four-option menu from subject SS V: re-generate,
    show/hide the shortest path, rotate the wall colours, and quit.
    Holds the solution, the show/hide flag and the palette index as
    locals, so a redraw needs no second solve() call and the colour
    module never decides which colour comes next. An unrecognised
    choice reprints the menu without raising; EOF and interrupts are
    handled by the __main__ block, which exits 0 for both.

    Raises:
        ConfigError: If the config file is missing, malformed, or
            invalid.
        OutputError: If the output file cannot be written.
        MazegenError: If the maze parameters are invalid or the maze
            can't be generated/solved.
    """
    config_path = get_config_path()
    config = parse_config(load_config(config_path))
    show_path = False
    colour_idx = 0
    generator = MazeGenerator(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit=config["EXIT"],
        perfect=config["PERFECT"],
        seed=config.get("SEED"),
    )
    solution = generate_maze(generator, config)
    display_maze(generator, config, solution, show_path, colour_idx)

    while True:
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print("4. Quit")

        choice = input("Choice? (1-4): ").strip()
        if choice == "1":
            solution = generate_maze(generator, config)
        elif choice == "2":
            show_path = not show_path
            delay = config.get("ANIMATION_DELAY", DEFAULT_DELAY_MS)
            if show_path and delay and use_animation():
                animate_path(
                    generator.grid,
                    config,
                    solution,
                    generator.pattern_cells,
                    colour_idx,
                    delay,
                )
        elif choice == "3":
            colour_idx = (colour_idx + 1) % len(PALETTE)
        elif choice == "4":
            break
        else:
            print(f"\nExpected input 1-4, got '{choice}' try again\n")
            continue
        display_maze(generator, config, solution, show_path, colour_idx)


if __name__ == "__main__":
    try:
        main()
    except MazegenError as e:
        print(f"[MAZE_ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except AppError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    # Last resort (split.md:203). Subject SS IV.2 makes one traceback
    # fatal, and the engine's parameter validation (A8) is not written
    # yet, so bad WIDTH/HEIGHT/ENTRY/EXIT still reach the renderer as
    # IndexError. This is a backstop, not error handling: anything it
    # catches is a bug that deserves its own handler above.
    except Exception as e:
        print(
            f"[INTERNAL_ERROR] unexpected {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
