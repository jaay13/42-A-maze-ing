"""Exception hierarchy for the application layer.

Mirrors src/mazegen/errors.py so both halves of the project have the
same shape: the engine raises MazegenError subclasses, the app raises
AppError subclasses, and a_maze_ing.py catches one of each.
"""


class AppError(Exception):
    """Base class for every error the application layer raises.

    Exists so a_maze_ing.py can catch a single type at the top level.
    Without it each new kind of app error would need its own except
    clause, and the handler block would grow with every backlog item.
    Subclasses carry their own '[CATEGORY]' prefix in the message,
    since one handler cannot know which kind it caught.
    """


class ConfigError(AppError):
    """Raised when config.txt is missing, malformed, or invalid.

    Args:
        message: Description of what is wrong with the
            config file, including enough detail (line number, key
            name, or path) for the user to fix it.
    """


class OutputError(AppError):
    """Raised when the maze output file cannot be written.

    Separate from ConfigError because the config was read fine: the
    failure is in writing OUTPUT_FILE, not in the user's settings.

    Args:
        message: Description of what went wrong, including the output
            path, so the user can fix it.
    """
