"""Tests for assistant instruction installation."""

from __future__ import annotations

from pathlib import Path

from wiki_engine.agent_install import install_agent_instructions
from wiki_engine.updater import WikiUpdater


def test_install_vscode_agent_writes_instruction_and_skill(tmp_path: Path) -> None:
    """Agent install should write a scoped prompt block and shared LLM guide."""

    repo_root = tmp_path
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "wiki_engine.yaml"
    config_path.write_text(
        (
            "project_name: code_space\n"
            "wiki_root: wiki_code_space\n"
            "qmd_collection: wiki_code_space\n"
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
    skill_path = repo_root / ".ai" / "wiki_code_space" / "llm_wiki_workflow_guide.md"
    assert instruction_path.exists()
    assert skill_path.exists()
    assert "python -m wiki_engine.cli update --project code_space" in (
        instruction_path.read_text(encoding="utf-8")
    )
    assert "Never read, summarize, index, or update wiki_code_space/stage/" in (
        skill_path.read_text(encoding="utf-8")
    )
    assert ".github/copilot-instructions.md" in result.changed_files
