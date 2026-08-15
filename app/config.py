"""Config file loading and validation for a_maze_ing (Person B / app layer)."""


MANDATORY_CONFIG_KEYS = [
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
]


class ConfigError(Exception):
    """Raised when config.txt is missing, malformed, or invalid.

    Args:
        message: Description of what is wrong with the
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
            line has no '=', a mandatory key is missing, or the file
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
    except FileNotFoundError:
        raise ConfigError(
            f"[CONFIG_ERROR] No such file at following path '{path}' found"
        )
    check_mandatory_keys(config)
    check_unknown_keys(config)
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


def check_unknown_keys(config: dict) -> None:
    """Reject any config key the program does not recognise.

    Unknown keys are an error rather than a silent pass-through so that
    a typo in an optional key (e.g. 'SED' for 'SEED') fails loudly
    instead of quietly changing behaviour. Adding a new key to the
    config format therefore means registering it in
    MANDATORY_CONFIG_KEYS or OPTIONAL_CONVERTERS.

    Args:
        config: The raw config dict returned by load_config.

    Raises:
        ConfigError: If the config contains one or more keys that are
            neither mandatory nor optional, naming all of them in a
            single message.
    """
    known_keys = set(MANDATORY_CONFIG_KEYS) | set(OPTIONAL_CONVERTERS)
    remainder = set(config.keys()) - known_keys
    if remainder:
        unrecognised = ", ".join(sorted(remainder))
        raise ConfigError(
            f"[CONFIG_ERROR] The config has unrecognised keys: {unrecognised}"
        )


def parse_int(raw: str, key: str) -> int:
    """Convert a raw string into an int.

    Used for WIDTH, HEIGHT and SEED.

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


def parse_bool(raw: str, key: str) -> bool:
    """Convert a raw string into a bool.

    Used for PERFECT.

    Args:
        raw: The raw value string, e.g. 'true' or 'False'.
        key: The config key this value came from, used in the error
            message (e.g. 'PERFECT').

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


CONVERTERS = {
    "WIDTH": parse_int, "HEIGHT": parse_int, "ENTRY": parse_coords,
    "EXIT": parse_coords, "PERFECT": parse_bool
}

OPTIONAL_CONVERTERS = {
    "SEED": parse_int
}


def parse_config(raw: dict) -> dict:
    """Convert known config values to their real types.

    WIDTH/HEIGHT become int, ENTRY/EXIT become (int, int) tuples, and
    PERFECT becomes bool. SEED becomes int, but only when the key is
    present: an absent optional key stays absent rather than becoming
    None. Every other key (e.g. OUTPUT_FILE) is passed through
    unchanged.

    Args:
        raw: The raw string-valued dict returned by load_config.

    Returns:
        A dict with the same keys as raw, but with known values
        converted to their proper types.

    Raises:
        ConfigError: If any known value fails its conversion.
    """
    typed_dict = {}
    for k, converter in CONVERTERS.items():
        typed_dict[k] = converter(raw[k], k)

    for k, converter in OPTIONAL_CONVERTERS.items():
        if k in raw:
            typed_dict[k] = converter(raw[k], k)

    for k, v in raw.items():
        if k not in typed_dict:
            typed_dict[k] = v

    return typed_dict
