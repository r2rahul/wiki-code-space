"""Regression tests for wheel metadata and command entry points."""

from __future__ import annotations

from pathlib import Path
import tomllib


def test_wheel_exposes_only_wiki_wspace_command() -> None:
    """Installed wheels must expose one canonical CLI entry point."""

    project_root = Path(__file__).parents[1]
    with (project_root / "pyproject.toml").open("rb") as pyproject_file:
        project_config = tomllib.load(pyproject_file)

    scripts = project_config["project"]["scripts"]
    assert scripts == {"wiki_wspace": "wiki_engine.wiki_wspace:main"}
    assert not (project_root / "wiki_engine" / "cli.py").exists()
    assert not (project_root / "wiki_engine" / "__main__.py").exists()
