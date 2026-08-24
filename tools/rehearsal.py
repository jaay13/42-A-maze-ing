"""End-to-end verification harness. Development tool, not part of the app.

Written by Claude (Anthropic), on Jason's instruction, as a testing
tool only. It lives in tools/ and nothing that ships imports it.

Runs two groups of checks: seven config sabotages that must each fail
cleanly with a controlled non-zero exit, then each PERFECT mode's
output file checked against an independent BFS, the rendered screen,
and maze_analyzer.py. Prints a PASS/WARN/FAIL report. FAIL means a
hard requirement is broken; WARN means our own convention is unmet
while the requirement still holds.

Usage:
    python3 tools/rehearsal.py [--strict]
"""

import os
import subprocess
import sys
import tempfile
from collections import deque
from typing import Callable, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(REPO_ROOT, "a_maze_ing.py")
SHIPPED_CONFIG = os.path.join(REPO_ROOT, "config.txt")
ANALYZER = os.path.join(REPO_ROOT, "tools", "maze_analyzer.py")

PROMPT = "Choice? (1-4): "
TRACEBACK_MARKER = "Traceback (most recent call last)"
TIMEOUT_SECONDS = 60

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

# Re-derived from subject SS IV.5 rather than imported from
# app.render, on purpose: this file is the second opinion.
WALL_BITS = {"N": 1, "E": 2, "S": 4, "W": 8}
MOVES = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}

# Group 3 runs every mode on several seeds. One seed proves that one
# maze is correct; it does not prove the generator is.
SEEDS = [42, 7, 1234]

BASE_CONFIG = [
    ("WIDTH", "15"),
    ("HEIGHT", "15"),
    ("ENTRY", "0,0"),
    ("EXIT", "14,14"),
    ("PERFECT", "true"),
    ("SEED", "42"),
]


class Tally:
    """Running count of check outcomes, and the worst one seen."""

    def __init__(self) -> None:
        self.passed = 0
        self.warned = 0
        self.failed = 0

    def add(self, state: str) -> str:
        """Record one outcome and return it unchanged."""
        if state == FAIL:
            self.failed += 1
        elif state == WARN:
            self.warned += 1
        else:
            self.passed += 1
        return state

    def verdict(self) -> str:
        """Return the worst state recorded so far."""
        if self.failed:
            return FAIL
        if self.warned:
            return WARN
        return PASS

    def line(self) -> str:
        """Return the one-line summary."""
        return (
            f"{self.verdict()}  {self.passed} pass  "
            f"{self.warned} warn  {self.failed} fail"
        )


class Run:
    """The four artefacts one run of the app leaves behind."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        code: int,
        output_file: Optional[str],
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.code = code
        self.output_file = output_file

    @property
    def combined(self) -> str:
        """Return stdout and stderr together, as a user would see it."""
        return self.stdout + self.stderr

    @property
    def message_lines(self) -> list[str]:
        """Return the non-blank lines the run printed."""
        return [ln for ln in self.combined.splitlines() if ln.strip()]

    @property
    def has_traceback(self) -> bool:
        """Report whether a Python traceback escaped."""
        return TRACEBACK_MARKER in self.combined


def run_app(config_path: str, stdin_text: str, workdir: str) -> Run:
    """Run a_maze_ing.py against one config and capture everything.

    Runs with cwd set to a temp directory so a config with a relative
    OUTPUT_FILE cannot write into the repo, and with the repo on
    PYTHONPATH so the app package still imports from there.

    Args:
        config_path: The config file to pass as the single argument.
        stdin_text: Keystrokes to feed the menu. An empty string is
            an immediate EOF.
        workdir: Directory to run in, and where a relative OUTPUT_FILE
            would land.

    Returns:
        The run's stdout, stderr and exit code. output_file is unset;
        callers that care fill it in.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, APP, config_path],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=workdir,
        env=env,
        timeout=TIMEOUT_SECONDS,
    )
    return Run(proc.stdout, proc.stderr, proc.returncode, None)


def drop_key(key: str) -> Callable[[list[tuple[str, str]]], None]:
    """Return a mutator that deletes one key from a config."""
    def mutate(pairs: list[tuple[str, str]]) -> None:
        for index, (name, _) in enumerate(pairs):
            if name == key:
                del pairs[index]
                return
    return mutate


def set_key(key: str, value: str) -> Callable[[list[tuple[str, str]]], None]:
    """Return a mutator that replaces one key's value."""
    def mutate(pairs: list[tuple[str, str]]) -> None:
        for index, (name, _) in enumerate(pairs):
            if name == key:
                pairs[index] = (name, value)
                return
    return mutate


