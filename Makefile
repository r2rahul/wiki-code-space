.PHONY: install format test build update-wiki migrate-wiki

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

migrate-wiki:
	uv run python -m wiki_engine.cli migrate . --project code_space
