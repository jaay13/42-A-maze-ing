"""Entry point for A-Maze-ing.

Reads a KEY=VALUE configuration file, generates a maze with the mazegen
engine, displays it, and offers an interactive menu. Every error the
user can trigger is reported as a single clean message on stderr with
exit code 1; no traceback ever reaches the terminal.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys

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


def generate_and_display(generator: MazeGenerator, config: dict) -> None:
    """Generate a maze, write it to the output file, and print it.

    Shared by the initial run and the menu's regenerate option so the
    two cannot drift apart. Keeping the write in here is what stops
    OUTPUT_FILE going stale after a regenerate: the file always
    describes the maze currently on screen.

    solve() is called once and its result reused, since the path in the
    file and the path shown to the user must come from the same call.

    Subject SS IV.4 allows the '42' pattern to be omitted when the maze
    is too small and asks for an error message in that case. It is only
    a message: the maze is still generated, solved, written and drawn,
    so nothing is skipped and the exit code stays 0. It goes to stderr
    because the run succeeded and stdout holds the maze itself.

    Args:
        generator: The generator to (re)run. Modified in place.
        config: The typed config dict, read for OUTPUT_FILE, ENTRY and
            EXIT.

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
    lines = render(
        generator.grid,
        config["ENTRY"],
        config["EXIT"],
        solution,
        generator.pattern_cells,
    )
    for line in lines:
        print(line)

    print(f"entry={config['ENTRY']} exit={config['EXIT']}")


def main() -> None:
    """Load and validate the config, build a maze, and drive the CLI loop.

    Reads the config file named on the command line, builds a
    MazeGenerator from the validated, typed config, then generates a
    maze, writes it to OUTPUT_FILE and prints it. Loops offering the
    user a chance to regenerate or quit; regenerating rewrites the
    output file too. Exits 1 via get_config_path if the program was
    invoked with anything other than exactly one argument.

    Raises:
        ConfigError: If the config file is missing, malformed, or
            invalid.
        OutputError: If the output file cannot be written.
        MazegenError: If the maze parameters are invalid or the maze
            can't be generated/solved.
    """
    config_path = get_config_path()
    config = parse_config(load_config(config_path))
    generator = MazeGenerator(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit=config["EXIT"],
        perfect=config["PERFECT"],
        seed=config.get("SEED"),
    )
    generate_and_display(generator, config)

    while True:
        choice = input("\n[r]egenerate, [q]uit: ").strip().lower()
        if choice == "q":
            break
        if choice == "r":
            generate_and_display(generator, config)


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