def add_line(text: str) -> Callable[[list[tuple[str, str]]], None]:
    """Return a mutator that appends a raw line with no '=' in it."""
    def mutate(pairs: list[tuple[str, str]]) -> None:
        pairs.append((text, ""))
    return mutate


def render_pairs(pairs: list[tuple[str, str]]) -> list[str]:
    """Render pairs to lines, keeping bare lines bare."""
    return [k if v == "" and "=" not in k else f"{k}={v}" for k, v in pairs]


SABOTAGES: list[tuple[str, Callable[[list[tuple[str, str]]], None], str]] = [
    ("mandatory key removed", drop_key("WIDTH"), "WIDTH"),
    ("line without '='", add_line("WIDTHIS15"), "WIDTHIS15"),
    ("numbers -> letters", set_key("WIDTH", "abc"), "WIDTH"),
    ("bad boolean PERFECT", set_key("PERFECT", "maybe"), "PERFECT"),
    ("malformed ENTRY tuple", set_key("ENTRY", "0,0,0"), "ENTRY"),
    ("ENTRY out of bounds", set_key("ENTRY", "-1,0"), "ENTRY"),
    ("WIDTH=0", set_key("WIDTH", "0"), "WIDTH"),
]


def run_group1(tally: Tally) -> None:
    """Run the seven sabotages and print the error table.

    Each case asserts four things. Two are hard requirements (no
    uncontrolled termination, a controlled non-zero exit) and are
    FAIL. Three are our own conventions -- one line of output, a
    [CATEGORY] prefix, the offending key named -- and are WARN.

    Sabotages are generated at runtime rather than committed as
    fixture files, so they cannot go stale when a config key changes.
    The generator is guarded: a mutation that silently did nothing
    would otherwise produce a valid config and a confusing pass.

    Args:
        tally: Accumulator for the run's outcomes, updated in place.
    """
    print("SCALE: Configuration file > Error Management")
    print('  "Edit the configuration file to ensure that the program')
    print('   correctly handles its errors."')
    print()
    print(
        "  case                     exit  lines  traceback  "
        "outfile  message"
    )

    base_text = "\n".join(render_pairs(BASE_CONFIG))
    notes: list[str] = []

    for name, mutate, expect in SABOTAGES:
        with tempfile.TemporaryDirectory() as workdir:
            out_path = os.path.join(workdir, "maze.txt")
            pairs = list(BASE_CONFIG)
            mutate(pairs)
            if "\n".join(render_pairs(pairs)) == base_text:
                print(f"  {name:<24} HARNESS BUG: mutation did nothing")
                tally.add(FAIL)
                continue
            config_path = os.path.join(workdir, "config.txt")
            text = "\n".join(render_pairs(pairs))
            text += f"\nOUTPUT_FILE={out_path}\n"
            with open(config_path, "w") as handle:
                handle.write(text)

            run = run_app(config_path, "", workdir)
            wrote = os.path.exists(out_path)

        first = run.message_lines[0] if run.message_lines else ""
        count = len(run.message_lines)

        state = PASS
        detail: list[str] = []
        if run.has_traceback:
            state = FAIL
            detail.append("SCALE HARD ZERO: a traceback reached the "
                          "terminal")
            detail.append("    " + first)
        elif run.code != 1:
            state = FAIL
            detail.append(f"expected exit 1, got {run.code}")
            if wrote:
                detail.append("an output file was written for a config "
                              "that should have been rejected")
        else:
            if count != 1:
                state = WARN
                detail.append(f"expected 1 line of output, got {count}")
            if not first.startswith("["):
                state = WARN
                detail.append("message carries no [CATEGORY] prefix")
                detail.append("    got: " + first)
            elif expect.lower() not in run.combined.lower():
                state = WARN
                detail.append(f"message does not name {expect!r}")
                detail.append("    got: " + first)
            if wrote:
                state = WARN
                detail.append("an output file was written for a "
                              "rejected config")

        shown = "ok" if state == PASS else state
        note = f'  ("{expect}")' if state == PASS else ""
        print(
            f"  {name:<24}{run.code:>4}{count:>7}"
            f"{'YES' if run.has_traceback else 'no':>11}"
            f"{'WRITTEN' if wrote else 'absent':>9}  {shown}{note}"
        )
        for entry in detail:
            notes.append(f"      {name}: {entry}")
        tally.add(state)

    with tempfile.TemporaryDirectory() as workdir:
        run = run_app(SHIPPED_CONFIG, "4\n", workdir)
        smoke = PASS if run.code == 0 and not run.has_traceback else FAIL
        print(
            f"  {'shipped config.txt':<24}{run.code:>4}"
            f"{'-':>7}{'YES' if run.has_traceback else 'no':>11}"
            f"{'-':>9}  {'ok' if smoke == PASS else smoke}  (smoke)"
        )
        if smoke == FAIL:
            notes.append(
                "      shipped config.txt: the committed config does "
                "not run cleanly"
            )
        tally.add(smoke)

    for note in notes:
        print(note)


