"""CLI tests for wiki_engine command surfaces."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from wiki_engine.cli import main


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


def test_install_cli_defaults_to_project_gemini(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """Bare install should target Gemini at project scope."""

    write_config(repo_root=tmp_path, qmd_enabled=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("wiki_engine.cli.shutil.which", lambda _: None)

    exit_code = main(["install"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "agent=gemini" in output
    assert "scope=project" in output
    assert "refresh_command=/wiki-ref-code-space" in output
    assert "qmd is not installed" in output
    assert (tmp_path / "GEMINI.md").exists()
    assert (
        tmp_path / ".gemini" / "skills" / "wiki-query-code-space" / "SKILL.md"
    ).exists()


def test_install_cli_bootstraps_config_and_skills_in_fresh_project(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """A wheel install command must work without a source-tree config file."""

    project_root = tmp_path / "Fresh Analytics Project"
    project_root.mkdir()
    monkeypatch.chdir(project_root)
    monkeypatch.setattr("wiki_engine.cli.shutil.which", lambda _: None)

    exit_code = main(["install", "codex"])

    config_path = project_root / "config" / "wiki_engine.yaml"
    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    output = capsys.readouterr().out
    assert exit_code == 0
    assert config_payload["project_name"] == "fresh_analytics_project"
    assert config_payload["wiki_root"] == "wiki_fresh_analytics_project"
    assert "config_created=true" in output
    assert (project_root / "AGENTS.md").exists()
    assert (
        project_root
        / ".agents"
        / "skills"
        / "wiki-ref-fresh-analytics-project"
        / "SKILL.md"
    ).exists()
    assert (
        project_root
        / ".agents"
        / "skills"
        / "wiki-ref-fresh-analytics-project"
        / "references"
        / "wiki-workflow.md"
    ).exists()
    assert (
        project_root
        / ".agents"
        / "skills"
        / "wiki-query-fresh-analytics-project"
        / "SKILL.md"
    ).exists()


def test_install_cli_user_scope_does_not_write_project(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    """CLI --user should direct every generated file beneath the user home."""

    repo_root = tmp_path / "repo"
    user_home = tmp_path / "home"
    repo_root.mkdir()
    write_config(repo_root=repo_root, qmd_enabled=False)
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: user_home))

    exit_code = main(["install", "codex", "--user"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "scope=user" in output
    assert (user_home / ".codex" / "AGENTS.md").exists()
    assert not (repo_root / "AGENTS.md").exists()


def test_install_cli_user_scope_does_not_bootstrap_project_config(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """A fresh --user install must preserve its no-project-writes contract."""

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.chdir(repo_root)

    with pytest.raises(SystemExit) as exc_info:
        main(["install", "codex", "--user"])

    assert exc_info.value.code == 2
    assert not (repo_root / "config" / "wiki_engine.yaml").exists()
    assert not (repo_root / "AGENTS.md").exists()
