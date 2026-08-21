"""Public mazegen package surface.

Re-exports ``MazeGenerator`` and the typed ``MazegenError`` hierarchy
used by the application layer.
"""

from .errors import (
    ImpossibleMazeError,
    InvalidCoordinateError,
    InvalidDimensionError,
    MazegenError,
    NoSolutionError,
)
from .generator import MazeGenerator

__all__ = [
    "MazeGenerator",
    "MazegenError",
    "InvalidDimensionError",
    "InvalidCoordinateError",
    "ImpossibleMazeError",
    "NoSolutionError",
]