def parse_output_file(
    text: str,
) -> tuple[list[list[int]], tuple[int, int], tuple[int, int], list[str]]:
    """Split an output file into grid, entry, exit and path.

    Decodes the hex wall digits here rather than importing
    app.render.is_closed, so a wrong wall encoding cannot pass both
    the renderer and its checker for the same reason.

    Args:
        text: The whole output file, as written by app.output.

    Returns:
        The grid as grid[y][x] wall values, the entry cell, the exit
        cell, and the path as direction letters.

    Raises:
        ValueError: If the layout is not rows, blank line, three
            footer lines.
    """
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if "" not in lines:
        raise ValueError("no blank line separating grid from footer")
    blank = lines.index("")
    rows = lines[:blank]
    footer = lines[blank + 1:]
    if len(footer) != 3:
        raise ValueError(f"expected 3 footer lines, found {len(footer)}")
    if not rows:
        raise ValueError("no grid rows")

    grid = [[int(char, 16) for char in row] for row in rows]

    def coordinate(raw: str) -> tuple[int, int]:
        parts = raw.split(",")
        if len(parts) != 2:
            raise ValueError(f"malformed coordinate {raw!r}")
        return (int(parts[0]), int(parts[1]))

    return grid, coordinate(footer[0]), coordinate(footer[1]), \
        footer[2].split()


def is_open(grid: list[list[int]], cell: tuple[int, int], side: str) -> bool:
    """Report whether a cell's wall is open on one side."""
    x, y = cell
    return not grid[y][x] & WALL_BITS[side]


def walk(
    grid: list[list[int]],
    entry: tuple[int, int],
    path: list[str],
) -> tuple[list[tuple[int, int]], Optional[str]]:
    """Replay a path from entry, checking every step is legal.

    Args:
        grid: The maze, grid[y][x].
        entry: Where the walk starts.
        path: Direction letters to follow.

    Returns:
        The cells visited (entry included) and a problem description,
        or None if the whole walk was legal.
    """
    height = len(grid)
    width = len(grid[0])
    cell = entry
    cells = [entry]
    seen = {entry}
    for step, letter in enumerate(path):
        if letter not in MOVES:
            return cells, f"step {step}: {letter!r} is not a direction"
        if not is_open(grid, cell, letter):
            return cells, (
                f"step {step}: moving {letter} from {cell} crosses a "
                "closed wall"
            )
        dx, dy = MOVES[letter]
        cell = (cell[0] + dx, cell[1] + dy)
        if not (0 <= cell[0] < width and 0 <= cell[1] < height):
            return cells, f"step {step}: leaves the grid at {cell}"
        if cell in seen:
            return cells, f"step {step}: revisits {cell}"
        seen.add(cell)
        cells.append(cell)
    return cells, None


def bfs_length(
    grid: list[list[int]],
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
) -> Optional[int]:
    """Return the shortest number of steps from entry to exit.

    An independent breadth-first search, deliberately not the engine's
    and not the renderer's: its whole purpose is to disagree when the
    file's path is not shortest.

    Args:
        grid: The maze, grid[y][x].
        entry: Start cell.
        exit_cell: Target cell.

    Returns:
        The step count, or None if the exit is unreachable.
    """
    height = len(grid)
    width = len(grid[0])
    queue = deque([(entry, 0)])
    seen = {entry}
    while queue:
        cell, distance = queue.popleft()
        if cell == exit_cell:
            return distance
        for side, (dx, dy) in MOVES.items():
            if not is_open(grid, cell, side):
                continue
            nxt = (cell[0] + dx, cell[1] + dy)
            if not (0 <= nxt[0] < width and 0 <= nxt[1] < height):
                continue
            if nxt in seen:
                continue
            seen.add(nxt)
            queue.append((nxt, distance + 1))
    return None


