"""Tests for initialization workflow on existing project folders."""

from __future__ import annotations

from pathlib import Path

import yaml

from wiki_engine.migration import initialize_project, migrate_project


def test_initialize_project_bootstraps_config_and_wiki(tmp_path: Path) -> None:
    """Initialization should create config and construct required wiki folder."""

    project_root = tmp_path / "legacy-analytics-project"
    project_root.mkdir(parents=True)

    result = initialize_project(target_dir=str(project_root))

    config_path = project_root / "config" / "wiki_engine.yaml"
    wiki_root = project_root / "wiki_legacy_analytics_project"

    assert config_path.exists()
    assert wiki_root.exists()
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "stage" / ".noindex").exists()
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / "CLAUDE.md").exists()
    assert (
        project_root
        / ".ai"
        / "wiki_legacy_analytics_project"
        / "llm_wiki_workflow_guide.md"
    ).exists()
    assert "wiki_legacy_analytics_project" in (
        project_root / "AGENTS.md"
    ).read_text(encoding="utf-8")
    assert "wiki_legacy_analytics_project" in (
        project_root / "CLAUDE.md"
    ).read_text(encoding="utf-8")

    config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config_payload["project_name"] == "legacy_analytics_project"
    assert config_payload["qmd_collection"] == "wiki_legacy_analytics_project"

    assert result.project_name == "legacy_analytics_project"
    assert len(result.update_result.changed_files) >= 1


def test_migrate_project_alias_still_initializes(tmp_path: Path) -> None:
    """The legacy migrate API should remain a compatible alias."""

    project_root = tmp_path / "legacy-project"
    project_root.mkdir(parents=True)

    result = migrate_project(target_dir=str(project_root))

    assert result.project_name == "legacy_project"
    assert (project_root / "wiki_legacy_project" / "index.md").exists()
