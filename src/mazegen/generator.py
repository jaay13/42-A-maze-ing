import random
from collections import deque

from .errors import (
    InvalidCoordinateError,
    InvalidDimensionError,
    NoSolutionError,
)

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
        self._validate()

    def _validate(self) -> None:
        """Raise if size or entry/exit cannot make a maze.

        Subject IV.4: entry and exit exist, differ, and lie inside the
        grid. A 1xN strip or a negative size is not a maze, so those
        fail here too, before generate() indexes the grid. Python would
        otherwise treat ENTRY=-1,0 as the last cell of the row.
        """
        if self.width < 2 or self.height < 2:
            raise InvalidDimensionError(
                "width and height must be at least 2, "
                f"got {self.width}x{self.height}"
            )
        if self.entry == self.exit:
            raise InvalidCoordinateError(
                "entry and exit must be different cells"
            )
        for name, cell in (("entry", self.entry), ("exit", self.exit)):
            x, y = cell
            if not self._in_bounds(x, y):
                raise InvalidCoordinateError(
                    f"{name} {cell} is outside the "
                    f"{self.width}x{self.height} maze"
                )

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

    def _corner_cells(self) -> set[tuple[int, int]]:
        """The four outer corners."""
        w = self.width
        h = self.height
        return {(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)}

    def _centre_cells(self) -> set[tuple[int, int]]:
        """Pac-Man start cell(s). Same rule as maze_analyzer.

        Odd size: one middle cell. Even size: the 2x2 around the middle.
        Only *one* of those must stay a corridor, so the 42 may cover
        the others and still sit in the visual centre.
        """
        w = self.width
        h = self.height
        rows = {h // 2} if h % 2 else {h // 2 - 1, h // 2}
        cols = {w // 2} if w % 2 else {w // 2 - 1, w // 2}
        return {(x, y) for y in rows for x in cols}

    def _hard_forbidden(self) -> set[tuple[int, int]]:
        """Cells the 42 must never cover: entry, exit, corners."""
        return {self.entry, self.exit} | self._corner_cells()

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
        centre, not the first fit from the top-left.

        The app (Person B) prints the console message when has_pattern
        is False. The engine never prints.
        """
        self._pattern_cells = frozenset()
        self._has_pattern = False
        if self.width < _PATTERN_W or self.height < _PATTERN_H:
            return
        hard = self._hard_forbidden()
        centres = self._centre_cells()
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
                blocked = set(cells)
                if any(cell in hard for cell in cells):
                    continue
                # Analyzer: at least one centre candidate stays a corridor.
                if centres and not (centres - blocked):
                    continue
                if not self._remainder_connected(blocked):
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

        Start at the entry. Walk into a random unvisited neighbour and
        knock the wall down. Dead end: pop the stack and try another
        neighbour. Pattern cells are marked visited first, so they stay
        fully closed and the walk goes around them.

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

    def _degree(self, x: int, y: int) -> int:
        """How many open passages this cell has to in-bound neighbours."""
        n = 0
        for wall, (dx, dy) in _DELTA.items():
            if self._grid[y][x] & wall:
                continue
            nx = x + dx
            ny = y + dy
            if self._in_bounds(nx, ny):
                n += 1
        return n

    def _block_is_open_3x3(self, x: int, y: int) -> bool:
        """True if the 3x3 with top-left (x, y) has no internal walls.

        Only east walls inside the window and south walls inside the
        window matter. The outer edge of the 3x3 is the hall boundary,
        not an internal opening.
        """
        for dy in range(3):
            for dx in range(2):
                if self._grid[y + dy][x + dx] & EAST:
                    return False
        for dy in range(2):
            for dx in range(3):
                if self._grid[y + dy][x + dx] & SOUTH:
                    return False
        return True

    def _has_open_3x3(self) -> bool:
        """True if any 3x3 block has all internal walls open."""
        for y in range(self.height - 2):
            for x in range(self.width - 2):
                if self._block_is_open_3x3(x, y):
                    return True
        return False

    def _creates_open_3x3(self, x: int, y: int, wall: int) -> bool:
        """True if opening this wall would make a 3x3 hall.

        Open, inspect, restore. The eval asks how the 3x3 rule is
        verified: the check lives in the removal loop, not as a cleanup
        pass afterwards.
        """
        dx, dy = _DELTA[wall]
        nx = x + dx
        ny = y + dy
        old_a = self._grid[y][x]
        old_b = self._grid[ny][nx]
        self._open_wall(x, y, wall)
        bad = self._has_open_3x3()
        self._grid[y][x] = old_a
        self._grid[ny][nx] = old_b
        return bad

    def _closed_interior_walls(
        self, x: int, y: int
    ) -> list[int]:
        """Closed walls that lead to a normal (non-42) neighbour."""
        walls: list[int] = []
        for wall, (dx, dy) in _DELTA.items():
            if not (self._grid[y][x] & wall):
                continue
            nx = x + dx
            ny = y + dy
            if not self._in_bounds(nx, ny):
                continue
            if (nx, ny) in self._pattern_cells:
                continue
            walls.append(wall)
        return walls

    def _try_open(self, x: int, y: int, wall: int) -> bool:
        """Open one wall unless that would create a 3x3 hall."""
        if self._creates_open_3x3(x, y, wall):
            return False
        self._open_wall(x, y, wall)
        return True

    def _braid(self) -> None:
        """Open dead-ends so the board has loops (A6).

        Subject: PERFECT=False needs at least two independent routes.
        A couple of real dead-ends are tolerated; 42-enclosed ones do
        not count. Each candidate wall is checked for 3x3 first.
        """
        limit = self.width * self.height * 4
        for _ in range(limit):
            dead: list[tuple[int, int]] = []
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) in self._pattern_cells:
                        continue
                    if self._degree(x, y) == 1:
                        dead.append((x, y))
            if not dead:
                return
            self._rng.shuffle(dead)
            opened = False
            for x, y in dead:
                if self._degree(x, y) != 1:
                    continue
                walls = self._closed_interior_walls(x, y)
                if not walls:
                    continue
                self._rng.shuffle(walls)
                for wall in walls:
                    if self._try_open(x, y, wall):
                        opened = True
                        break
            if not opened:
                return

    def _key_cells(self) -> set[tuple[int, int]]:
        """Corners plus centre: Pac-Man start / ghost seats."""
        w = self.width
        h = self.height
        cells: set[tuple[int, int]] = {
            (0, 0),
            (w - 1, 0),
            (0, h - 1),
            (w - 1, h - 1),
        }
        rows = {h // 2} if h % 2 else {h // 2 - 1, h // 2}
        cols = {w // 2} if w % 2 else {w // 2 - 1, w // 2}
        for y in rows:
            for x in cols:
                cells.add((x, y))
        return cells

    def _open_key_cells(self) -> None:
        """Give corners and centre a second exit when 3x3 allows it."""
        keys = [cell for cell in self._key_cells()
                if cell not in self._pattern_cells]
        self._rng.shuffle(keys)
        for x, y in keys:
            if self._degree(x, y) >= 2:
                continue
            walls = self._closed_interior_walls(x, y)
            self._rng.shuffle(walls)
            for wall in walls:
                if self._try_open(x, y, wall) and self._degree(x, y) >= 2:
                    break

    def generate(self) -> None:
        """Build the maze in a fixed order.

        Re-seed first so the same seed always rebuilds the same maze.
        Stamp the 42 (or skip it), then carve a perfect maze. If
        PERFECT is false, braid dead-ends and open corners plus centre.
        Each extra opening is refused if it would create a 3x3 hall.
        """
        self._rng = random.Random(self.seed)
        self._init_grid()
        self._place_pattern()
        self._carve()
        if not self.perfect:
            self._braid()
            self._open_key_cells()

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
        """Shortest path from entry to exit as N/E/S/W.

        BFS, not DFS: popleft spreads in waves, so the first time the
        exit is reached the route is the shortest. The app must call
        this once and reuse the list for the file and the screen.
        """
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
