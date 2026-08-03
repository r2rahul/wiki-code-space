"""Install wiki_engine skills and harness-specific instructions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from jinja2 import Environment


HARNESS_PATHS = {
    "copilot": {
        "project_instruction": Path(".github/copilot-instructions.md"),
        "project_skills": Path(".agents/skills"),
        "user_instruction": Path(".copilot/copilot-instructions.md"),
        "user_skills": Path(".agents/skills"),
    },
    "codex": {
        "project_instruction": Path("AGENTS.md"),
        "project_skills": Path(".agents/skills"),
        "user_instruction": Path(".codex/AGENTS.md"),
        "user_skills": Path(".codex/skills"),
    },
    "claude": {
        "project_instruction": Path("CLAUDE.md"),
        "project_skills": Path(".claude/skills"),
        "user_instruction": Path(".claude/CLAUDE.md"),
        "user_skills": Path(".claude/skills"),
    },
    "gemini": {
        "project_instruction": Path("GEMINI.md"),
        "project_skills": Path(".gemini/skills"),
        "user_instruction": Path(".gemini/GEMINI.md"),
        "user_skills": Path(".gemini/skills"),
    },
}


@dataclass(frozen=True)
class AgentInstallResult:
    """Result payload for one harness skill installation."""

    agent_name: str
    scope: str
    instruction_path: Path
    skill_paths: tuple[Path, Path]
    refresh_command: str
    query_command: str
    changed_files: list[str]


def project_command_suffix(project_name: str) -> str:
    """Build a stable command suffix from the first two and last two words."""

    words = re.findall(r"[a-z0-9]+", project_name.casefold())
    if not words:
        raise ValueError("Project name must contain at least one letter or number")
    selected_words = words if len(words) <= 4 else words[:2] + words[-2:]
    return "-".join(selected_words)


def project_skill_names(project_name: str) -> tuple[str, str]:
    """Return specification-compliant refresh and query skill names."""

    suffix = project_command_suffix(project_name)
    refresh_prefix = "wiki-ref-"
    query_prefix = "wiki-query-"
    suffix_limit = 64 - max(len(refresh_prefix), len(query_prefix))
    suffix = suffix[:suffix_limit].rstrip("-")
    refresh_name = f"{refresh_prefix}{suffix}"
    query_name = f"{query_prefix}{suffix}"
    return refresh_name, query_name


def _write_if_changed(file_path: Path, content: str) -> bool:
    """Write content only when it changes."""

    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists() and file_path.read_text(encoding="utf-8") == content:
        return False
    file_path.write_text(content, encoding="utf-8")
    return True


def _merge_marked_block(
    existing_content: str,
    block_content: str,
    begin_marker: str,
    end_marker: str,
) -> str:
    """Replace or append one deterministic marked instruction block."""

    if begin_marker in existing_content and end_marker in existing_content:
        before, rest = existing_content.split(begin_marker, maxsplit=1)
        _, after = rest.split(end_marker, maxsplit=1)
        prefix = f"{before.rstrip()}\n\n" if before.rstrip() else ""
        return f"{prefix}{block_content.strip()}\n{after.lstrip()}"

    separator = "\n\n" if existing_content.rstrip() else ""
    return f"{existing_content.rstrip()}{separator}{block_content.strip()}\n"


def install_agent_instructions(
    repo_root: Path,
    project_name: str,
    agent_name: str,
    jinja_env: Environment,
    *,
    user: bool = False,
    user_home: Path | None = None,
) -> AgentInstallResult:
    """Install two Agent Skills and a concise harness instruction block.

    Project installation is the default. ``user=True`` writes only beneath the
    supplied user home (or ``Path.home()``) and never modifies the project.
    """

    if agent_name not in HARNESS_PATHS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    harness_paths = HARNESS_PATHS[agent_name]
    scope_root = (user_home or Path.home()) if user else repo_root
    scope_key = "user" if user else "project"
    instruction_path = scope_root / harness_paths[f"{scope_key}_instruction"]
    skills_root = scope_root / harness_paths[f"{scope_key}_skills"]

    refresh_name, query_name = project_skill_names(project_name)
    wiki_root = f"wiki_{project_name}"
    refresh_skill_path = skills_root / refresh_name
    query_skill_path = skills_root / query_name
    workflow_reference_path = refresh_skill_path / "references" / "wiki-workflow.md"

    template_context = {
        "project_name": project_name,
        "wiki_root": wiki_root,
        "refresh_name": refresh_name,
        "query_name": query_name,
        "refresh_command": f"/{refresh_name}",
        "query_command": f"/{query_name}",
    }
    refresh_content = jinja_env.get_template("wiki_refresh_skill.md.j2").render(
        **template_context
    )
    query_content = jinja_env.get_template("wiki_query_skill.md.j2").render(
        **template_context
    )
    workflow_content = jinja_env.get_template("llm_wiki_workflow_guide.md").render(
        project_name=project_name,
        wiki_root=wiki_root,
    )

    marker_slug = project_command_suffix(project_name)
    begin_marker = f"<!-- wiki-engine:{marker_slug}:start -->"
    end_marker = f"<!-- wiki-engine:{marker_slug}:end -->"
    instruction_block = jinja_env.get_template("agent_wiki_install.md.j2").render(
        **template_context,
        agent_name=agent_name,
        begin_marker=begin_marker,
        end_marker=end_marker,
    )

    changed_files: list[str] = []
    generated_files = {
        refresh_skill_path / "SKILL.md": f"{refresh_content.rstrip()}\n",
        workflow_reference_path: f"{workflow_content.rstrip()}\n",
        query_skill_path / "SKILL.md": f"{query_content.rstrip()}\n",
    }
    for file_path, content in generated_files.items():
        if _write_if_changed(file_path, content):
            changed_files.append(str(file_path))

    existing_content = (
        instruction_path.read_text(encoding="utf-8")
        if instruction_path.exists()
        else ""
    )
    legacy_begin_marker = "<!-- wiki-engine:start -->"
    legacy_end_marker = "<!-- wiki-engine:end -->"
    if (
        legacy_begin_marker in existing_content
        and legacy_end_marker in existing_content
    ):
        begin_marker = legacy_begin_marker
        end_marker = legacy_end_marker
    merged_content = _merge_marked_block(
        existing_content=existing_content,
        block_content=instruction_block,
        begin_marker=begin_marker,
        end_marker=end_marker,
    )
    if _write_if_changed(instruction_path, merged_content):
        changed_files.append(str(instruction_path))

    return AgentInstallResult(
        agent_name=agent_name,
        scope=scope_key,
        instruction_path=instruction_path,
        skill_paths=(refresh_skill_path, query_skill_path),
        refresh_command=f"/{refresh_name}",
        query_command=f"/{query_name}",
        changed_files=changed_files,
    )
