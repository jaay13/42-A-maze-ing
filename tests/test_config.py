"""Tests for config loading and parsing in app/config.py."""

from pathlib import Path

import pytest

from app.config import load_config, parse_config
from app.errors import ConfigError

VALID = (
    "WIDTH=10\n"
    "HEIGHT=8\n"
    "ENTRY=0,0\n"
    "EXIT=9,7\n"
    "OUTPUT_FILE=maze.txt\n"
    "PERFECT=true\n"
)


def write(tmp_path: Path, text: str) -> str:
    """Write text to a config file and return its path."""
    path = tmp_path / "config.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_valid_config_round_trip(tmp_path: Path) -> None:
    config = parse_config(load_config(write(tmp_path, VALID)))
    assert config == {
        "WIDTH": 10,
        "HEIGHT": 8,
        "ENTRY": (0, 0),
        "EXIT": (9, 7),
        "OUTPUT_FILE": "maze.txt",
        "PERFECT": True,
    }


def test_comments_blank_lines_and_key_case_are_ignored(
    tmp_path: Path,
) -> None:
    text = "# header\n\n" + VALID.replace("WIDTH", "width") + "SEED=42\n"
    config = parse_config(load_config(write(tmp_path, text)))
    assert config["WIDTH"] == 10
    assert config["SEED"] == 42


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="CONFIG_ERROR"):
        load_config(str(tmp_path / "nope.txt"))


def test_directory_instead_of_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="CONFIG_ERROR"):
        load_config(str(tmp_path))


def test_non_utf8_file_is_a_config_error(tmp_path: Path) -> None:
    path = tmp_path / "config.txt"
    path.write_bytes(b"WIDTH=10\xff\xfe\n")
    with pytest.raises(ConfigError, match="not UTF-8"):
        load_config(str(path))


def test_duplicate_key_names_both_lines(tmp_path: Path) -> None:
    path = write(tmp_path, VALID + "width=3\n")
    with pytest.raises(ConfigError, match=r"'WIDTH'.*lines 1 and 7"):
        load_config(path)


def test_line_without_equals(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"line \(No. 2\)"):
        load_config(write(tmp_path, "WIDTH=10\nHEIGHT 8\n"))


def test_missing_mandatory_keys_are_all_named(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="EXIT, HEIGHT"):
        load_config(write(tmp_path, VALID.replace("HEIGHT=8\n", "")
                          .replace("EXIT=9,7\n", "")))


def test_unknown_key(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="SED"):
        load_config(write(tmp_path, VALID + "SED=42\n"))


@pytest.mark.parametrize(
    "key, value",
    [
        ("WIDTH", "ten"),
        ("HEIGHT", "8.5"),
        ("ENTRY", "0"),
        ("ENTRY", "0,0,0"),
        ("EXIT", "a,b"),
        ("PERFECT", "yes"),
        ("SEED", "x"),
        ("RENDERER", "svg"),
        ("ANIMATION_DELAY", "-1"),
    ],
)
def test_bad_values(tmp_path: Path, key: str, value: str) -> None:
    lines = [ln for ln in VALID.splitlines() if not ln.startswith(key)]
    text = "\n".join(lines) + f"\n{key}={value}\n"
    raw = load_config(write(tmp_path, text))
    with pytest.raises(ConfigError, match=key):
        parse_config(raw)
