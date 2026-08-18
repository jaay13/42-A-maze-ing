"""Entry point for A-Maze-ing.

Reads a KEY=VALUE configuration file, generates a maze with the mazegen
engine, displays it, and offers an interactive menu.

No traceback ever reaches the terminal. Anything that stops the run --
a bad config, an unreadable file, a maze the engine cannot build -- is
reported as a single clean message on stderr and exits 1. Two kinds of
message deliberately do neither: the '42' pattern notice, which reports
that an otherwise successful run left the glyph out (subject SS IV.4),
goes to stderr and leaves the exit code at 0; and the menu's reply to
an unrecognised choice, which is interactive feedback rather than a
failure, goes to stdout and also leaves it at 0.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys

from app.colour import PALETTE, colourise
from app.config import load_config, parse_config
from app.errors import AppError
from app.output import write_output
from app.render import render
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


def generate_maze(generator: MazeGenerator, config: dict) -> list[str]:
    """Generate a maze and write it to the output file.

    Paired with display_maze, which draws the result. The two are kept
    apart because this one changes the world -- it re-runs the
    generator and rewrites OUTPUT_FILE -- while drawing only describes
    it. The menu depends on that: showing or hiding the path re-renders
    an unchanged maze, and must neither generate a new one nor touch
    the file.

    Keeping the write in here is what stops OUTPUT_FILE going stale
    after a regenerate: the file always describes the current maze.
    It does not always match the screen, since the path can be hidden
    from view while remaining in the file, where the subject requires
    it.

    solve() is called once and its result returned rather than
    re-derived, since the path in the file and the path shown to the
    user must come from the same call. The caller holds it for as long
    as the maze stays on screen.

    Subject SS IV.4 allows the '42' pattern to be omitted when the maze
    is too small and asks for an error message in that case. It is only
    a message: the maze is still generated, solved, written and drawn,
    so nothing is skipped and the exit code stays 0. It goes to stderr
    because the run succeeded and stdout holds the maze itself. It is
    reported here rather than in display_maze so it is printed once per
    maze, not once per redraw.

    Args:
        generator: The generator to (re)run. Modified in place.
        config: The typed config dict, read for OUTPUT_FILE, ENTRY and
            EXIT.

    Returns:
        The solution as direction letters, from the single solve()
        call. Pass it to display_maze to draw the same path that was
        written to the file.

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
    config: dict,
    solution: list[str],
    show_path: bool,
    colour_idx: int,
) -> None:
    """Draw the current maze to stdout.

    Paired with generate_maze, which produces the maze this draws.
    Drawing only describes the world: it reads the generator and
    prints, and changes nothing. That is what lets the menu redraw the
    same maze with a different view -- showing or hiding the path, and
    later rotating wall colours -- without regenerating it or
    rewriting OUTPUT_FILE.

    Takes the solution as an argument rather than calling solve()
    again, so every redraw of one maze shows the path that was written
    to the file.

    Args:
        generator: The generator holding the maze to draw. Read only,
            for grid and pattern_cells.
        config: The typed config dict, read for ENTRY and EXIT. These
            come from the config rather than the generator because
            entry/exit attributes are not part of the frozen interface.
        solution: Direction letters from the generate_maze call that
            produced the maze currently held by the generator.
        show_path: Whether to draw the solution as '*'. Passed straight
            to render. The caller owns this state, so the same maze can
            be drawn either way without being regenerated, and the
            written file keeps the path regardless of what is shown.

    Raises:
        RenderError: If the solution contains a direction letter that
            is not 'N', 'E', 'S' or 'W'. Raised by render.
    """
    lines = render(
        generator.grid,
        config["ENTRY"],
        config["EXIT"],
        solution,
        generator.pattern_cells,
        show_path,
    )
    lines = colourise(lines, PALETTE[colour_idx])
    for line in lines:
        print(line)

    print(f"\nentry={config['ENTRY']} exit={config['EXIT']}\n")


def main() -> None:
    """Load and validate the config, build a maze, and drive the CLI loop.

    Reads the config file named on the command line, builds a
    MazeGenerator from the validated, typed config, then calls
    generate_maze to produce and write the maze and display_maze to
    draw it. Then loops on the four-option menu from subject SS V:
    re-generate, show/hide the shortest path, rotate the wall colours,
    and quit. Colour rotation cycles the wall colour through
    app.colour.PALETTE, wrapping with len(PALETTE); main owns the index
    so the colour module never decides which colour comes next.
    Re-generating runs
    both halves again, so the output file
    never goes stale; showing or hiding the path runs only display_maze,
    so it redraws the same maze without touching the file. Exits 1 via
    get_config_path if the program was invoked with anything other than
    exactly one argument.

    An unrecognised choice reprints the menu rather than raising: a
    mistyped menu entry is not an error, so nothing goes to stderr and
    the exit code stays 0. split.md:145 requires the menu to survive
    garbage and empty input; EOF and interrupts are handled by the
    __main__ block, which exits 0 for both.

    Holds the solution returned by generate_maze in a local for as long
    as that maze is on screen, so a redraw can show the same path
    without a second solve() call.

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
