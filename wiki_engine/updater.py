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
    """Configuration values that drive wiki_engine update workflows.

    This frozen dataclass holds all configuration parameters required for a
    coherent wiki update cycle, including project identification, path layout,
    qmd enablement, and temporal formatting.

    Attributes:
        project_name (str): Canonical project identifier; normalized alphanumeric
            with underscores.
        wiki_root (str): Relative path to the wiki folder (e.g., "wiki_myproject").
        qmd_collection (str): Collection name registered with qmd for semantic search.
        qmd_enabled (bool): Whether to attempt qmd indexing and query operations.
        date_format (str): Python strftime format for wiki dates (e.g., "%Y-%m-%d").
        timestamp_format (str): Python strftime format for update log timestamps
            (e.g., "%Y-%m-%dT%H:%M:%S").
        stage_exclude_paths (list[str]): Glob patterns to exclude from indexing
            (e.g., ["stage/**"]).
        default_tags (list[str]): Default tags applied to wiki documents.
        update_mode (str): Wiki update strategy; presently supports "coherent".
    """

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
    """Structured result for one coherent wiki update call.

    Contains the unified output of an update workflow, including file change
    tracking and detailed status from semantic graph and qmd subsystems.

    Attributes:
        changed_files (list[str]): Sorted, deduplicated list of relative file
            paths (POSIX format) modified by the update.
        graph_result (dict[str, Any]): Status payload from graph bridge operations,
            including graph construction and constraint validation results.
        qmd_result (dict[str, Any]): Status payload from qmd indexing operations,
            including collection registration and embedding refresh results.
    """

    changed_files: list[str]
    graph_result: dict[str, Any]
    qmd_result: dict[str, Any]


