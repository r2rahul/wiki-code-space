"""Regression tests for wheel metadata and command entry points."""

from __future__ import annotations

from pathlib import Path
import tomllib


def test_wheel_exposes_hyphenated_and_underscore_commands() -> None:
    """Installed wheels must support both documented CLI spellings."""

    project_root = Path(__file__).parents[1]
    with (project_root / "pyproject.toml").open("rb") as pyproject_file:
        project_config = tomllib.load(pyproject_file)

    scripts = project_config["project"]["scripts"]
    assert scripts["wiki-engine"] == "wiki_engine.cli:main"
    assert scripts["wiki_engine"] == "wiki_engine.cli:main"
