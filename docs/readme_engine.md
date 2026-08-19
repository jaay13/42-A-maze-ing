# readme_engine.md: maze generator (Person A)

Fragment for the final `README.md`, assembled at CP5 together with B's
`readme_app.md`.

---

## Chosen algorithm (and why)

The generator uses **recursive backtracking**, but with an explicit
stack rather than real Python recursion.

How it builds a maze, in plain language:

1. You stand in a cell. Every wall is closed.
2. You look at the neighbours you have never visited.
3. You pick one at random, knock down the wall between you, and walk
   into it.
4. Dead end? You step back along the notes you kept (the stack) and
   try a different neighbour.
5. Repeat until every cell has been visited.

That is A3. After this pass the maze is *perfect*: exactly one path
between any two cells, no loops.

Why this algorithm, and why a stack:

- A perfect maze falls out of the method itself. You do not have to
  repair loops afterwards.
- Defence can ask for 200x200. Real recursion would hit
  `RecursionError`. A list used as a stack does not.
- With a `seed`, the random choices are replayable, so the same config
  always rebuilds the same maze.

Pac-Man mode (`PERFECT=false`, the default) starts from that same
perfect maze and then *braids* it: extra walls come down at dead ends,
and the four corners plus the centre are forced open. That is A6. The
subject wants several independent routes, not "a perfect maze with one
wall missing".

**Videos, if you want to see it move:**

- Building (recursive backtracker, live animation):
  https://www.youtube.com/watch?v=KWeeTMwFA9Y
- The article most explanations copy from (pictures, very readable):
  https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking
- Same idea as text / pseudocode:
  https://en.wikipedia.org/wiki/Maze_generation_algorithm#Recursive_backtracker
- Solving (BFS, shortest path):
  https://www.youtube.com/watch?v=xlVX7dXLS64
  https://www.youtube.com/watch?v=5MwMPklN6PA

---

## How the engine is put together

Nothing here is a second algorithm. It is the same generator, built in
layers so each rule has one place to live.

| Step | What it actually does | Builds a maze? | Solves a maze? |
| --- | --- | --- | --- |
| A1 | Empty module + error types + a fake 5x5 so the app could start | No (stub) | No |
| A2 | Grid of closed cells, `_open_wall`, hex dump (`to_rows`) | No (tools only) | No |
| A3 | Recursive backtracker on an explicit stack | **Yes** | No |
| A4 | BFS from entry to exit | No | **Yes** (shortest path) |
| A5 | Stamp a "42" of fully closed cells *before* A3 runs | Only those cells stay sealed | No |
| A6 | If not perfect: braid dead ends, open corners + centre | Extra openings | No |
| A7 | Before any extra opening, refuse it if it would make a 3x3 hall | Constraint | No |
| A8 | Reject impossible sizes and coordinates | No | No |

**A2, the tool that keeps walls honest.** A cell is a number 0..15.
Bit 0 = North, 1 = East, 2 = South, 3 = West. A *set* bit means that
wall is closed. When `_open_wall` knocks down the east wall of cell A,
it also knocks down the west wall of cell B. One function, both sides.
The outer border has no neighbour, so those walls stay closed.

**A4, the solver.** BFS, not DFS. Waves spread from the entry. The
first time a wave hits the exit, that route is the shortest. Result is
a list of letters like `["E", "E", "S"]`. The app must call this once
and use it for both the file and the screen, so the two cannot disagree.

**A5, the "42".** A 7x5 stamp of fully closed cells, placed as close as
possible to the middle of the maze. It must not sit on the entry, the
exit, a corner, or *every* centre cell (Pac-Man needs at least one
centre cell as a corridor). If the maze is too small to fit that
without breaking those rules, the pattern is simply left out and
`has_pattern` is `False`. The engine does not print. The app prints
`[PATTERN_ERROR]` in that case.

**A7, the 3x3 rule.** Corridors may be 2 cells wide. A 3x3 block of
open cells is forbidden. The check runs *before* a wall is opened, not
as a cleanup pass: try the opening, look at every 3x3 window that
touches that cell, restore the wall if any window would be fully open.

The engine never prints. Bad input raises a `MazegenError` subclass.
The app catches that and turns it into one line on stderr.

---

## Reusable module

`mazegen` is a normal pip package. The class you import is
`MazeGenerator`. Internals do not have to look like the output file.
`to_rows()` and `solve()` are what you write to disk.

### Install

From this repo, after a rebuild:

```
pip install mazegen-1.0.0-py3-none-any.whl
```

Or during development:

```
pip install -e .
```

### Instantiate and generate

```python
from mazegen import MazeGenerator

maze = MazeGenerator(
    width=15,
    height=15,
    entry=(0, 0),
    exit=(14, 14),
    perfect=False,
    seed=42,
)
maze.generate()
```

### Parameters

| Parameter | Meaning |
| --- | --- |
| `width`, `height` | Size in cells. Both must be at least 2. |
| `entry`, `exit` | `(x, y)` with `(0, 0)` in the top-left. Must differ, must sit inside the grid. |
| `perfect` | `True`: one path, no loops. `False` (default): Pac-Man board, several routes. |
| `seed` | Optional int. Same seed, same maze. `None` means a fresh maze each call. |
| `algorithm` | Reserved. Currently only `"backtracker"`. |

### Structure and solution

```python
# Hex rows, one character per cell (the output-file encoding).
rows = maze.to_rows()

# Same data as integers 0..15. grid[y][x].
cell = maze.grid[0][0]

# Shortest path as direction letters.
path = maze.solve()          # e.g. ["E", "S", "E"]

# The "42" cells, or empty if the maze was too small.
maze.has_pattern             # bool
maze.pattern_cells           # frozenset of (x, y)
```

If the maze is 5x5, `generate()` still succeeds, but `has_pattern` is
`False` and `pattern_cells` is empty. That is allowed. Do not treat it
as a crash.

### Errors (all subclass `MazegenError`)

| Exception | Typical cause |
| --- | --- |
| `InvalidDimensionError` | width or height below 2 |
| `InvalidCoordinateError` | entry equals exit, or a coordinate outside the grid |
| `NoSolutionError` | `solve()` could not reach the exit (should not happen after a successful `generate`) |
| `ImpossibleMazeError` | reserved for a maze that cannot be built |

Catch `MazegenError` if you only care that the engine refused. Catch
the subclass if you want to tell the kinds apart.

### Why MIT

`LICENSE.md` is the MIT license. The later Pac-Man project has to reuse
and redistribute this generator. MIT says that in one page, without
copyleft. The full eval answers (3x3, 42, PERFECT vs Pac-Man, two-venv
rebuild) live in the root `README.md` under "Maze generation (eval
answers)" and "Rebuild the package".
