"""Orchestrates coherent wiki, semantic bridge, and qmd update runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PackageLoader
import yaml

from wiki_engine.agent_install import install_agent_instructions
from wiki_engine.graph_bridge import update_graph_bridge
from wiki_engine.qmd_bridge import refresh_qmd_index, search_wiki
from wiki_engine.session_distill import distill_session_note, discover_session_notes


@dataclass(frozen=True)
class WikiEngineConfig:
    """Configuration values that drive wiki_engine update workflows."""

    project_name: str
    wiki_root: str
    qmd_collection: str
    qmd_enabled: bool
    date_format: str
    timestamp_format: str
    stage_exclude_paths: list[str]
    default_tags: list[str]
    update_mode: str


@dataclass(frozen=True)
class UpdateResult:
    """Structured result for one coherent wiki update call."""

    changed_files: list[str]
    graph_result: dict[str, Any]
    qmd_result: dict[str, Any]


class WikiUpdater:
    """Run one coherent update that keeps wiki and graph artifacts in sync."""

    def __init__(self, repo_root: Path, config_path: Path) -> None:
        """Initialize updater with repository and YAML configuration."""

        self.repo_root = repo_root
        self.config_path = config_path
        self.config = self._load_config(config_path=config_path)
        template_dir = repo_root / "wiki_engine" / "templates"
        loader_list: list[FileSystemLoader | PackageLoader] = []
        if template_dir.exists():
            loader_list.append(FileSystemLoader(str(template_dir)))
        loader_list.append(PackageLoader("wiki_engine", "templates"))
        self.jinja_env = Environment(
            loader=ChoiceLoader(loader_list),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _load_config(self, config_path: Path) -> WikiEngineConfig:
        """Load and validate required config keys from YAML."""

        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        required_keys = {
            "project_name",
            "wiki_root",
            "qmd_collection",
            "date_format",
            "timestamp_format",
            "stage_exclude_paths",
            "default_tags",
            "update_mode",
        }
        missing_keys = sorted(required_keys.difference(raw_config.keys()))
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")

        return WikiEngineConfig(
            project_name=str(raw_config["project_name"]),
            wiki_root=str(raw_config["wiki_root"]),
            qmd_collection=str(raw_config["qmd_collection"]),
            qmd_enabled=bool(raw_config.get("qmd_enabled", True)),
            date_format=str(raw_config["date_format"]),
            timestamp_format=str(raw_config["timestamp_format"]),
            stage_exclude_paths=list(raw_config["stage_exclude_paths"]),
            default_tags=list(raw_config["default_tags"]),
            update_mode=str(raw_config["update_mode"]),
        )

    @staticmethod
    def normalize_project_name(raw_name: str) -> str:
        """Normalize project names for stable wiki folder conventions."""

        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", raw_name.strip()).strip("_")
        if not normalized:
            raise ValueError("Project name cannot be empty after normalization")
        return normalized.lower()

    def update(self, project_override: str | None = None) -> UpdateResult:
        """Execute one coherent Wiki+bridge+qmd update workflow."""

        now = datetime.now()
        project_name = project_override or self.config.project_name
        wiki_root = self.repo_root / f"wiki_{project_name}"

        changed_files: list[str] = []
        changed_files.extend(
            self._ensure_wiki_scaffold(
                project_name=project_name,
                wiki_root=wiki_root,
                now=now,
            )
        )
        changed_files.extend(self._ensure_agent_files(project_name=project_name))

        distilled_changed_files = self._distill_sessions_if_present(
            wiki_root=wiki_root,
            now=now,
        )
        changed_files.extend(distilled_changed_files)

        graph_result = update_graph_bridge(
            project_name=project_name,
            wiki_root=wiki_root,
            exclude_paths=self.config.stage_exclude_paths,
        )

        qmd_result = refresh_qmd_index(
            wiki_root=wiki_root,
            qmd_collection=f"wiki_{project_name}",
            exclude_paths=self.config.stage_exclude_paths,
            qmd_enabled=self.config.qmd_enabled,
        )

        changed_files.append(
            self._append_log_entry(
                wiki_root=wiki_root,
                now=now,
                changed_files=changed_files,
                update_type=(
                    "session_distill" if distilled_changed_files else "code_sync"
                ),
            )
        )

        return UpdateResult(
            changed_files=sorted(set(changed_files)),
            graph_result=graph_result,
            qmd_result=qmd_result,
        )

    def search(
        self,
        query_text: str,
        project_override: str | None = None,
        result_count: int = 10,
    ) -> dict[str, Any]:
        """Search the project wiki using qmd with markdown fallback."""

        project_name = project_override or self.config.project_name
        wiki_root = self.repo_root / f"wiki_{project_name}"
        return search_wiki(
            query_text=query_text,
            wiki_root=wiki_root,
            qmd_collection=f"wiki_{project_name}",
            exclude_paths=self.config.stage_exclude_paths,
            result_count=result_count,
            qmd_enabled=self.config.qmd_enabled,
        )

    def _ensure_wiki_scaffold(
        self,
        project_name: str,
        wiki_root: Path,
        now: datetime,
    ) -> list[str]:
        """Create or refresh required wiki files and folders."""

        changed_files: list[str] = []

        directories = [
            wiki_root / ".qmd",
            wiki_root / "architecture",
            wiki_root / "decisions",
            wiki_root / "qa",
            wiki_root / "sessions",
            wiki_root / "glossary",
            wiki_root / "stage" / "plan",
            wiki_root / "stage" / "spec",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        created_or_updated = {
            wiki_root / "index.md": self._render_template(
                "index.md.j2",
                project_name=project_name,
                wiki_root=wiki_root.name,
                date_text=now.strftime(self.config.date_format),
            ),
            wiki_root / "log.md": self._render_template(
                "log.md.j2",
                date_text=now.strftime(self.config.date_format),
            ),
            wiki_root / "qmd.yml": self._render_qmd_yaml(project_name=project_name),
            wiki_root / "stage" / ".noindex": "stage is excluded from indexing\n",
            wiki_root / "stage" / ".qmdexclude": "stage is excluded from qmd\n",
        }

        for file_path, content in created_or_updated.items():
            if file_path.exists() and file_path.name == "log.md":
                continue
            was_updated = self._write_if_changed(file_path=file_path, content=content)
            if was_updated:
                changed_files.append(file_path.relative_to(self.repo_root).as_posix())

        return changed_files

    def _ensure_agent_files(self, project_name: str) -> list[str]:
        """Ensure root agent instruction files include wiki refresh template."""

        changed_files: list[str] = []
        for agent_name in ("codex", "claude"):
            result = install_agent_instructions(
                repo_root=self.repo_root,
                project_name=project_name,
                agent_name=agent_name,
                jinja_env=self.jinja_env,
            )
            changed_files.extend(result.changed_files)

        return changed_files

    def _distill_sessions_if_present(self, wiki_root: Path, now: datetime) -> list[str]:
        """Distill all session notes into permanent note destinations."""

        changed_files: list[str] = []
        sessions_dir = wiki_root / "sessions"
        for session_path in discover_session_notes(sessions_dir):
            result = distill_session_note(
                session_path=session_path,
                wiki_root=wiki_root,
                current_date=now.date(),
            )
            changed_files.extend(
                [
                    changed_path.relative_to(self.repo_root).as_posix()
                    for changed_path in result.changed_files
                ]
            )
        return changed_files

    def _append_log_entry(
        self,
        wiki_root: Path,
        now: datetime,
        changed_files: list[str],
        update_type: str,
    ) -> str:
        """Append one concise entry to append-only log.md."""

        log_path = wiki_root / "log.md"
        timestamp_text = now.strftime(self.config.timestamp_format)
        changed_file_list = ", ".join(changed_files)
        reason_text = "Coherent wiki+graph+qmd update run"

        entry = (
            f"\n## {timestamp_text}\n"
            f"- update_type: {update_type}\n"
            f"- changed_files: [{changed_file_list}]\n"
            f"- reason: {reason_text}\n"
            "- source: agent\n"
        )

        with log_path.open("a", encoding="utf-8") as file_pointer:
            file_pointer.write(entry)

        return log_path.relative_to(self.repo_root).as_posix()

    def _render_template(self, template_name: str, **kwargs: str) -> str:
        """Render a Jinja template with deterministic newline policy."""

        template = self.jinja_env.get_template(template_name)
        rendered = template.render(**kwargs)
        if rendered.endswith("\n"):
            return rendered
        return f"{rendered}\n"

    def _render_qmd_yaml(self, project_name: str) -> str:
        """Render qmd YAML with strict stage exclusion contract."""

        content = {
            "collection": f"wiki_{project_name}",
            "ignore": ["stage/**", "_*.md"],
        }
        return yaml.safe_dump(content, sort_keys=False)

    def _write_if_changed(self, file_path: Path, content: str) -> bool:
        """Write file content only when changed to keep updates atomic."""

        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and file_path.read_text(encoding="utf-8") == content:
            return False
        file_path.write_text(content, encoding="utf-8")
        return True
