.PHONY: install run debug clean fclean re lint lint-strict test

# fclean asks config.txt where the maze is written rather than
# assuming maze.txt, since OUTPUT_FILE is configurable.
OUTPUT_FILE := $(shell grep '^OUTPUT_FILE=' config.txt | cut -d= -f2)

MYPY_FLAGS = --warn-return-any \
			--warn-unused-ignores \
			--ignore-missing-imports \
			--disallow-untyped-defs \
			--check-untyped-defs

install:
	pip install -e .
	pip install -r requirements-dev.txt

run:
	python3 a_maze_ing.py config.txt

debug:
	python3 -m pdb a_maze_ing.py config.txt

# Build artifacts and tool caches only: everything here is regenerated
# by make install or the next tool run. The wheel at the repo root is a
# tracked deliverable and is deliberately not matched.
#
# egg-info is removed by explicit path, never by a recursive -name: in a
# virtualenv's site-packages a *.egg-info directory is a package's
# installed metadata, and deleting it breaks pip for that package.
clean:
	find . \( -path './.venv*' -o -path './venv*' \) -prune -o \
		\( -name '__pycache__' -o -name '.pytest_cache' \
		   -o -name '*.py[co]' \) \
		-exec rm -rf {} +
	rm -rf build dist .mypy_cache src/*.egg-info *.egg-info

# clean plus the generated maze, which is program output rather than a
# build artifact.
fclean: clean
	rm -f "$(OUTPUT_FILE)"

re: fclean install

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

test:
	python3 -m pytest -q
