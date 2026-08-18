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

# "42" glyph: digit 4 (3 cols), one-col gap, digit 2 (3 cols). 5 rows.
_PATTERN_W = 7
_PATTERN_H = 5
_PATTERN_42: tuple[tuple[int, int], ...] = (
    (0, 0), (2, 0),
    (0, 1), (2, 1),
    (0, 2), (1, 2), (2, 2),
    (2, 3),
    (2, 4),
    (4, 0), (5, 0), (6, 0),
    (6, 1),
    (4, 2), (5, 2), (6, 2),
    (4, 3),
    (4, 4), (5, 4), (6, 4),
)


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
        self._pattern_cells: frozenset[tuple[int, int]] = frozenset()
        self._has_pattern: bool = False

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

    def _forbidden_cells(self) -> set[tuple[int, int]]:
        """Cells the 42 glyph must not cover (entry, exit, corners, centre)."""
        w = self.width
        h = self.height
        cells: set[tuple[int, int]] = {
            self.entry,
            self.exit,
            (0, 0),
            (w - 1, 0),
            (0, h - 1),
            (w - 1, h - 1),
        }
        # Same centre rule as tools/maze_analyzer.py
        rows = {h // 2} if h % 2 else {h // 2 - 1, h // 2}
        cols = {w // 2} if w % 2 else {w // 2 - 1, w // 2}
        for y in rows:
            for x in cols:
                cells.add((x, y))
        return cells

    def _remainder_connected(
        self,
        blocked: set[tuple[int, int]],
    ) -> bool:
        """True if every non-blocked cell is reachable from entry."""
        if self.entry in blocked or self.exit in blocked:
            return False
        seen: set[tuple[int, int]] = {self.entry}
        queue: deque[tuple[int, int]] = deque([self.entry])
        while queue:
            x, y = queue.popleft()
            for dx, dy in _DELTA.values():
                nx = x + dx
                ny = y + dy
                nxt = (nx, ny)
                if not self._in_bounds(nx, ny):
                    continue
                if nxt in blocked or nxt in seen:
                    continue
                seen.add(nxt)
                queue.append(nxt)
        open_count = self.width * self.height - len(blocked)
        return len(seen) == open_count

    def _place_pattern(self) -> None:
        """Stamp a 42 of fully closed cells, or skip if it cannot fit.

        Subject pictures put the glyph in the middle of the maze. The
        exact centre cell stays open (Pac-Man player start), so we pick
        the valid offset whose glyph centre is closest to the maze
        centre — not the first fit from the top-left.

        The app (Person B) prints the console message when has_pattern
        is False. The engine never prints.
        """
        self._pattern_cells = frozenset()
        self._has_pattern = False
        if self.width < _PATTERN_W or self.height < _PATTERN_H:
            return
        forbidden = self._forbidden_cells()
        max_ox = self.width - _PATTERN_W
        max_oy = self.height - _PATTERN_H
        mid_x = (self.width - 1) / 2
        mid_y = (self.height - 1) / 2
        best_dist: float | None = None
        best_cells: list[tuple[int, int]] | None = None
        for oy in range(max_oy + 1):
            for ox in range(max_ox + 1):
                cells = [
                    (ox + dx, oy + dy) for dx, dy in _PATTERN_42
                ]
                if any(cell in forbidden for cell in cells):
                    continue
                if not self._remainder_connected(set(cells)):
                    continue
                glyph_x = ox + (_PATTERN_W - 1) / 2
                glyph_y = oy + (_PATTERN_H - 1) / 2
                dist = (glyph_x - mid_x) ** 2 + (glyph_y - mid_y) ** 2
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_cells = cells
        if best_cells is None:
            return
        self._pattern_cells = frozenset(best_cells)
        self._has_pattern = True

    def _carve(self) -> None:
        """Carve a perfect maze with an iterative recursive-backtracker.

        An explicit stack is used instead of recursion so a 200x200
        maze cannot blow the call stack at defence.
        """
        visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        # Pattern cells stay fully closed; never carve into them.
        for px, py in self._pattern_cells:
            visited[py][px] = True
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
        self._place_pattern()
        self._carve()

    @property
    def grid(self) -> list[list[int]]:
        return self._grid

    @property
    def pattern_cells(self) -> frozenset[tuple[int, int]]:
        return self._pattern_cells

    @property
    def has_pattern(self) -> bool:
        return self._has_pattern

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
