# readme_app.md — application layer (Person B)

Fragment for the final `README.md`, assembled at CP5 together with A's
`readme_engine.md`. Headings match the subject's required sections.

> **Note:** the `lint` / `lint-strict` targets and `requirements-dev.txt`
> described below arrive with B7 (PR #15). Remove this note once it is
> merged.

---

*This project has been created as part of the 42 curriculum by jakoch, jhimmero.*

## Contents

- [Description](#description)
- [Instructions](#instructions)
  - [Menu](#menu)
- [Example output](#example-output)
  - [Default board, colour blocks (`PERFECT=false`)](#default-board-colour-blocks-perfectfalse)
  - [Perfect maze, path revealed (`PERFECT=true`)](#perfect-maze-path-revealed-perfecttrue)
  - [ASCII renderer (`RENDERER=ascii`)](#ascii-renderer-rendererascii)
  - [ASCII with the path revealed](#ascii-with-the-path-revealed)
- [Configuration file](#configuration-file)
  - [Mandatory keys](#mandatory-keys)
  - [Optional keys](#optional-keys)
  - [Unknown keys are rejected](#unknown-keys-are-rejected)
  - [Example](#example)
- [Output file](#output-file)
- [Error handling](#error-handling)
- [Resources](#resources)
  - [How AI was used](#how-ai-was-used)
- [Still to settle before CP5](#still-to-settle-before-cp5)

## Description

A-Maze-ing generates a random maze, solves it, displays it in the
terminal and writes it to a file. It is split in two: a reusable,
pip-installable generator package (`mazegen`) and an application layer
(`a_maze_ing.py` + `app/`) that reads the configuration, renders the
result and drives the menu.

The maze is either *perfect* (exactly one route between any two cells)
or a *Pac-Man board* (fully connected, several independent routes, few
or no dead-ends). A "42" is drawn into the maze with fully closed
cells.

## Instructions

Requires Python 3.10 or newer. A virtual environment is recommended.

```
python3 -m venv .venv && source .venv/bin/activate
make install                 # installs mazegen (editable) + dev tools
make run                     # python3 a_maze_ing.py config.txt
```

The program takes exactly one argument, the config file:

```
python3 a_maze_ing.py config.txt
```

Other targets:

| Target | Does |
|---|---|
| `make install` | `pip install -e .` plus `requirements-dev.txt` |
| `make run` | runs against `config.txt` |
| `make debug` | the same, under `pdb` |
| `make clean` | removes `__pycache__`, `build`, `dist`, `.mypy_cache` |
| `make lint` | `flake8 .` and `mypy .` with the subject's flags |
| `make lint-strict` | `flake8 .` and `mypy . --strict` |

`requirements-dev.txt` pins flake8 and mypy exactly, so a fresh clone
lints with the same versions rather than whatever is newest.

### Menu

| Key | Action |
|---|---|
| 1 | generate a new maze |
| 2 | show / hide the shortest path |
| 3 | change the wall colour |
| 4 | quit |

The path starts hidden. Any other input prints a short hint and asks
again. Ctrl-D and Ctrl-C both quit cleanly.

## Example output

Four runs of the same program. The `config.txt` behind each picture is
printed above it, so the settings that produced it are visible rather than
implied.

### Default board, colour blocks (`PERFECT=false`)

The default mode, and what a terminal shows: fully connected, several
independent routes and no dead-ends, so the board is directly usable by a
Pac-Man-style game. The grey cells are the "42" — fully closed, and the
only cells allowed to be unreachable. Magenta marks the entry, red the
exit.

```
WIDTH=15
HEIGHT=15
ENTRY=0,0
EXIT=14,14
OUTPUT_FILE=maze.txt
PERFECT=false
SEED=42
```

![Default board rendered as colour blocks](img/default_board_false.png)

### Perfect maze, path revealed (`PERFECT=true`)

With `PERFECT=true` there is exactly one route between any two cells and
no loops at all, so the shortest path is the only path — which is why it
winds through nearly the whole maze. Revealed with menu key `2`; it starts
hidden.

```
WIDTH=15
HEIGHT=15
ENTRY=0,0
EXIT=14,14
OUTPUT_FILE=maze.txt
PERFECT=true
SEED=42
```

![Perfect maze with the solution path shown](img/default_board_2_true_full.png)

### ASCII renderer (`RENDERER=ascii`)

`S` is the entry, `E` the exit, and `#` the cells forming the "42". Walls
are drawn as `+`, `-` and `|`.

This is also what redirected or piped output looks like, minus the colour:
when stdout is not a terminal the program falls back to ASCII and emits no
escape sequences at all, whatever `RENDERER` says.

```
WIDTH=15
HEIGHT=15
ENTRY=0,0
EXIT=14,14
OUTPUT_FILE=maze.txt
PERFECT=false
SEED=42
RENDERER=ascii
```

![Board rendered as ASCII, path hidden](img/ascii_board_false.png)

### ASCII with the path revealed

The same run after pressing `2`. The shortest path from `S` to `E` is
drawn as `*`, and it is the same path written to the output file — both
come from a single call to the engine's solver, so they cannot disagree.

![ASCII board with the solution path shown](img/ascii_board_2_false.png)

**A maze smaller than 12x12 cannot fit the "42".** In that case it is left
out and a `[PATTERN_ERROR]` notice is printed on stderr, as the subject
allows; the program continues normally.

## Configuration file

One `KEY=VALUE` per line. Blank lines and lines starting with `#` are
ignored, surrounding spaces are stripped, and key names are
case-insensitive (`width=15` works). Values are not: paths keep their
case.

### Mandatory keys

| Key | Format | Example | Meaning |
|---|---|---|---|
| `WIDTH` | integer | `15` | maze width in cells |
| `HEIGHT` | integer | `15` | maze height in cells |
| `ENTRY` | `x,y` | `0,0` | entry cell |
| `EXIT` | `x,y` | `14,14` | exit cell |
| `OUTPUT_FILE` | path | `maze.txt` | where the maze is written |
| `PERFECT` | `true` / `false`, case-insensitive | `false` | perfect maze, or Pac-Man board |

### Optional keys

| Key | Format | Default | Meaning |
|---|---|---|---|
| `SEED` | integer | none (random) | same seed, same maze |
| `RENDERER` | `blocks` / `ascii` | `blocks` | preferred display style |

`RENDERER` is a preference, not a guarantee. Coloured blocks are used
only when stdout is a terminal, `NO_COLOR` is unset and `TERM` is not
`dumb`; otherwise the output is plain ASCII with no escape sequences,
so redirecting to a file always produces something readable.

### Unknown keys are rejected

A key that is neither mandatory nor optional is an error, not a
warning. A typo in an optional key would otherwise be invisible —
`SED=42` would silently run with a random seed while looking
reproducible. The cost is that adding a key means registering it in
`app/config.py`.

### Example

```
WIDTH=15
HEIGHT=15
ENTRY=0,0
EXIT=14,14
OUTPUT_FILE=maze.txt
PERFECT=false
# SEED=42
# RENDERER=ascii
```

## Output file

`HEIGHT` lines of `WIDTH` hexadecimal digits, one digit per cell,
encoding that cell's walls (bit 0 = North, 1 = East, 2 = South,
3 = West; a set bit means the wall is closed). Then a blank line, then
three lines: the entry as `x,y`, the exit as `x,y`, and the shortest
path as direction letters **separated by single spaces**, e.g.
`E E S E S S`. Every line ends with `\n`.

The file always describes the maze currently generated. Hiding the
path on screen does not remove it from the file — the subject requires
it to be there.

## Error handling

Every message that stops the program is a single line on stderr with a
category prefix, and the exit code is 1. No traceback ever reaches the
terminal.

| Prefix | Cause |
|---|---|
| `[USAGE_ERROR]` | wrong number of arguments |
| `[CONFIG_ERROR]` | config missing, unreadable, malformed or invalid |
| `[MAZE_ERROR]` | the generator rejected the parameters or failed |
| `[OUTPUT_ERROR]` | the output file could not be written |
| `[RENDER_ERROR]` | the engine returned data that cannot be drawn |
| `[INTERNAL_ERROR]` | last-resort backstop; a bug, not user input |

Two deliberate exceptions:

- `[PATTERN_ERROR]` — the maze is too small for the "42". The subject
  allows omitting it as long as a message is printed, so this goes to
  stderr and the program continues with exit code 0. It is a notice,
  not a failure.
- An unrecognised menu key prints a plain hint on stdout, with no
  prefix and no error exit. It is interactive feedback rather than a
  fault, and prefixing it would dilute the convention.

## Resources

- Subject and `maze_analyzer.py`, 42 intra.
- Python documentation
- <https://no-color.org/> — the `NO_COLOR` convention.
- ANSI 256-colour codes, for the wall palette.

### How AI was used

- **`not_for_submission/b8_rehearsal.py` was written by Claude
  (Anthropic)** and is the only file in the repository authored by AI.
  It is a test harness: it replays the evaluation scale's config
  sabotages and checks the output file's solution path against an
  independent breadth-first search and against the rendered maze. It is
  not submitted, nothing that ships imports it, and its module
  docstring states this.
- Claude was also used for review and explanation of the application
  layer — arguing through design decisions, reproducing failures and
  checking output — but did not write the submitted source.

## Still to settle before CP5

- **Image paths.** They are `img/...`, relative to this file, so they
  render here and on GitHub. When this fragment is merged into
  `README.md` at the repo root, prefix them with `docs/`.
- A's fragment: chosen algorithm, why it was chosen, and the
  reusable-module documentation.
- Joint sections: team roles, planning and how it evolved, what worked
  well and what could be improved, tools used.
- If B10 lands, add its config key and its menu entry to the tables
  above.
