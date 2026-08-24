# Interface — Frozen Contract

## What this file is

This is the API boundary between the **engine** (`src/mazegen/**`, owned by A) and the **application** (`a_maze_ing.py` + `app/**`, owned by B). It defines exactly how the app talks to the engine: the `MazeGenerator` class B instantiates, and the exceptions B is guaranteed to catch.

**"Frozen"** means: once both of you agree on it, neither person changes it unilaterally. If a change is needed — a new method, a different return type, an extra parameter — message the other person *before* pushing. A silent change on one side breaks the other side's code without warning, since each of you is building against this file, not against the other person's actual implementation.

This is also why `src/mazegen/generator.py` currently contains a **stub**: a fake `MazeGenerator` that returns a hardcoded 5×5 grid instead of running a real algorithm. It satisfies this exact contract, so B can build and test the whole application layer today, before A has written a single line of real maze-generation logic. When A's real implementation lands, it drops in as a straight replacement — B's code doesn't need to change, because both honor the same interface below.

Frozen day 0. Changing this contract requires a message to the other person before you push. Everything else is yours to refactor freely.

## Engine surface

```python
# Wall encoding — matches the output file spec exactly.
# bit 0 = N (1), bit 1 = E (2), bit 2 = S (4), bit 3 = W (8)
# Bit SET = wall CLOSED.

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
    ) -> None: ...

    def generate(self) -> None: ...

    @property
    def grid(self) -> list[list[int]]: ...        # grid[y][x] -> 0..15

    @property
    def pattern_cells(self) -> frozenset[tuple[int, int]]: ...   # the "42" cells

    @property
    def has_pattern(self) -> bool: ...            # False if maze too small

    def solve(self) -> list[str]: ...             # ["E", "S", "E", ...]

    def to_rows(self) -> list[str]: ...           # HEIGHT strings of WIDTH hex chars
```

## Errors (`mazegen/errors.py`)

```python
class MazegenError(Exception): ...
class InvalidDimensionError(MazegenError): ...
class InvalidCoordinateError(MazegenError): ...
class ImpossibleMazeError(MazegenError): ...
class NoSolutionError(MazegenError): ...
```

## Two contract rules that are non-negotiable

- **The app never reimplements BFS.** The path written to the output file and the path drawn on screen both come from the same `solve()` call. Any cross-check of the file's path string against the visual is therefore free — there is only one source of truth.
- **Every exception the app can see is a `MazegenError` subclass.** The app catches `MazegenError` at the top level and prints a clean message. Nothing else may escape: a raw traceback reaching the user is treated as a hard failure.
