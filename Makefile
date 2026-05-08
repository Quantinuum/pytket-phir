.PHONY: install dev dev-all tests lint audit docs clean build

install:
	uv sync --no-dev

dev:
	uv sync --dev

dev-all:
	uv sync --dev --extra phirc

tests:
	uv run python tests/e2e_test.py
	uv run pytest -s -x -vv tests/test*.py

lint:
	uv run prek run --all-files

audit:
	uv audit --locked

docs:
	# uv run sphinx-apidoc --implicit-namespaces -f -o docs/source/ pytket
	uv run sphinx-build -M html docs/source/ docs/build/

clean:
	rm -rf *.egg-info dist build docs/build

build: clean
	uv build