def last_render(stdout: str, width: int, height: int) -> Optional[list[str]]:
    """Pull the final ASCII maze out of captured stdout.

    input() writes its prompt without a trailing newline and piped
    input is not echoed, so the first line of every redraw arrives
    glued to 'Choice? (1-4): '. That prefix is stripped before the
    canvas is located, or the search would never match.

    Args:
        stdout: Everything the run printed.
        width: Maze width in cells.
        height: Maze height in cells.

    Returns:
        The canvas rows of the last maze drawn, or None if no canvas
        of the expected size is present.
    """
    canvas_width = 4 * width + 1
    canvas_height = 2 * height + 1
    lines = []
    for raw in stdout.splitlines():
        index = raw.find(PROMPT)
        if index != -1:
            raw = raw[index + len(PROMPT):]
        lines.append(raw)

    for start in range(len(lines) - canvas_height, -1, -1):
        block = lines[start:start + canvas_height]
        if block[0].startswith("+") and all(
            len(line) == canvas_width for line in block
        ):
            return block
    return None


def star_cells(
    block: list[str],
    width: int,
    height: int,
) -> set[tuple[int, int]]:
    """Return the cells drawn as '*' on a rendered canvas.

    Cell (x, y)'s interior sits at row 2*y+1, column 4*x+2, matching
    the layout app.render.draw_walls builds.
    """
    found = set()
    for y in range(height):
        for x in range(width):
            if block[2 * y + 1][4 * x + 2] == "*":
                found.add((x, y))
    return found


def run_analyzer(
    output_file: str,
    max_dead_ends: Optional[int] = None,
) -> tuple[str, str]:
    """Run tools/maze_analyzer.py and return its verdict and coherence.

    The analyzer's exit code is not a pass/fail signal: main() returns
    EXIT_OK whenever the file merely *parses*, so a
    'Not Pac-Man-ready' verdict still exits 0. Only the verdict text
    can be trusted, which is why this returns strings rather than a
    boolean.

    Args:
        output_file: The maze file to analyze.
        max_dead_ends: Passed as --max-dead-ends when given. Zero is
            the subject's no-dead-end bonus threshold.

    Returns:
        The text after 'Verdict: ', and the 'Wall coherence' value.
        Either is an explanatory string if the analyzer did not
        produce that line.
    """
    argv = [sys.executable, ANALYZER, output_file]
    if max_dead_ends is not None:
        argv += ["--max-dead-ends", str(max_dead_ends)]
    proc = subprocess.run(
        argv, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
    )
    verdict = "analyzer printed no verdict"
    coherence = "analyzer printed no coherence line"
    for line in proc.stdout.splitlines():
        if line.startswith("Verdict:"):
            verdict = line[len("Verdict:"):].strip()
        elif line.startswith("Wall coherence"):
            coherence = line.split(":", 1)[1].strip()
    return verdict, coherence


def check(label: str, state: str, note: str = "") -> None:
    """Print one dotted check line."""
    dots = "." * max(3, 56 - len(label))
    shown = "ok" if state == PASS else state
    print(f"    {label} {dots} {shown}  {note}".rstrip())


