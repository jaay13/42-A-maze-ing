import sys

from mazegen import MazeGenerator, MazegenError

# CP1 skeleton: config parsing (B1), output writing (B3), rendering (B4) and
# the real menu (B5) land later. This just proves the app can drive the
# engine end to end.

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else "config.txt"


def load_config(path: str) -> dict[str, str]:
    config: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().upper()] = value.strip()
    return config


def parse_coord(raw: str) -> tuple[int, int]:
    x, y = raw.strip("() ").split(",")
    return int(x), int(y)


def main() -> None:
    config = load_config(CONFIG_PATH)
    generator = MazeGenerator(
        width=int(config["WIDTH"]),
        height=int(config["HEIGHT"]),
        entry=parse_coord(config["ENTRY"]),
        exit=parse_coord(config["EXIT"]),
        perfect=config.get("PERFECT", "false").lower() == "true",
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
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
