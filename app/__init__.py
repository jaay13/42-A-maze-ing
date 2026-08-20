"""Application layer for A-Maze-ing (Person B).

Holds everything outside the reusable mazegen engine: configuration
parsing, output file writing, and rendering. Only src/mazegen is built
into the wheel -- app is imported, never shipped.

Being a regular package rather than a PEP 420 namespace package is
required by mypy, which otherwise cannot tell whether app/config.py is
the module `config` or `app.config`.
"""
