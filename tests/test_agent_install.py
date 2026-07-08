"""Tests for assistant instruction installation."""

from __future__ import annotations

from pathlib import Path

from wiki_engine.agent_install import install_agent_instructions
from wiki_engine.updater import WikiUpdater


def test_install_vscode_agent_writes_instruction_and_guides(tmp_path: Path) -> None:
    """Agent install should write instruction plus shared prompt guides."""

    repo_root = tmp_path
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "wiki_engine.yaml"
    config_path.write_text(
        (
            "project_name: code_space\n"
            "wiki_root: wiki_code_space\n"
            "qmd_collection: wiki_code_space\n"
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
    updater = WikiUpdater(repo_root=repo_root, config_path=config_path)

    result = install_agent_instructions(
        repo_root=repo_root,
        project_name="code_space",
        agent_name="vscode",
        jinja_env=updater.jinja_env,
    )

    instruction_path = repo_root / ".github" / "copilot-instructions.md"
    guide_path = (
        repo_root / "wiki_code_space" / "templates" / "llm_wiki_workflow_guide.md"
    )
    bootstrap_path = (
        repo_root / "wiki_code_space" / "templates" / "wiki_first_init_bootstrap.md"
    )
    assert instruction_path.exists()
    assert guide_path.exists()
    assert bootstrap_path.exists()
    assert "python -m wiki_engine.cli update --project code_space" in (
        instruction_path.read_text(encoding="utf-8")
    )
    assert "wiki_first_init_bootstrap.md" in instruction_path.read_text(
        encoding="utf-8"
    )
    assert "Never read, summarize, index, or update wiki_code_space/stage/" in (
        guide_path.read_text(encoding="utf-8")
    )
    assert "python -m wiki_engine.cli init <target_dir> --project code_space" in (
        bootstrap_path.read_text(encoding="utf-8")
    )
    assert result.guide_path.as_posix() == (
        "wiki_code_space/templates/llm_wiki_workflow_guide.md"
    )
    assert result.bootstrap_path.as_posix() == (
        "wiki_code_space/templates/wiki_first_init_bootstrap.md"
    )
    assert ".github/copilot-instructions.md" in result.changed_files
