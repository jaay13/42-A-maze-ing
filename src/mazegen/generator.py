import random

# Subject IV.5: one hex digit per cell. A set bit means that wall is CLOSED.
NORTH: int = 1  # bit 0
EAST: int = 2   # bit 1
SOUTH: int = 4  # bit 2
WEST: int = 8   # bit 3
ALL_WALLS: int = NORTH | EAST | SOUTH | WEST  # 15 / 0xF, fully closed cell

# Step from a cell to the neighbour on that side: (dx, dy).
_DELTA: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

# The same shared wall, seen from the other cell.
_OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

# STUB — still used by generate() until the backtracker lands.
# Hardcoded 5x5 so the app layer keeps working in the meantime.
_STUB_GRID = [
    [12, 10, 10, 10, 14],
    [5, 12, 10, 10, 9],
    [5, 6, 9, 12, 5],
    [5, 3, 6, 5, 5],
    [3, 2, 3, 6, 3],
]


class MazeGenerator:
    """Reusable maze engine. Public surface is frozen in INTERFACE.md."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        perfect: bool = False,
        seed: int | None = None,
        algorithm: str = "backtracker",
    ) -> None:
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.seed = seed
        self.algorithm = algorithm
        self._rng = random.Random(seed)
        self._grid: list[list[int]] = []

    def _in_bounds(self, x: int, y: int) -> bool:
        """True if (x, y) is a cell inside the maze."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _init_grid(self) -> None:
        """Start every cell fully closed. Passages are opened later."""
        self._grid = [
            [ALL_WALLS] * self.width for _ in range(self.height)
        ]

    def _open_wall(self, x: int, y: int, wall: int) -> None:
        """Open one wall and the neighbour's matching opposite wall.

        Subject IV.4: shared walls must agree. If there is no neighbour
        (outer border), leave the wall closed.
        """
        dx, dy = _DELTA[wall]
        nx = x + dx
        ny = y + dy
        if not self._in_bounds(nx, ny):
            return
        self._grid[y][x] &= ~wall
        self._grid[ny][nx] &= ~_OPPOSITE[wall]

    def generate(self) -> None:
        self._grid = [row[: self.width] for row in _STUB_GRID[: self.height]]

    @property
    def grid(self) -> list[list[int]]:
        return self._grid

    @property
    def pattern_cells(self) -> frozenset[tuple[int, int]]:
        return frozenset()

    @property
    def has_pattern(self) -> bool:
        return False

    def solve(self) -> list[str]:
        return ["E"] * (self.width - 1) + ["S"] * (self.height - 1)

    def to_rows(self) -> list[str]:
        """One hex digit per cell, row by row (Subject IV.5)."""
        return ["".join(f"{cell:x}" for cell in row) for row in self._grid]
