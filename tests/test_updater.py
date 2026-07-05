"""Integration-style tests for coherent updater behavior."""

from pathlib import Path

from wiki_engine.updater import WikiUpdater


def write_minimal_templates(repo_root: Path) -> None:
    """Create minimal templates required for updater rendering in tests."""

    template_dir = repo_root / "wiki_engine" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "index.md.j2").write_text("# {{ wiki_root }}\n", encoding="utf-8")
    (template_dir / "log.md.j2").write_text("# Update Log\n", encoding="utf-8")
    (template_dir / "session_template.md.j2").write_text("# Session\n", encoding="utf-8")
    (template_dir / "note_template.md.j2").write_text("{{ body }}\n", encoding="utf-8")
    (template_dir / "wiki_auto_refresh.md.j2").write_text(
        "## wiki auto refresh\n"
        "wiki_{{ project_name }}\n",
        encoding="utf-8",
    )
    (template_dir / "agent_wiki_install.md.j2").write_text(
        "{{ begin_marker }}\n"
        "## wiki maintenance\n"
        "wiki_{{ project_name }} {{ skill_path }}\n"
        "{{ end_marker }}\n",
        encoding="utf-8",
    )
    (template_dir / "llm_wiki_workflow_guide.md.j2").write_text(
        "Guide for wiki_{{ project_name }}\n",
        encoding="utf-8",
    )


def test_update_creates_required_wiki_files(tmp_path: Path) -> None:
    """Updater should create the mandatory wiki scaffold and sentinels."""

    repo_root = tmp_path
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "wiki_engine.yaml"
    config_path.write_text(
        (
            "project_name: code_space\n"
            "wiki_root: wiki_code_space\n"
            "qmd_collection: wiki_code_space\n"
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

    write_minimal_templates(repo_root=repo_root)

    updater = WikiUpdater(repo_root=repo_root, config_path=config_path)
    result = updater.update(project_override="code_space")

    wiki_root = repo_root / "wiki_code_space"
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "qmd.yml").exists()
    assert (wiki_root / "stage" / ".noindex").exists()
    assert (wiki_root / "stage" / ".qmdexclude").exists()
    assert (repo_root / "AGENTS.md").exists()
    assert (repo_root / "CLAUDE.md").exists()
    assert (
        repo_root / ".ai" / "wiki_code_space" / "llm_wiki_workflow_guide.md"
    ).exists()
    assert "wiki_code_space" in (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "wiki_code_space" in (repo_root / "CLAUDE.md").read_text(encoding="utf-8")
    assert any(path.endswith("log.md") for path in result.changed_files)


def test_update_replaces_marked_blocks_in_existing_agent_files(
    tmp_path: Path,
) -> None:
    """Updater should replace generated agent blocks in existing agent files."""

    repo_root = tmp_path
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "wiki_engine.yaml"
    config_path.write_text(
        (
            "project_name: code_space\n"
            "wiki_root: wiki_code_space\n"
            "qmd_collection: wiki_code_space\n"
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

    write_minimal_templates(repo_root=repo_root)
    (repo_root / "AGENTS.md").write_text(
        "<!-- wiki-engine:start -->\n"
        "old generated content\n"
        "<!-- wiki-engine:end -->\n",
        encoding="utf-8",
    )
    (repo_root / "CLAUDE.md").write_text(
        "# Handwritten heading\n",
        encoding="utf-8",
    )

    updater = WikiUpdater(repo_root=repo_root, config_path=config_path)
    updater.update(project_override="code_space")

    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    claude_text = (repo_root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "old generated content" not in agents_text
    assert "wiki_code_space" in agents_text
    assert "# Handwritten heading" in claude_text
    assert "wiki_code_space" in claude_text