def run_group3_mode(tally: Tally, perfect: bool, seed: int) -> None:
    """Check one PERFECT mode's path against the file and the screen.

    Sends '2' to reveal the path -- it starts hidden -- then '4' to
    quit, and reads the last canvas printed.

    Args:
        tally: Accumulator, updated in place.
        perfect: Which PERFECT mode to generate.
        seed: SEED value for this run, so a failure is reproducible
            by hand from the printed header.
    """
    pairs = list(BASE_CONFIG)
    set_key("PERFECT", "true" if perfect else "false")(pairs)
    set_key("SEED", str(seed))(pairs)
    width = int(dict(pairs)["WIDTH"])
    height = int(dict(pairs)["HEIGHT"])
    label = "true " if perfect else "false"
    print(f"  PERFECT={label}   {width}x{height}  seed {seed}")

    with tempfile.TemporaryDirectory() as workdir:
        out_path = os.path.join(workdir, "maze.txt")
        config_path = os.path.join(workdir, "config.txt")
        text = "\n".join(render_pairs(pairs))
        text += f"\nOUTPUT_FILE={out_path}\n"
        with open(config_path, "w") as handle:
            handle.write(text)

        run = run_app(config_path, "2\n4\n", workdir)
        if run.code != 0 or run.has_traceback or not os.path.exists(
            out_path
        ):
            check("run produced an output file", tally.add(FAIL))
            first = run.message_lines[0] if run.message_lines else ""
            print(f"      exit {run.code}: {first}")
            print()
            return
        with open(out_path) as handle:
            file_text = handle.read()
        verdict, coherence = run_analyzer(out_path)
        braided = (
            run_analyzer(out_path, max_dead_ends=0)[0]
            if not perfect else ""
        )

    try:
        grid, entry, exit_cell, path = parse_output_file(file_text)
    except ValueError as error:
        check("output file parses", tally.add(FAIL), str(error))
        print()
        return

    if (entry, exit_cell) != ((0, 0), (14, 14)):
        check(
            "entry/exit in file match the config",
            tally.add(FAIL),
            f"{entry} {exit_cell}",
        )
    else:
        check("entry/exit in file match the config", tally.add(PASS))

    cells, problem = walk(grid, entry, path)
    if problem is None:
        check(
            "path walkable (crosses no closed wall)",
            tally.add(PASS),
            f"{len(path)} steps",
        )
    else:
        check("path walkable (crosses no closed wall)", tally.add(FAIL))
        print(f"      {problem}")

    if problem is None and cells[-1] == exit_cell:
        check("path ends on EXIT, no cell revisited", tally.add(PASS))
    else:
        check("path ends on EXIT, no cell revisited", tally.add(FAIL))
        print(f"      path ends at {cells[-1]}, exit is {exit_cell}")

    shortest = bfs_length(grid, entry, exit_cell)
    if shortest is None:
        check("length == independent BFS", tally.add(FAIL))
        print("      the exit is not reachable from the entry at all")
    elif shortest == len(path):
        check(
            "length == independent BFS",
            tally.add(PASS),
            f"{len(path)} == {shortest}",
        )
    else:
        check(
            "length == independent BFS",
            tally.add(FAIL),
            f"{len(path)} vs {shortest}",
        )
        print(f"      file path : {' '.join(path)}")
        print("      -> reaches the exit but is not the shortest path.")
        print('      SCALE: "the shortest valid path from entry to exit".')

    block = last_render(run.stdout, width, height)
    if block is None:
        check("'*' on screen == cells path visits", tally.add(FAIL))
        print("      no canvas of the expected size found in stdout")
    else:
        drawn = star_cells(block, width, height)
        expected = set(cells) - {entry, exit_cell}
        if drawn == expected:
            check(
                "'*' on screen == cells path visits",
                tally.add(PASS),
                f"{len(drawn)} cells",
            )
        else:
            check("'*' on screen == cells path visits", tally.add(FAIL))
            print(f"      on screen but not on the file's path: "
                  f"{sorted(drawn - expected)[:6]}")
            print(f"      on the file's path but not on screen: "
                  f"{sorted(expected - drawn)[:6]}")

    wanted = "PERFECT maze" if perfect else "Pac-Man-USABLE"
    if verdict.startswith(wanted):
        check(
            f"maze_analyzer verdict is {wanted}",
            tally.add(PASS),
        )
    else:
        check(f"maze_analyzer verdict is {wanted}", tally.add(FAIL))
        print(f"      {verdict}")

    if coherence.startswith("OK"):
        check("maze_analyzer wall coherence", tally.add(PASS), coherence)
    else:
        check("maze_analyzer wall coherence", tally.add(FAIL), coherence)

    if braided:
        state = "yes" if braided.startswith("Pac-Man-USABLE") else "no"
        print(f"    (bonus, not graded here: --max-dead-ends 0 -> "
              f"{state})")
    print()


def run_group3(tally: Tally) -> None:
    """Run the path audit for both PERFECT modes, on several seeds."""
    print("SCALE: Output file > Format")
    print('  "Control that the shortest path sequence in the output')
    print('   file matches the visual representation."')
    print('  "Generate one maze with each value of PERFECT and run the')
    print('   analysis script on each output file."')
    print()
    for perfect in (True, False):
        for seed in SEEDS:
            run_group3_mode(tally, perfect, seed)


def main(argv: list[str]) -> int:
    """Run both groups and return the process exit code."""
    strict = "--strict" in argv
    print()
    print("A-Maze-ing verification harness")
    print(f"repo {REPO_ROOT}")
    print()

    group1 = Tally()
    run_group1(group1)
    print()
    print(f"  {group1.line()}")
    print()

    group3 = Tally()
    run_group3(group3)
    print(f"  {group3.line()}")
    print()

    total = Tally()
    total.passed = group1.passed + group3.passed
    total.warned = group1.warned + group3.warned
    total.failed = group1.failed + group3.failed
    print("=" * 70)
    print(f"RESULT: {total.line()}")
    print("=" * 70)
    print()

    if total.failed:
        return 1
    if strict and total.warned:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
