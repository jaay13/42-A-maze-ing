"""Typed exceptions raised by the maze generator.

Every exception the app is allowed to see subclasses MazegenError, so
a single ``except MazegenError`` catches them all.
"""


class MazegenError(Exception):
    """Base class for every mazegen failure."""


class InvalidDimensionError(MazegenError):
    """Raised when width or height cannot make a maze."""


class InvalidCoordinateError(MazegenError):
    """Raised when entry or exit is invalid or out of bounds."""


class ImpossibleMazeError(MazegenError):
    """Raised when the requested maze cannot be built."""


class NoSolutionError(MazegenError):
    """Raised when ``solve()`` finds no path from entry to exit."""
