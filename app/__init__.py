"""Application layer for A-Maze-ing (Person B).

Holds everything outside the reusable mazegen engine: configuration
parsing, output file writing, and rendering.

This file marks `app` as a regular package rather than a PEP 420
namespace package. Imports work either way, but without it mypy cannot
tell whether `app/config.py` is the module `config` or `app.config`,
and fails with "Source file found twice under different module names"
before checking anything.

Being a package is not the same as being distributable: `app` is
imported, never shipped. Only `src/mazegen` is built into the wheel,
per `[tool.setuptools.packages.find] where = ["src"]` in pyproject.toml.
"""
