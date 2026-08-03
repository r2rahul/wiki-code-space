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
	uv run wiki_wspace update --project code_space

init-wiki:
	uv run wiki_wspace init . --project code_space
