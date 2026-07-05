.PHONY: format test run-notebook

install:
	uv sync

format:
	uv run ruff check --fix .
	uv run ruff format
