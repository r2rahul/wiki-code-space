"""CLI tests for wiki_engine command surfaces."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
