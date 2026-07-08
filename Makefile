.PHONY: install format test build update-wiki init-wiki

install:
	uv sync

format:
	uv run ruff check --fix .
	uv run ruff format

test:
	uv run pytest -q

build:
	uv build

update-wiki:
	uv run python -m wiki_engine.cli update --project code_space

init-wiki:
	uv run python -m wiki_engine.cli init . --project code_space