class WikiUpdater:
    """Orchestrate coherent wiki, graph bridge, and qmd update workflows.

    This class manages a complete update cycle that synchronizes wiki markdown
    artifacts, semantic graph constraints, and qmd searchability. It handles
    template rendering, configuration loading, and coordinated subsystem calls.
    """

    def __init__(self, repo_root: Path, config_path: Path) -> None:
        """Initialize updater with repository and YAML configuration.

        Args:
            repo_root (Path): Absolute or relative path to the repository root.
            config_path (Path): Absolute or relative path to wiki_engine.yaml config.

        Raises:
            ValueError: If required config keys are missing from the YAML file.
        """

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
        """Load and validate required config keys from YAML.

        Args:
            config_path (Path): Path to wiki_engine.yaml configuration file.

        Returns:
            WikiEngineConfig: Validated, frozen config dataclass.

        Raises:
            ValueError: If any required config key is missing.
        """

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
        """Normalize project names for stable wiki folder conventions.

        Converts arbitrary project names to lowercase alphanumeric with underscores,
        stripping leading/trailing underscores and collapsing consecutive separators.
        This ensures deterministic wiki folder names (wiki_<normalized_name>).

        Args:
            raw_name (str): Arbitrary project name (may contain spaces, hyphens, etc.).

        Returns:
            str: Normalized project name in lowercase, alphanumeric with underscores.

        Raises:
            ValueError: If normalization results in an empty string.
        """

        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", raw_name.strip()).strip("_")
        if not normalized:
            raise ValueError("Project name cannot be empty after normalization")
        return normalized.lower()

    def update(self, project_override: str | None = None) -> UpdateResult:
        """Execute one coherent Wiki+bridge+qmd update workflow.

        Orchestrates a complete update cycle:
        1. Ensures wiki scaffold (directories and template-rendered files).
        2. Installs/refreshes agent instruction files.
        3. Distills session notes into permanent wiki destinations.
        4. Updates semantic graph bridge.
        5. Refreshes qmd collection index.
        6. Appends atomic log entry.

        Args:
            project_override (str | None): Override project name from config.
                If None, uses config.project_name. Used for multi-project scenarios.

        Returns:
            UpdateResult: Aggregated result including changed files and subsystem
                status payloads from graph bridge and qmd operations.
        """

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
        """Search the project wiki using qmd with markdown fallback.

        Attempts semantic search via qmd; if unavailable or disabled, falls back
        to deterministic case-insensitive markdown text matching.

        Args:
            query_text (str): Query string to search for in wiki content.
            project_override (str | None): Override project name from config.
            result_count (int): Maximum number of results to return. Defaults to 10.

        Returns:
            dict[str, Any]: Search result payload with 'status' key ('ok' or
                'fallback') and 'results' key containing ordered list of matches.
                Each match includes path, line number, score, and snippet.
        """

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
        """Create or refresh required wiki files and folders.

        Creates canonical directory structure (architecture, decisions, qa, sessions,
        glossary, stage) and renders template-driven files (index.md, log.md, qmd.yml).
        Only updates files when content has changed.

        Args:
            project_name (str): Normalized project identifier.
            wiki_root (Path): Absolute path to wiki root directory.
            now (datetime): Current datetime for template rendering.

        Returns:
            list[str]: Relative paths (POSIX) of files created or updated.
        """

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
        """Ensure root agent instruction files include wiki refresh template.

        Installs or refreshes agent instruction files (.github/copilot-instructions.md,
        .claude/instructions.md) with wiki refresh command templates for supported
        agent platforms (codex, claude).

        Args:
            project_name (str): Normalized project identifier.

        Returns:
            list[str]: Relative paths (POSIX) of agent instruction files created
                or updated.
        """

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
        """Distill all session notes into permanent note destinations.

        Discovers and processes session notes (YYYY-MM-DD-<topic>.md) in the
        sessions/ folder, extracting structured lessons and distributing them
        into permanent wiki locations (architecture, decisions, qa, glossary).

        Args:
            wiki_root (Path): Absolute path to wiki root directory.
            now (datetime): Current datetime for timestamping distilled notes.

        Returns:
            list[str]: Relative paths (POSIX) of all files changed by distillation.
        """

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
        """Append one concise entry to append-only log.md.

        Appends a structured update log entry (timestamp, type, changed files, reason).
        Maintains an immutable update audit trail.

        Args:
            wiki_root (Path): Absolute path to wiki root directory.
            now (datetime): Current datetime for log entry timestamp.
            changed_files (list[str]): Files modified in this update cycle.
            update_type (str): Type of update ("session_distill" or "code_sync").

        Returns:
            str: Relative path (POSIX) to log.md file.
        """

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
        """Render a Jinja template with deterministic newline policy.

        Renders a Jinja template from the configured template loader (project-local
        or package-default). Ensures output always ends with exactly one newline.

        Args:
            template_name (str): Template filename (e.g., "index.md.j2").
            **kwargs (str): Template context variables.

        Returns:
            str: Rendered template content with trailing newline guarantee.
        """

        template = self.jinja_env.get_template(template_name)
        rendered = template.render(**kwargs)
        if rendered.endswith("\n"):
            return rendered
        return f"{rendered}\n"

    def _render_qmd_yaml(self, project_name: str) -> str:
        """Render qmd YAML with strict stage exclusion contract.

        Generates qmd.yml configuration with collection name and exclusion patterns
        to prevent stage/ and _*.md files from being indexed.

        Args:
            project_name (str): Normalized project identifier.

        Returns:
            str: YAML content for qmd.yml file.
        """

        content = {
            "collection": f"wiki_{project_name}",
            "ignore": ["stage/**", "_*.md"],
        }
        return yaml.safe_dump(content, sort_keys=False)

    def _write_if_changed(self, file_path: Path, content: str) -> bool:
        """Write file content only when changed to keep updates atomic.

        Atomically writes file content only if it differs from existing content.
        Creates parent directories as needed. Used to ensure that unchanged files
        do not trigger downstream update side-effects.

        Args:
            file_path (Path): Target file path (created if missing).
            content (str): New file content.

        Returns:
            bool: True if file was written, False if content was already current.
        """

        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and file_path.read_text(encoding="utf-8") == content:
            return False
        file_path.write_text(content, encoding="utf-8")
        return True
