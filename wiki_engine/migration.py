"""Initialization helpers to bootstrap wiki workflow in existing projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from wiki_engine.updater import UpdateResult, WikiUpdater


@dataclass(frozen=True)
class InitializationResult:
    """Result payload for project initialization command."""

    project_root: Path
    config_path: Path
    project_name: str
    update_result: UpdateResult


def build_default_config(
    project_name: str,
    qmd_enabled: bool = True,
) -> dict[str, object]:
    """Build default initialization config using mandatory workflow keys."""

    return {
        "project_name": project_name,
        "wiki_root": f"wiki_{project_name}",
        "qmd_collection": f"wiki_{project_name}",
        "qmd_enabled": qmd_enabled,
        "date_format": "%Y-%m-%d",
        "timestamp_format": "%Y-%m-%dT%H:%M:%S",
        "stage_exclude_paths": ["stage/**"],
        "default_tags": ["wiki", "agent"],
        "update_mode": "coherent",
    }


def ensure_initialization_config(
    project_root: Path,
    project_name: str,
    config_relpath: str,
    qmd_enabled: bool = True,
) -> Path:
    """Create initialization config if missing and return absolute config path."""

    config_path = project_root / config_relpath
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        config_payload = build_default_config(
            project_name=project_name,
            qmd_enabled=qmd_enabled,
        )
        config_path.write_text(
            yaml.safe_dump(config_payload, sort_keys=False),
            encoding="utf-8",
        )

    return config_path


def initialize_project(
    target_dir: str,
    project_name: str | None = None,
    config_relpath: str = "config/wiki_engine.yaml",
    qmd_enabled: bool = True,
) -> InitializationResult:
    """Bootstrap and run wiki workflow in an existing project folder."""

    project_root = Path(target_dir).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f"Target directory does not exist: {project_root}")

    inferred_name = project_name or project_root.name
    normalized_name = WikiUpdater.normalize_project_name(inferred_name)
    config_path = ensure_initialization_config(
        project_root=project_root,
        project_name=normalized_name,
        config_relpath=config_relpath,
        qmd_enabled=qmd_enabled,
    )

    updater = WikiUpdater(repo_root=project_root, config_path=config_path)
    update_result = updater.update(project_override=normalized_name)

    return InitializationResult(
        project_root=project_root,
        config_path=config_path,
        project_name=normalized_name,
        update_result=update_result,
    )


MigrationResult = InitializationResult


def ensure_migration_config(
    project_root: Path,
    project_name: str,
    config_relpath: str,
    qmd_enabled: bool = True,
) -> Path:
    """Backward-compatible alias for initialization config creation."""

    return ensure_initialization_config(
        project_root=project_root,
        project_name=project_name,
        config_relpath=config_relpath,
        qmd_enabled=qmd_enabled,
    )


def migrate_project(
    target_dir: str,
    project_name: str | None = None,
    config_relpath: str = "config/wiki_engine.yaml",
    qmd_enabled: bool = True,
) -> InitializationResult:
    """Backward-compatible alias for initialize_project."""

    return initialize_project(
        target_dir=target_dir,
        project_name=project_name,
        config_relpath=config_relpath,
        qmd_enabled=qmd_enabled,
    )
