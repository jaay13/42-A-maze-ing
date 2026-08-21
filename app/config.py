"""Config file loading and validation for a_maze_ing (Person B / app layer)."""

from typing import Any

from .errors import ConfigError

MANDATORY_CONFIG_KEYS = [
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
]


def load_config(path: str) -> dict[str, str]:
    """Read a KEY=VALUE config file into a dict of raw string values.

    Blank lines and lines starting with '#' are ignored. Keys are
    upper-cased so lookups don't depend on the casing used in the file.

    Args:
        path: Path to the config file to read.

    Returns:
        A dict mapping each upper-cased key to its raw string value.

    Raises:
        ConfigError: If the file cannot be read at all (missing,
            unreadable, a directory, ...), a non-blank/non-comment line
            has no '=', a mandatory key is missing, or the file
            contains a key the program does not recognise.
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
    except OSError as e:
        raise ConfigError(
            f"[CONFIG_ERROR] {e.strerror}: '{path}'"
        ) from e
    check_mandatory_keys(config)
    check_unknown_keys(config)
    return config


def check_mandatory_keys(config: dict[str, str]) -> None:
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


def check_unknown_keys(config: dict[str, str]) -> None:
    """Reject any config key the program does not recognise.

    Unknown keys are an error rather than a silent pass-through so a typo
    in an optional key ('SED' for 'SEED') fails loudly. A new config key
    must therefore be registered in MANDATORY_CONFIG_KEYS or
    OPTIONAL_CONVERTERS.

    Args:
        config: The raw config dict returned by load_config.

    Raises:
        ConfigError: If the config contains one or more keys that are
            neither mandatory nor optional, naming all of them in a single
            message.
    """
    known_keys = set(MANDATORY_CONFIG_KEYS) | set(OPTIONAL_CONVERTERS)
    remainder = set(config.keys()) - known_keys
    if remainder:
        unrecognised = ", ".join(sorted(remainder))
        raise ConfigError(
            f"[CONFIG_ERROR] The config has unrecognised keys: {unrecognised}"
        )


def parse_int(raw: str, key: str) -> int:
    """Convert a raw string into an int, for WIDTH, HEIGHT and SEED.

    Args:
        raw: The raw value string, e.g. '5'.
        key: The config key, named in the error message.

    Returns:
        The parsed int.

    Raises:
        ConfigError: If raw is not a valid integer.
    """
    try:
        x = int(raw)
    except ValueError:
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be an integer, got '{raw}'"
        )
    return x


def parse_coords(raw: str, key: str) -> tuple[int, int]:
    """Convert a 'x,y' string into a tuple of two ints, for ENTRY/EXIT.

    Args:
        raw: The raw coordinate string, e.g. '0,0'.
        key: The config key, named in the error message.

    Returns:
        A (x, y) tuple of ints.

    Raises:
        ConfigError: If raw does not split into exactly two integers
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


def parse_bool(raw: str, key: str) -> bool:
    """Convert a raw string into a bool, for PERFECT.

    Args:
        raw: The raw value string, e.g. 'true' or 'False'.
        key: The config key, named in the error message.

    Returns:
        True if raw is 'true' (case-insensitive), False if 'false'.

    Raises:
        ConfigError: If raw is anything other than 'true'/'false'.
    """
    lower = raw.lower()
    if not (lower == "true" or lower == "false"):
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be either true/false "
            f"(case-insensitive), got '{raw}'"
        )
    return lower == "true"


def parse_renderer(raw: str, key: str) -> str:
    """Convert a raw string into a renderer name, for RENDERER.

    The value is a preference, not a guarantee: a run whose stdout is not
    a terminal falls back to plain ASCII whatever this says.

    Args:
        raw: The raw value string, e.g. 'blocks' or 'ASCII'.
        key: The config key, named in the error message.

    Returns:
        'ascii' or 'blocks', lowercased.

    Raises:
        ConfigError: If raw is anything other than 'ascii'/'blocks'.
    """
    lower = raw.lower()
    if not (lower == "ascii" or lower == "blocks"):
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be either ascii/blocks "
            f"(case-insensitive), got '{raw}'"
        )
    return lower


def parse_delay(raw: str, key: str) -> int:
    """Convert a raw string into a frame delay in milliseconds.

    Used for ANIMATION_DELAY. Zero disables the animation.

    Args:
        raw: The raw value string, e.g. '30'.
        key: The config key, named in the error message.

    Returns:
        The delay in milliseconds, zero or more.

    Raises:
        ConfigError: If raw is not an integer, or is negative.
    """
    ms = parse_int(raw, key)
    # A negative delay would otherwise reach time.sleep and raise,
    # landing in the last-resort handler instead of being reported
    # as the config error it is.
    if ms < 0:
        raise ConfigError(
            f"[CONFIG_ERROR] '{key}' must be zero or more milliseconds, "
            f"got '{raw}'"
        )
    return ms


CONVERTERS = {
    "WIDTH": parse_int, "HEIGHT": parse_int, "ENTRY": parse_coords,
    "EXIT": parse_coords, "PERFECT": parse_bool
}

OPTIONAL_CONVERTERS = {
    "SEED": parse_int, "RENDERER": parse_renderer,
    "ANIMATION_DELAY": parse_delay
}


def parse_config(raw: dict[str, str]) -> dict[str, Any]:
    """Convert known config values to their real types.

    WIDTH/HEIGHT become int, ENTRY/EXIT become (int, int) tuples, and
    PERFECT becomes bool. The optional keys SEED and RENDERER are
    converted only when present: an absent optional key stays absent
    rather than becoming None, so the caller supplies its own default.
    Every other key (e.g. OUTPUT_FILE) is passed through unchanged.

    Args:
        raw: The raw string-valued dict returned by load_config.

    Returns:
        A dict with the same keys as raw, but with known values
        converted to their proper types.

    Raises:
        ConfigError: If any known value fails its conversion.
    """
    typed_dict: dict[str, Any] = {}
    for k, converter in CONVERTERS.items():
        typed_dict[k] = converter(raw[k], k)

    for k, converter in OPTIONAL_CONVERTERS.items():
        if k in raw:
            typed_dict[k] = converter(raw[k], k)

    for k, v in raw.items():
        if k not in typed_dict:
            typed_dict[k] = v

    return typed_dict
