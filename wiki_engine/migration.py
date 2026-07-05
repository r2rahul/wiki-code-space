"""Migration helpers to bootstrap wiki workflow in existing projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from wiki_engine.updater import UpdateResult, WikiUpdater


@dataclass(frozen=True)
class MigrationResult:
    """Result payload for project migration command."""

    project_root: Path
    config_path: Path
    project_name: str
    update_result: UpdateResult


def build_default_config(project_name: str) -> dict[str, object]:
    """Build default migration config using mandatory workflow keys."""

    return {
        "project_name": project_name,
        "wiki_root": f"wiki_{project_name}",
        "qmd_collection": f"wiki_{project_name}",
        "date_format": "%Y-%m-%d",
        "timestamp_format": "%Y-%m-%dT%H:%M:%S",
        "stage_exclude_paths": ["stage/**"],
        "default_tags": ["wiki", "agent"],
        "update_mode": "coherent",
    }


def ensure_migration_config(
    project_root: Path,
    project_name: str,
    config_relpath: str,
) -> Path:
    """Create migration config if missing and return absolute config path."""

    config_path = project_root / config_relpath
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        config_payload = build_default_config(project_name=project_name)
        config_path.write_text(
            yaml.safe_dump(config_payload, sort_keys=False),
            encoding="utf-8",
        )

    return config_path


def migrate_project(
    target_dir: str,
    project_name: str | None = None,
    config_relpath: str = "config/wiki_engine.yaml",
) -> MigrationResult:
    """Bootstrap and run wiki migration workflow in an existing project folder."""

    project_root = Path(target_dir).expanduser().resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f"Target directory does not exist: {project_root}")

    inferred_name = project_name or project_root.name
    normalized_name = WikiUpdater.normalize_project_name(inferred_name)
    config_path = ensure_migration_config(
        project_root=project_root,
        project_name=normalized_name,
        config_relpath=config_relpath,
    )

    updater = WikiUpdater(repo_root=project_root, config_path=config_path)
    update_result = updater.update(project_override=normalized_name)

    return MigrationResult(
        project_root=project_root,
        config_path=config_path,
        project_name=normalized_name,
        update_result=update_result,
    )
