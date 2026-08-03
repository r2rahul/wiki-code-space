"""Tests for harness-specific Agent Skill installation."""

from __future__ import annotations

from pathlib import Path

import pytest

from wiki_engine.agent_install import (
    HARNESS_PATHS,
    install_agent_instructions,
    project_command_suffix,
    project_skill_names,
)
from wiki_engine.updater import WikiUpdater


def write_config(repo_root: Path, project_name: str = "code_space") -> Path:
    """Write a minimal wiki_engine config and return its path."""

    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "wiki_engine.yaml"
    config_path.write_text(
        (
            f"project_name: {project_name}\n"
            f"wiki_root: wiki_{project_name}\n"
            f"qmd_collection: wiki_{project_name}\n"
            "qmd_enabled: true\n"
            "date_format: '%Y-%m-%d'\n"
            "timestamp_format: '%Y-%m-%dT%H:%M:%S'\n"
            "stage_exclude_paths:\n"
            "  - stage/**\n"
            "default_tags:\n"
            "  - wiki\n"
            "update_mode: coherent\n"
        ),
        encoding="utf-8",
    )
    return config_path


def test_project_skill_names_use_first_two_and_last_two_words() -> None:
    """Dynamic slash commands should be stable and specification-compliant."""

    assert project_command_suffix("Risk & Pricing for European Equities") == (
        "risk-pricing-european-equities"
    )
    assert project_skill_names("code_space") == (
        "wiki-ref-code-space",
        "wiki-query-code-space",
    )
    long_refresh, long_query = project_skill_names("a" * 100 + " project")
    assert len(long_refresh) <= 64
    assert len(long_query) <= 64
    assert long_refresh.removeprefix("wiki-ref-") == long_query.removeprefix(
        "wiki-query-"
    )


@pytest.mark.parametrize("agent_name", sorted(HARNESS_PATHS))
def test_project_install_writes_harness_prompt_and_two_skills(
    tmp_path: Path,
    agent_name: str,
) -> None:
    """Each harness should receive its project prompt and native skill paths."""

    config_path = write_config(tmp_path)
    updater = WikiUpdater(repo_root=tmp_path, config_path=config_path)

    result = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name=agent_name,
        jinja_env=updater.jinja_env,
    )

    instruction_path = tmp_path / HARNESS_PATHS[agent_name]["project_instruction"]
    refresh_path, query_path = result.skill_paths
    assert result.scope == "project"
    assert instruction_path.exists()
    assert (refresh_path / "SKILL.md").exists()
    assert (refresh_path / "references" / "wiki-workflow.md").exists()
    assert (query_path / "SKILL.md").exists()
    assert result.refresh_command == "/wiki-ref-code-space"
    assert result.query_command == "/wiki-query-code-space"
    assert result.refresh_command in instruction_path.read_text(encoding="utf-8")
    assert result.query_command in instruction_path.read_text(encoding="utf-8")
    assert (
        (refresh_path / "SKILL.md")
        .read_text(encoding="utf-8")
        .startswith("---\nname: wiki-ref-code-space\n")
    )


def test_user_install_writes_only_beneath_user_home(tmp_path: Path) -> None:
    """The --user implementation must not create project-level harness files."""

    repo_root = tmp_path / "repo"
    user_home = tmp_path / "home"
    repo_root.mkdir()
    config_path = write_config(repo_root)
    updater = WikiUpdater(repo_root=repo_root, config_path=config_path)

    result = install_agent_instructions(
        repo_root=repo_root,
        project_name="code_space",
        agent_name="codex",
        jinja_env=updater.jinja_env,
        user=True,
        user_home=user_home,
    )

    assert result.scope == "user"
    assert result.instruction_path == user_home / ".codex" / "AGENTS.md"
    assert all(path.is_relative_to(user_home) for path in result.skill_paths)
    assert not (repo_root / "AGENTS.md").exists()
    assert not (repo_root / ".agents").exists()


def test_install_replaces_its_marked_block_without_removing_handwritten_text(
    tmp_path: Path,
) -> None:
    """Repeated installation should be idempotent and preserve manual prompts."""

    config_path = write_config(tmp_path)
    updater = WikiUpdater(repo_root=tmp_path, config_path=config_path)
    instruction_path = tmp_path / "CLAUDE.md"
    instruction_path.write_text("# Handwritten\n", encoding="utf-8")

    first = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="claude",
        jinja_env=updater.jinja_env,
    )
    second = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="claude",
        jinja_env=updater.jinja_env,
    )

    content = instruction_path.read_text(encoding="utf-8")
    assert "# Handwritten" in content
    assert content.count("<!-- wiki-engine:code-space:start -->") == 1
    assert first.changed_files
    assert second.changed_files == []


def test_install_migrates_legacy_unsuffixed_instruction_marker(tmp_path: Path) -> None:
    """Old /wiki-refresh prompt blocks should be replaced, not duplicated."""

    config_path = write_config(tmp_path)
    updater = WikiUpdater(repo_root=tmp_path, config_path=config_path)
    instruction_path = tmp_path / "AGENTS.md"
    instruction_path.write_text(
        "# Existing\n\n"
        "<!-- wiki-engine:start -->\n"
        "/wiki-refresh\n"
        "<!-- wiki-engine:end -->\n",
        encoding="utf-8",
    )

    install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="codex",
        jinja_env=updater.jinja_env,
    )

    content = instruction_path.read_text(encoding="utf-8")
    assert "/wiki-refresh" not in content
    assert content.count("wiki-engine:code-space:start") == 1
    assert "/wiki-ref-code-space" in content
