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


def test_project_skill_names_use_first_two_and_last_two_clean_characters() -> None:
    """Dynamic slash commands should use the compact canonical project name."""

    assert project_command_suffix("Risk & Pricing for European Equities") == "ries"
    assert project_command_suffix("A! B@") == "ab"
    assert project_skill_names("code_space") == (
        "wiki-ref-coce",
        "wiki-query-coce",
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
    assert instruction_path.exists()
    assert (refresh_path / "SKILL.md").exists()
    assert (refresh_path / "references" / "wiki-workflow.md").exists()
    assert (query_path / "SKILL.md").exists()
    assert result.refresh_command == "/wiki-ref-coce"
    assert result.query_command == "/wiki-query-coce"
    assert result.refresh_command in instruction_path.read_text(encoding="utf-8")
    assert result.query_command in instruction_path.read_text(encoding="utf-8")
    assert (
        (refresh_path / "SKILL.md")
        .read_text(encoding="utf-8")
        .startswith("---\nname: wiki-ref-coce\n")
    )


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
    assert content.count("<!-- wiki-wspace:coce:start -->") == 1
    assert first.changed_files
    assert second.changed_files == []


def test_install_is_idempotent_for_new_instruction_file(tmp_path: Path) -> None:
    """A generated-only harness prompt should not gain leading blank lines."""

    config_path = write_config(tmp_path)
    updater = WikiUpdater(repo_root=tmp_path, config_path=config_path)

    first = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="codex",
        jinja_env=updater.jinja_env,
    )
    second = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="codex",
        jinja_env=updater.jinja_env,
    )

    instruction_text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert first.changed_files
    assert second.changed_files == []
    assert instruction_text.startswith("<!-- wiki-wspace:coce:start -->")


def test_copilot_install_uses_github_native_skill_directory(tmp_path: Path) -> None:
    """Copilot project skills should stay alongside its GitHub instructions."""

    config_path = write_config(tmp_path)
    updater = WikiUpdater(repo_root=tmp_path, config_path=config_path)

    result = install_agent_instructions(
        repo_root=tmp_path,
        project_name="code_space",
        agent_name="copilot",
        jinja_env=updater.jinja_env,
    )

    assert result.instruction_path == tmp_path / ".github/copilot-instructions.md"
    assert all(
        path.is_relative_to(tmp_path / ".github/skills")
        for path in result.skill_paths
    )
    assert not (tmp_path / ".agents").exists()
