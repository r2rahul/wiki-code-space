"""End-to-end integration test for wiki_engine update contracts."""

from __future__ import annotations

from pathlib import Path
import re
import shutil

import yaml

from wiki_engine.updater import WikiUpdater


DATE_HEADER_PATTERN = re.compile(r"^## \d{4}-\d{2}-\d{2}$", re.MULTILINE)


def _extract_front_matter(markdown_text: str) -> dict[str, object]:
    """Extract and parse YAML front matter from a markdown note."""

    if not markdown_text.startswith("---\n"):
        raise ValueError("Missing front matter start delimiter")

    _, front_matter, _ = markdown_text.split("---\n", maxsplit=2)
    parsed = yaml.safe_load(front_matter)
    if not isinstance(parsed, dict):
        raise ValueError("Front matter is not a mapping")
    return parsed


def test_update_contracts_end_to_end(tmp_path: Path) -> None:
    """Run full update workflow and validate generated wiki contract files."""

    project_root = Path(__file__).resolve().parents[1]

    # Arrange isolated repo scaffold with real package templates and config.
    (tmp_path / "wiki_engine").mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        project_root / "wiki_engine" / "templates",
        tmp_path / "wiki_engine" / "templates",
        dirs_exist_ok=True,
    )
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        project_root / "config" / "wiki_engine.yaml",
        tmp_path / "config" / "wiki_engine.yaml",
    )

    updater = WikiUpdater(
        repo_root=tmp_path,
        config_path=tmp_path / "config" / "wiki_engine.yaml",
    )

    # Act: one coherent update run.
    result = updater.update(project_override="code_space")

    wiki_root = tmp_path / "wiki_coce"

    # Assert: required artifacts and stage exclusions exist.
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "qmd.yml").exists()
    assert (wiki_root / "stage" / ".noindex").exists()
    assert (wiki_root / "stage" / ".qmdexclude").exists()

    # Assert: OKF root index and Karpathy-style guard rails are present.
    index_text = (wiki_root / "index.md").read_text(encoding="utf-8")
    assert index_text.startswith("---\nokf_version: \"0.2\"\n---\n")
    assert "# First Files To Load" in index_text
    assert "# Never Auto-Read" in index_text
    assert "`stage/`" in index_text

    # Assert: qmd ignore policy excludes stage and utility files.
    qmd_config = yaml.safe_load((wiki_root / "qmd.yml").read_text(encoding="utf-8"))
    assert qmd_config["collection"] == "wiki_coce"
    assert "stage/**" in qmd_config["ignore"]
    assert "_*.md" in qmd_config["ignore"]

    # Assert: first update does not create placeholder semantic notes.
    assert not (wiki_root / "sessions" / "_template.md").exists()
    assert not (wiki_root / "architecture" / "config_params.md").exists()
    assert not (wiki_root / "qa" / "business.md").exists()
    assert not (wiki_root / "qa" / "technical.md").exists()
    assert not (wiki_root / "decisions" / "adr-placeholder.md").exists()
    assert not (wiki_root / "glossary" / "terms.md").exists()

    session_path = wiki_root / "sessions" / "2026-07-05-config-routing.md"
    session_path.write_text(
        (
            "---\n"
            "type: session\n"
            "title: Session Config Routing\n"
            "description: Distillation fixture for config routing.\n"
            "tags: [session, distilled]\n"
            "status: stable\n"
            "generated: { by: wiki_wspace/agent, at: 2026-07-05T00:00:00Z }\n"
            "---\n\n"
            "# Reusable Knowledge\n"
            "- Config Parameter: volatility_penalty in config/config.yaml; "
            "Target: src/models/forecasting.py -> run_forecast()\n\n"
            "# Distillation Status\n"
            "- [ ] Applied to permanent note(s)\n"
            "- [ ] Logged in log.md\n"
        ),
        encoding="utf-8",
    )

    result = updater.update(project_override="code_space")

    # Assert: OKF v0.2 front matter contract for distilled concept notes.
    architecture_path = wiki_root / "architecture" / "config_params.md"
    architecture_text = architecture_path.read_text(encoding="utf-8")
    architecture_front_matter = _extract_front_matter(architecture_text)
    required_keys = {
        "type",
        "title",
        "description",
        "tags",
        "status",
        "generated",
    }
    assert required_keys.issubset(set(architecture_front_matter.keys()))
    assert architecture_front_matter["type"] == "architecture"
    assert architecture_front_matter["status"] == "stable"
    generated = architecture_front_matter["generated"]
    assert isinstance(generated, dict)
    assert generated["by"] == "wiki_wspace/agent"
    assert "at" in generated

    # Assert: graph bridge has lexical code reference links.
    assert "Target: src/models/forecasting.py -> run_forecast()" in architecture_text
    assert result.graph_result["bridge_edge_count"] >= 1

    # Assert: a later update does not re-append the same distilled snippet.
    first_architecture_text = architecture_text
    updater.update(project_override="code_space")
    second_architecture_text = architecture_path.read_text(encoding="utf-8")
    assert second_architecture_text == first_architecture_text
    assert second_architecture_text.count("volatility_penalty") == 1

    # Assert: OKF log uses date headings and newest-first update bullets.
    log_text = (wiki_root / "log.md").read_text(encoding="utf-8")
    assert DATE_HEADER_PATTERN.search(log_text)
    assert "* **Update**:" in log_text
    assert "by agent" in log_text
    assert "changed_files:" in log_text
    assert not any("T" in heading for heading in DATE_HEADER_PATTERN.findall(log_text))
