.PHONY: install run debug clean lint lint-strict

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

clean:
	find . -path ./.venv -prune -o -name '__pycache__' -exec rm -rf {} +
	rm -rf build dist
	rm -rf .mypy_cache

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict
