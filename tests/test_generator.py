"""Invariant tests for the mazegen engine.

Each test builds mazes over a spread of sizes, seeds and entry/exit
positions and checks a property the subject requires, rather than a
hand-drawn expected grid that would break on any algorithm change.
"""

import itertools
import random
from collections import deque

import pytest

from mazegen import (
    InvalidCoordinateError,
    InvalidDimensionError,
    MazeGenerator,
    NoSolutionError,
)

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
DELTA = {NORTH: (0, -1), EAST: (1, 0), SOUTH: (0, 1), WEST: (-1, 0)}
OPPOSITE = {NORTH: SOUTH, EAST: WEST, SOUTH: NORTH, WEST: EAST}
LETTER = {"N": NORTH, "E": EAST, "S": SOUTH, "W": WEST}

Cell = tuple[int, int]

SIZES = [(2, 2), (3, 5), (5, 3), (7, 5), (8, 6), (10, 10), (15, 15),
         (20, 9)]


def cases() -> list[tuple[int, int, Cell, Cell, bool, int]]:
    """Return (width, height, entry, exit, perfect, seed) combinations."""
    rng = random.Random(0)
    out = []
    for (w, h), perfect, seed in itertools.product(
        SIZES, (True, False), range(3)
    ):
        cells = [(x, y) for y in range(h) for x in range(w)]
        entry, exit_ = rng.sample(cells, 2)
        out.append((w, h, entry, exit_, perfect, seed))
    return out


def build(w: int, h: int, entry: Cell, exit_: Cell, perfect: bool,
          seed: int) -> MazeGenerator:
    """Construct and generate a maze."""
    maze = MazeGenerator(w, h, entry, exit_, perfect=perfect, seed=seed)
    maze.generate()
    return maze


def neighbours(maze: MazeGenerator, x: int, y: int) -> list[Cell]:
    """Return in-bound cells reachable from (x, y) through open walls."""
    out = []
    for wall, (dx, dy) in DELTA.items():
        nx, ny = x + dx, y + dy
        if (0 <= nx < maze.width and 0 <= ny < maze.height
                and not maze.grid[y][x] & wall):
            out.append((nx, ny))
    return out


def distances(maze: MazeGenerator, start: Cell) -> dict[Cell, int]:
    """BFS distance from start to every reachable cell."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for nxt in neighbours(maze, *cur):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                queue.append(nxt)
    return dist


def open_cells(maze: MazeGenerator) -> set[Cell]:
    """Every cell that is not part of the 42 pattern."""
    all_cells = {(x, y) for y in range(maze.height)
                 for x in range(maze.width)}
    return all_cells - maze.pattern_cells


ALL = pytest.mark.parametrize("w, h, entry, exit_, perfect, seed", cases())


@ALL
def test_walls_are_consistent_and_border_closed(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    for y, x in itertools.product(range(h), range(w)):
        assert 0 <= maze.grid[y][x] <= 15
        for wall, (dx, dy) in DELTA.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                assert maze.grid[y][x] & wall, (x, y, wall)
            else:
                here = bool(maze.grid[y][x] & wall)
                there = bool(maze.grid[ny][nx] & OPPOSITE[wall])
                assert here == there, (x, y, wall)


@ALL
def test_every_open_cell_is_reachable(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    assert set(distances(maze, entry)) == open_cells(maze)


@ALL
def test_pattern_cells_are_fully_closed(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    assert maze.has_pattern == bool(maze.pattern_cells)
    assert entry not in maze.pattern_cells
    assert exit_ not in maze.pattern_cells
    for x, y in maze.pattern_cells:
        assert maze.grid[y][x] == 15


@ALL
def test_perfect_is_a_tree_and_imperfect_has_loops(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    edges = sum(len(neighbours(maze, x, y))
                for y in range(h) for x in range(w)) // 2
    tree_edges = len(open_cells(maze)) - 1
    if perfect:
        assert edges == tree_edges
    else:
        assert edges > tree_edges


@ALL
def test_no_fully_open_3x3_area(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    g = maze.grid
    for y0, x0 in itertools.product(range(h - 2), range(w - 2)):
        inner_east = [g[y0 + dy][x0 + dx] & EAST
                      for dy in range(3) for dx in range(2)]
        inner_south = [g[y0 + dy][x0 + dx] & SOUTH
                       for dy in range(2) for dx in range(3)]
        assert any(inner_east) or any(inner_south), (x0, y0)


@ALL
def test_solve_returns_a_shortest_valid_path(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    path = maze.solve()
    x, y = entry
    for letter in path:
        wall = LETTER[letter]
        assert not maze.grid[y][x] & wall, (x, y, letter)
        dx, dy = DELTA[wall]
        x, y = x + dx, y + dy
    assert (x, y) == exit_
    assert len(path) == distances(maze, entry)[exit_]


@ALL
def test_to_rows_encodes_grid_as_hex(
    w: int, h: int, entry: Cell, exit_: Cell, perfect: bool, seed: int
) -> None:
    maze = build(w, h, entry, exit_, perfect, seed)
    rows = maze.to_rows()
    assert len(rows) == h
    for row, cells in zip(rows, maze.grid):
        assert [int(ch, 16) for ch in row] == cells


def test_same_seed_same_maze_even_on_regenerate() -> None:
    a = build(20, 15, (0, 0), (19, 14), False, 42)
    first = [row[:] for row in a.grid]
    a.generate()
    assert a.grid == first
    b = build(20, 15, (0, 0), (19, 14), False, 42)
    assert b.grid == first


def test_pattern_placed_when_it_fits_and_skipped_when_not() -> None:
    assert build(15, 15, (0, 0), (14, 14), True, 1).has_pattern
    small = build(6, 4, (0, 0), (5, 3), True, 1)
    assert not small.has_pattern
    assert small.pattern_cells == frozenset()


@pytest.mark.parametrize("w, h", [(1, 5), (5, 1), (0, 0), (-3, 4)])
def test_invalid_dimensions(w: int, h: int) -> None:
    with pytest.raises(InvalidDimensionError):
        MazeGenerator(w, h, (0, 0), (1, 1))


@pytest.mark.parametrize(
    "entry, exit_",
    [((0, 0), (0, 0)), ((-1, 0), (4, 4)), ((0, 0), (5, 4)),
     ((0, 5), (4, 4))],
)
def test_invalid_coordinates(entry: Cell, exit_: Cell) -> None:
    with pytest.raises(InvalidCoordinateError):
        MazeGenerator(5, 5, entry, exit_)


def test_solve_on_walled_off_grid_raises() -> None:
    maze = MazeGenerator(3, 3, (0, 0), (2, 2))
    maze.generate()
    for row in maze.grid:
        row[:] = [15] * len(row)
    with pytest.raises(NoSolutionError):
        maze.solve()
