"""Install wiki_engine skills and harness-specific instructions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment

from wiki_engine.naming import normalize_project_name


HARNESS_PATHS = {
    "copilot": {
        "project_instruction": Path(".github/copilot-instructions.md"),
        "project_skills": Path(".github/skills"),
    },
    "codex": {
        "project_instruction": Path("AGENTS.md"),
        "project_skills": Path(".agents/skills"),
    },
    "claude": {
        "project_instruction": Path("CLAUDE.md"),
        "project_skills": Path(".claude/skills"),
    },
    "gemini": {
        "project_instruction": Path("GEMINI.md"),
        "project_skills": Path(".gemini/skills"),
    },
    "cursor": {
        "project_instruction": Path(".cursor/rules/wiki-wspace.mdc"),
        "project_skills": Path(".cursor/skills"),
    },
}


@dataclass(frozen=True)
class AgentInstallResult:
    """Result payload for one harness skill installation."""

    agent_name: str
    instruction_path: Path
    skill_paths: tuple[Path, Path]
    refresh_command: str
    query_command: str
    changed_files: list[str]


def project_command_suffix(project_name: str) -> str:
    """Build a stable command suffix from the compact project name."""

    return normalize_project_name(project_name)


def project_skill_names(project_name: str) -> tuple[str, str]:
    """Return specification-compliant refresh and query skill names."""

    suffix = project_command_suffix(project_name)
    refresh_prefix = "wiki-ref-"
    query_prefix = "wiki-query-"
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
) -> AgentInstallResult:
    """Install two project Agent Skills and a harness instruction block."""

    if agent_name not in HARNESS_PATHS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    harness_paths = HARNESS_PATHS[agent_name]
    instruction_path = repo_root / harness_paths["project_instruction"]
    skills_root = repo_root / harness_paths["project_skills"]

    project_name = normalize_project_name(project_name)
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

    changed_files: list[str] = []
    generated_files = {
        refresh_skill_path / "SKILL.md": f"{refresh_content.rstrip()}\n",
        workflow_reference_path: f"{workflow_content.rstrip()}\n",
        query_skill_path / "SKILL.md": f"{query_content.rstrip()}\n",
    }
    for file_path, content in generated_files.items():
        if _write_if_changed(file_path, content):
            changed_files.append(str(file_path))

    if agent_name == "cursor":
        # Cursor uses a package-managed always-apply rule file; rewrite it whole
        # so frontmatter stays valid and other `.cursor/rules/*.mdc` files remain untouched.
        cursor_instruction = jinja_env.get_template(
            "agent_wiki_install_cursor.md.j2"
        ).render(**template_context)
        if _write_if_changed(instruction_path, f"{cursor_instruction.rstrip()}\n"):
            changed_files.append(str(instruction_path))
    else:
        marker_slug = project_command_suffix(project_name)
        begin_marker = f"<!-- wiki-wspace:{marker_slug}:start -->"
        end_marker = f"<!-- wiki-wspace:{marker_slug}:end -->"
        instruction_block = jinja_env.get_template("agent_wiki_install.md.j2").render(
            **template_context,
            agent_name=agent_name,
            begin_marker=begin_marker,
            end_marker=end_marker,
        )
        existing_content = (
            instruction_path.read_text(encoding="utf-8")
            if instruction_path.exists()
            else ""
        )
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
        instruction_path=instruction_path,
        skill_paths=(refresh_skill_path, query_skill_path),
        refresh_command=f"/{refresh_name}",
        query_command=f"/{query_name}",
        changed_files=changed_files,
    )
