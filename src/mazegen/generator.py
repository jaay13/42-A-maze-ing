import random

# STUB — Person A replaces this with the real backtracker/BFS/braiding engine.
# Hardcoded 5x5 fully-open-path grid so the application layer can be built
# and tested before the real algorithm exists. Wall encoding: N=1 E=2 S=4 W=8.

_STUB_GRID = [
    [12, 10, 10, 10, 14],
    [5, 12, 10, 10, 9],
    [5, 6, 9, 12, 5],
    [5, 3, 6, 5, 5],
    [3, 2, 3, 6, 3],
]


class MazeGenerator:
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
        return ["".join(f"{cell:x}" for cell in row) for row in self._grid]
