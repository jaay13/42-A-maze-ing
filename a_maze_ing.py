import sys

from app.config import ConfigError, load_config, parse_config
from mazegen import MazeGenerator, MazegenError

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "config.txt"


def main() -> None:
    """Load and validate the config, build a maze, and drive the CLI loop.

    Reads CONFIG_PATH, builds a MazeGenerator from the validated,
    typed config, prints the generated maze, and loops offering the
    user a chance to regenerate or quit.

    Raises:
        ConfigError: If the config file is missing, malformed, or
            invalid.
        MazegenError: If the maze parameters are invalid or the maze
            can't be generated/solved.
    """
    config = parse_config(load_config(CONFIG_PATH))
    generator = MazeGenerator(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit=config["EXIT"],
        perfect=config["PERFECT"],
        seed=int(config["SEED"]) if "SEED" in config else None,
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
    except MazegenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except ConfigError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
