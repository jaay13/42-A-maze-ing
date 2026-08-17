import random
from collections import deque

from .errors import NoSolutionError

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

_DIR_LETTER: dict[int, str] = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}


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

    def _carve(self) -> None:
        """Carve a perfect maze with an iterative recursive-backtracker.

        An explicit stack is used instead of recursion so a 200x200
        maze cannot blow the call stack at defence.
        """
        visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        start_x, start_y = self.entry
        stack: list[tuple[int, int]] = [(start_x, start_y)]
        visited[start_y][start_x] = True

        while stack:
            x, y = stack[-1]
            options: list[tuple[int, int, int]] = []
            for wall, (dx, dy) in _DELTA.items():
                nx = x + dx
                ny = y + dy
                if self._in_bounds(nx, ny) and not visited[ny][nx]:
                    options.append((nx, ny, wall))
            if not options:
                stack.pop()
                continue
            nx, ny, wall = self._rng.choice(options)
            self._open_wall(x, y, wall)
            visited[ny][nx] = True
            stack.append((nx, ny))

    def generate(self) -> None:
        # Re-seed so the same seed always rebuilds the same maze.
        self._rng = random.Random(self.seed)
        self._init_grid()
        self._carve()

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
        """Shortest path from entry to exit as N/E/S/W (BFS, not DFS)."""
        start = self.entry
        goal = self.exit
        queue: deque[tuple[int, int]] = deque([start])
        # Maps a cell to (previous cell, step letter). Start has none.
        prev: dict[
            tuple[int, int],
            tuple[tuple[int, int], str] | None,
        ] = {start: None}

        found = False
        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                found = True
                break
            for wall, (dx, dy) in _DELTA.items():
                if self._grid[y][x] & wall:
                    continue
                nx = x + dx
                ny = y + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in prev:
                    continue
                prev[(nx, ny)] = ((x, y), _DIR_LETTER[wall])
                queue.append((nx, ny))

        if not found or goal not in prev:
            raise NoSolutionError("no path from entry to exit")

        path: list[str] = []
        cur: tuple[int, int] = goal
        while cur != start:
            step = prev[cur]
            if step is None:
                break
            parent, letter = step
            path.append(letter)
            cur = parent
        path.reverse()
        return path

    def to_rows(self) -> list[str]:
        """One hex digit per cell, row by row (Subject IV.5)."""
        return ["".join(f"{cell:x}" for cell in row) for row in self._grid]
