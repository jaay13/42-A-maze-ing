"""Exception hierarchy for the application layer.

Mirrors src/mazegen/errors.py so both halves of the project have the
same shape: the engine raises MazegenError subclasses, the app raises
AppError subclasses, and a_maze_ing.py catches one of each.
"""


class AppError(Exception):
    """Base class for every error the application layer raises.

    Lets a_maze_ing.py catch a single type at the top level. Subclasses
    carry their own '[CATEGORY]' prefix in the message, since one handler
    cannot know which kind it caught.
    """


class ConfigError(AppError):
    """Raised when config.txt is missing, malformed, or invalid.

    Args:
        message: What is wrong, with enough detail (line number, key name
            or path) for the user to fix it.
    """


class OutputError(AppError):
    """Raised when the maze output file cannot be written.

    Separate from ConfigError because the config was read fine: the
    failure is in writing OUTPUT_FILE, not in the user's settings.

    Args:
        message: What went wrong, including the output path.
    """


class RenderError(AppError):
    """Raised when the maze cannot be drawn for the terminal.

    Separate from MazegenError because the app detects these: the engine
    returned successfully, but the data it handed over does not match
    INTERFACE.md. No user input can trigger this, only a contract
    violation.

    Args:
        message: What could not be drawn, including the offending value.
    """
