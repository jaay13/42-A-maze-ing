"""Config file loading and validation for a_maze_ing (Person B / app layer)."""


MANDATORY_CONFIG_KEYS = [
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"
]


class ConfigError(Exception):
    """Raised when config.txt is missing, malformed, or invalid."""


def load_config(path: str) -> dict[str, str]:
    """Read a KEY=VALUE config file into a dict of raw string values.

    Blank lines and lines starting with '#' are ignored. Keys are
    upper-cased so lookups don't depend on the casing used in the file.
    Raises ConfigError if the file doesn't exist, a non-blank/non-comment
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
    check_config(config)
    return config


def check_config(config: dict) -> None:
    """Raise ConfigError listing every mandatory key missing from config."""
    remainder = set(MANDATORY_CONFIG_KEYS) - set(config.keys())
    if remainder:
        missing = ", ".join(sorted(remainder))
        raise ConfigError(
            f"[CONFIG_ERROR] The config is missing mandatory keys: {missing}"
        )
