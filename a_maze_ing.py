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
            file=sys.stderr
        )
        sys.exit(1)
    return sys.argv[1]


def main() -> None:
    """Load and validate the config, build a maze, and drive the CLI loop.

    Reads the config file named on the command line, builds a
    MazeGenerator from the validated, typed config, prints the
    generated maze, and loops offering the user a chance to regenerate
    or quit. Exits 1 via get_config_path if the program was invoked
    with anything other than exactly one argument.

    Raises:
        ConfigError: If the config file is missing, malformed, or
            invalid.
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
    generator.generate()

    for row in generator.to_rows():
        print(row)
    print(f"entry={generator.entry} exit={generator.exit}")
    print(" ".join(generator.solve()))

    while True:
        choice = input("\n[r]egenerate, [q]uit: ").strip().lower()
        if choice == "q":
            break
        if choice == "r":
            generator.generate()
            for row in generator.to_rows():
                print(row)


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
