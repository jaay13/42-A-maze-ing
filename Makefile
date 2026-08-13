.PHONY: install run debug clean

install:
	pip install -e .

run:
	python3 a_maze_ing.py config.txt

debug:
	python3 -m pdb a_maze_ing.py config.txt

clean:
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf build dist *.egg-info
