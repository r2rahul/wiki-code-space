"""Tests for initialization workflow on existing project folders."""

from __future__ import annotations

from pathlib import Path

import yaml

from wiki_engine.migration import initialize_project


def test_initialize_project_bootstraps_config_and_wiki(tmp_path: Path) -> None:
    """Initialization should create config and construct required wiki folder."""

    project_root = tmp_path / "legacy-analytics-project"
    project_root.mkdir(parents=True)

    result = initialize_project(target_dir=str(project_root))

    config_path = project_root / "config" / "wiki_engine.yaml"
    wiki_root = project_root / "wiki_lect"

    assert config_path.exists()
    assert wiki_root.exists()
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "stage" / ".noindex").exists()
    assert not (wiki_root / "sessions" / "_template.md").exists()
    assert not (wiki_root / "architecture" / "config_params.md").exists()
    assert not (wiki_root / "qa" / "business.md").exists()
    assert not (wiki_root / "qa" / "technical.md").exists()
    assert not (wiki_root / "decisions" / "adr-placeholder.md").exists()
    assert not (wiki_root / "glossary" / "terms.md").exists()
    assert not (project_root / "AGENTS.md").exists()
    assert not (project_root / "CLAUDE.md").exists()
    assert not (project_root / ".agents").exists()

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config_payload["project_name"] == "lect"
    assert config_payload["qmd_collection"] == "wiki_lect"
    assert config_payload["qmd_enabled"] is True

    assert result.project_name == "lect"
    assert len(result.update_result.changed_files) >= 1


def test_initialize_project_can_disable_qmd_indexing(tmp_path: Path) -> None:
    """Initialization should persist explicit qmd indexing opt-out."""

    project_root = tmp_path / "legacy-analytics-project"
    project_root.mkdir(parents=True)

    result = initialize_project(target_dir=str(project_root), qmd_enabled=False)

    config_path = project_root / "config" / "wiki_engine.yaml"
    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config_payload["qmd_enabled"] is False
    assert result.update_result.qmd_result["status"] == "disabled"


def test_initialize_project_uses_directory_name_when_override_is_omitted(
    tmp_path: Path,
) -> None:
    """Default naming should clean and compact the target directory name."""

    project_root = tmp_path / "folder-name"
    project_root.mkdir(parents=True)
    first_result = initialize_project(
        target_dir=str(project_root),
        project_name="Demand Forecasting",
        qmd_enabled=False,
    )

    second_result = initialize_project(
        target_dir=str(project_root),
        qmd_enabled=False,
    )

    config_payload = yaml.safe_load(
        (project_root / "config" / "wiki_engine.yaml").read_text(encoding="utf-8")
    )
    assert first_result.project_name == "deng"
    assert second_result.project_name == "fome"
    assert config_payload["project_name"] == "fome"
    assert config_payload["wiki_root"] == "wiki_fome"
    assert config_payload["qmd_collection"] == "wiki_fome"
    assert (project_root / "wiki_deng" / "index.md").exists()
    assert (project_root / "wiki_fome" / "index.md").exists()


def test_initialize_project_removes_special_characters_from_user_name(
    tmp_path: Path,
) -> None:
    """User-provided names should be cleaned before compacting."""

    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)

    result = initialize_project(
        target_dir=str(project_root),
        project_name="!!! My Project @2026 ###",
        qmd_enabled=False,
    )

    assert result.project_name == "my26"
    assert (project_root / "wiki_my26" / "index.md").exists()
