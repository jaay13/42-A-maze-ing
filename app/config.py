"""Config file loading and validation for a_maze_ing (Person B / app layer)."""


MANDATORY_CONFIG_KEYS = [
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
]


class ConfigError(Exception):
    """Raised when config.txt is missing, malformed, or invalid.

    Args:
        message: Human-readable description of what is wrong with the
            config file, including enough detail (line number, key
            name, or path) for the user to fix it.
    """


def load_config(path: str) -> dict[str, str]:
    """Read a KEY=VALUE config file into a dict of raw string values.

    Blank lines and lines starting with '#' are ignored. Keys are
    upper-cased so lookups don't depend on the casing used in the file.

    Args:
        path: Path to the config file to read.

    Returns:
        A dict mapping each upper-cased key to its raw string value.

    Raises:
        ConfigError: If the file doesn't exist, a non-blank/non-comment
            line has no '=', or a mandatory key is missing.
    """
    config: dict[str, str] = {}
    try:
        with open(path) as f:
            for line_nbr, line in enumerate(f, start=1):
                raw_line = line.rstrip("\n")
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                elif "=" not in line:
                    raise ConfigError(
                        f"[CONFIG_ERROR] Found corrupted line "
                        f"(No. {line_nbr}) in config: '{raw_line}'"
                    )
                key, value = line.split("=", 1)
                config[key.strip().upper()] = value.strip()
    except FileNotFoundError:
        raise ConfigError(
            f"[CONFIG_ERROR] No such file at following path '{path}' found"
        )
    check_mandatory_keys(config)
    return config


def check_mandatory_keys(config: dict) -> None:
    """Validate that every mandatory config key is present.

    Args:
        config: The raw config dict returned by load_config.

    Raises:
        ConfigError: If one or more mandatory keys are missing, naming
            all of the missing keys in a single message.
    """
    remainder = set(MANDATORY_CONFIG_KEYS) - set(config.keys())
    if remainder:
        missing = ", ".join(sorted(remainder))
        raise ConfigError(
            f"[CONFIG_ERROR] The config is missing mandatory keys: {missing}"
        )


def parse_int(raw: str, key: str) -> int:
    """Convert a raw string into an int.

    Used for WIDTH and HEIGHT.

    Args:
        raw: The raw value string, e.g. '5'.
        key: The config key this value came from, used in the error
            message (e.g. 'WIDTH').

    Returns:
        The parsed int.

    Raises:
        ConfigError: If raw isn't a valid integer.
    """
    try:
        x = int(raw)
    except ValueError:
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be an integer, got '{raw}'"
        )
    return x


def parse_coords(raw: str, key: str) -> tuple[int, int]:
    """Convert a 'x,y' string into a tuple of two ints.

    Used for ENTRY and EXIT.

    Args:
        raw: The raw coordinate string, e.g. '0,0'.
        key: The config key this value came from, used in the error
            message (e.g. 'ENTRY').

    Returns:
        A (x, y) tuple of ints.

    Raises:
        ConfigError: If raw doesn't split into exactly two integers
            separated by a comma.
    """
    try:
        a, b = raw.split(",")
        int_a = int(a)
        int_b = int(b)
    except ValueError:
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be two integers "
            f"separated by a comma, e.g. 'x,y' .. got '{raw}'"
        )
    return (int_a, int_b)