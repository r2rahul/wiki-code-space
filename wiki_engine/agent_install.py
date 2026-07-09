"""Install assistant-specific wiki maintenance instructions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment


AGENT_INSTRUCTION_PATHS = {
    "codex": Path("AGENTS.md"),
    "vscode": Path(".github/copilot-instructions.md"),
    "claude": Path("CLAUDE.md"),
    "gemini": Path("GEMINI.md"),
}


@dataclass(frozen=True)
class AgentInstallResult:
    """Result payload for one agent instruction installation."""

    agent_name: str
    instruction_path: Path
    guide_path: Path
    bootstrap_path: Path
    changed_files: list[str]


def _write_if_changed(file_path: Path, content: str) -> bool:
    """Write content only when it changes.

    Conditionally writes file content to disk, avoiding unnecessary writes
    when content is unchanged. Creates parent directories as needed.

    :param file_path: Target file path where content will be written.
    :type file_path: pathlib.Path
    :param content: File content to write.
    :type content: str
    :return: True if file was written (content changed or file did not exist),
             False if file exists with identical content.
    :rtype: bool
    """

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
    """Replace or append a deterministic marked instruction block.

    Merges new content into an existing text block by locating begin and end
    markers. If markers are found, the content between them is replaced.
    Otherwise, the new content is appended.

    :param existing_content: Existing file or string content.
    :type existing_content: str
    :param block_content: New content to insert or replace.
    :type block_content: str
    :param begin_marker: String marker indicating block start (e.g., HTML comment).
    :type begin_marker: str
    :param end_marker: String marker indicating block end (e.g., HTML comment).
    :type end_marker: str
    :return: Merged content with new block inserted or appended. Content is
             stripped of trailing whitespace before markers.
    :rtype: str
    """

    if begin_marker in existing_content and end_marker in existing_content:
        before, rest = existing_content.split(begin_marker, maxsplit=1)
        _, after = rest.split(end_marker, maxsplit=1)
        return f"{before.rstrip()}\n\n{block_content.strip()}\n{after}"

    separator = "\n\n" if existing_content.rstrip() else ""
    return f"{existing_content.rstrip()}{separator}{block_content.strip()}\n"


def install_agent_instructions(
    repo_root: Path,
    project_name: str,
    agent_name: str,
    jinja_env: Environment,
) -> AgentInstallResult:
    """Install one agent instruction file plus shared wiki prompt guides.

    Installs or updates AI agent-specific instruction files and shared wiki
    maintenance templates. Renders Jinja2 templates and merges instruction
    blocks into agent configuration files using deterministic markers.
    Supports multiple agent types: codex, vscode, claude, gemini.

    :param repo_root: Root directory of the repository.
    :type repo_root: pathlib.Path
    :param project_name: Name of the project (used in wiki folder paths and
                         template rendering).
    :type project_name: str
    :param agent_name: Target agent identifier (one of 'codex', 'vscode',
                       'claude', 'gemini').
    :type agent_name: str
    :param jinja_env: Jinja2 environment configured with template loaders.
    :type jinja_env: jinja2.Environment
    :return: Installation result containing agent name, file paths updated,
             and list of changed files.
    :rtype: AgentInstallResult
    :raises ValueError: If agent_name is not in AGENT_INSTRUCTION_PATHS.
    """

    if agent_name not in AGENT_INSTRUCTION_PATHS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    wiki_root = f"wiki_{project_name}"
    prompt_dir = Path(wiki_root) / "templates"
    guide_path = prompt_dir / "llm_wiki_workflow_guide.md"
    bootstrap_path = prompt_dir / "wiki_first_init_bootstrap.md"
    instruction_path = AGENT_INSTRUCTION_PATHS[agent_name]
    begin_marker = "<!-- wiki-engine:start -->"
    end_marker = "<!-- wiki-engine:end -->"

    guide_content = jinja_env.get_template("llm_wiki_workflow_guide.md").render(
        project_name=project_name,
        wiki_root=wiki_root,
    )
    bootstrap_prompt_content = jinja_env.get_template(
        "wiki_first_init_bootstrap.md"
    ).render(
        project_name=project_name,
        wiki_root=wiki_root,
    )
    instruction_block = jinja_env.get_template("agent_wiki_install.md.j2").render(
        project_name=project_name,
        wiki_root=wiki_root,
        agent_name=agent_name,
        guide_path=guide_path.as_posix(),
        bootstrap_path=bootstrap_path.as_posix(),
        begin_marker=begin_marker,
        end_marker=end_marker,
    )

    changed_files: list[str] = []
    absolute_guide_path = repo_root / guide_path
    if _write_if_changed(absolute_guide_path, f"{guide_content.rstrip()}\n"):
        changed_files.append(guide_path.as_posix())

    absolute_bootstrap_path = repo_root / bootstrap_path
    if _write_if_changed(
        absolute_bootstrap_path,
        f"{bootstrap_prompt_content.rstrip()}\n",
    ):
        changed_files.append(bootstrap_path.as_posix())

    absolute_instruction_path = repo_root / instruction_path
    existing_content = (
        absolute_instruction_path.read_text(encoding="utf-8")
        if absolute_instruction_path.exists()
        else ""
    )
    merged_content = _merge_marked_block(
        existing_content=existing_content,
        block_content=instruction_block,
        begin_marker=begin_marker,
        end_marker=end_marker,
    )
    if _write_if_changed(absolute_instruction_path, merged_content):
        changed_files.append(instruction_path.as_posix())

    return AgentInstallResult(
        agent_name=agent_name,
        instruction_path=instruction_path,
        guide_path=guide_path,
        bootstrap_path=bootstrap_path,
        changed_files=changed_files,
    )
