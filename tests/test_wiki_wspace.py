"""CLI tests for wiki_engine command surfaces."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from wiki_engine.agent_install import HARNESS_PATHS
from wiki_engine.naming import normalize_project_name
from wiki_engine.wiki_wspace import main


def write_config(repo_root: Path, qmd_enabled: bool) -> None:
    """Write minimal wiki_engine config for CLI tests."""

    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "wiki_engine.yaml").write_text(
        (
            "project_name: code_space\n"
            "wiki_root: wiki_code_space\n"
            "qmd_collection: wiki_code_space\n"
            f"qmd_enabled: {str(qmd_enabled).lower()}\n"
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


@pytest.mark.parametrize("legacy_command", ["install", "migrate"])
def test_cli_rejects_removed_legacy_commands(legacy_command: str) -> None:
    """The CLI should expose no legacy initialization command paths."""

    with pytest.raises(SystemExit) as exc_info:
        main([legacy_command])

    assert exc_info.value.code == 2


def test_search_cli_prints_qmd_output(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Search CLI should use qmd output when qmd succeeds."""

    write_config(repo_root=tmp_path, qmd_enabled=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: "/usr/bin/qmd")
    monkeypatch.setattr(
        "wiki_engine.qmd_bridge.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout='[{"path":"index.md"}]',
            stderr="",
        ),
    )

    exit_code = main(["search", "volatility", "-n", "1"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "backend=qmd" in output
    assert '[{"path":"index.md"}]' in output


def test_search_cli_prints_markdown_fallback(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Search CLI should print markdown fallback matches."""

    write_config(repo_root=tmp_path, qmd_enabled=False)
    wiki_root = tmp_path / "wiki_code_space"
    wiki_root.mkdir()
    (wiki_root / "index.md").write_text("volatility context\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["search", "volatility"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "backend=markdown" in output
    assert "index.md:1" in output


def test_search_cli_missing_qmd_prints_fallback_guidance(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Search should explain the scale boundary when optional qmd is absent."""

    write_config(repo_root=tmp_path, qmd_enabled=True)
    wiki_root = tmp_path / "wiki_code_space"
    wiki_root.mkdir()
    (wiki_root / "index.md").write_text("volatility context\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: None)

    exit_code = main(["search", "volatility"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "backend=markdown" in output
    assert "qmd is not installed" in output
    assert "about 100 Markdown files or fewer" in output


def test_init_cli_no_qmd_index_writes_config(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Init CLI should persist the qmd indexing opt-out flag."""

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init", str(project_root), "--no-qmd-index"])

    config_payload = yaml.safe_load(
        (project_root / "config" / "wiki_engine.yaml").read_text(encoding="utf-8")
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert config_payload["qmd_enabled"] is False
    assert "qmd_status=disabled" in output
    assert "llm=gemini" in output
    assert (project_root / "GEMINI.md").exists()
    assert config_payload["project_name"] == "prct"
    assert (
        project_root / ".gemini" / "skills" / "wiki-query-prct" / "SKILL.md"
    ).exists()


def test_init_cli_missing_qmd_prints_scale_guidance(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """A missing optional qmd binary should produce actionable fallback guidance."""

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: None)

    exit_code = main(["init", str(project_root)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "qmd is not installed" in output
    assert "about 100 Markdown files or fewer" in output


def test_init_cli_defaults_to_project_gemini(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Init should install Gemini project skills when --llm is omitted."""

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init", str(project_root), "--no-qmd-index"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "llm=gemini" in output
    assert "project_name=prct" in output
    assert "refresh_command=/wiki-ref-prct" in output
    assert (project_root / "GEMINI.md").exists()
    assert (
        project_root / ".gemini" / "skills" / "wiki-query-prct" / "SKILL.md"
    ).exists()
    assert not (tmp_path / "GEMINI.md").exists()


@pytest.mark.parametrize("agent_name", sorted(HARNESS_PATHS))
def test_init_cli_installs_selected_harness_in_target_project(
    monkeypatch,
    capsys,
    tmp_path: Path,
    agent_name: str,
) -> None:
    """Every supported --llm value should install its prompt and both skills."""

    project_root = tmp_path / f"{agent_name}-analytics"
    project_root.mkdir()
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "init",
            str(project_root),
            "--no-qmd-index",
            "--llm",
            agent_name,
        ]
    )

    instruction_path = project_root / HARNESS_PATHS[agent_name]["project_instruction"]
    skills_root = project_root / HARNESS_PATHS[agent_name]["project_skills"]
    project_name = normalize_project_name(project_root.name)
    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"llm={agent_name}" in output
    assert instruction_path.exists()
    assert (skills_root / f"wiki-ref-{project_name}" / "SKILL.md").exists()
    assert (
        skills_root / f"wiki-ref-{project_name}" / "references" / "wiki-workflow.md"
    ).exists()
    assert (skills_root / f"wiki-query-{project_name}" / "SKILL.md").exists()
    assert (project_root / f"wiki_{project_name}" / "index.md").exists()
    assert not (project_root / f"wiki_{project_name}" / "templates").exists()


def test_init_cli_is_idempotent_with_user_project_name(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Repeated init should reuse the configured name and existing skill files."""

    project_root = tmp_path / "folder-name"
    project_root.mkdir()
    instruction_path = project_root / "AGENTS.md"
    instruction_path.write_text("# Handwritten instructions\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    first_exit_code = main(
        [
            "init",
            str(project_root),
            "--no-qmd-index",
            "--project",
            "Demand Forecasting",
            "--llm",
            "codex",
        ]
    )
    capsys.readouterr()
    second_exit_code = main(
        [
            "init",
            str(project_root),
            "--no-qmd-index",
            "--project",
            "Demand Forecasting",
            "--llm",
            "codex",
        ]
    )

    output = capsys.readouterr().out
    instruction_text = instruction_path.read_text(encoding="utf-8")
    assert first_exit_code == 0
    assert second_exit_code == 0
    assert "project_name=deng" in output
    assert "skill_changed_files=0" in output
    assert "# Handwritten instructions" in instruction_text
    assert instruction_text.count("wiki-wspace:deng:start") == 1
    assert (project_root / "wiki_deng" / "index.md").exists()
    assert not (project_root / "wiki_fome").exists()
