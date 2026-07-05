"""End-to-end integration test for wiki_engine update contracts."""

from __future__ import annotations

from pathlib import Path
import re
import shutil

import yaml

from wiki_engine.updater import WikiUpdater


TIMESTAMP_HEADER_PATTERN = re.compile(r"^## \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", re.MULTILINE)


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

    wiki_root = tmp_path / "wiki_code_space"

    # Assert: required artifacts and stage exclusions exist.
    assert (wiki_root / "index.md").exists()
    assert (wiki_root / "log.md").exists()
    assert (wiki_root / "qmd.yml").exists()
    assert (wiki_root / "stage" / ".noindex").exists()
    assert (wiki_root / "stage" / ".qmdexclude").exists()

    # Assert: Karpathy-style index guard rails are present.
    index_text = (wiki_root / "index.md").read_text(encoding="utf-8")
    assert "## First Files To Load" in index_text
    assert "## Never Auto-Read" in index_text
    assert "- stage/" in index_text

    # Assert: qmd ignore policy excludes stage and scaffold files.
    qmd_config = yaml.safe_load((wiki_root / "qmd.yml").read_text(encoding="utf-8"))
    assert qmd_config["collection"] == "wiki_code_space"
    assert "stage/**" in qmd_config["ignore"]
    assert "sessions/_template.md" in qmd_config["ignore"]

    # Assert: front matter keys required by Obsidian contract.
    architecture_text = (wiki_root / "architecture" / "config_params.md").read_text(
        encoding="utf-8"
    )
    architecture_front_matter = _extract_front_matter(architecture_text)
    required_keys = {
        "id",
        "title",
        "type",
        "tags",
        "last_updated",
        "status",
        "source",
    }
    assert required_keys.issubset(set(architecture_front_matter.keys()))
    assert architecture_front_matter["type"] == "architecture"

    # Assert: graph bridge has lexical code reference links.
    assert "Target: src/models/forecasting.py -> run_forecast()" in architecture_text
    assert result.graph_result["bridge_edge_count"] >= 1

    # Assert: append-only log format has timestamp header and update fields.
    log_text = (wiki_root / "log.md").read_text(encoding="utf-8")
    assert TIMESTAMP_HEADER_PATTERN.search(log_text)
    assert "- update_type:" in log_text
    assert "- changed_files:" in log_text
    assert "- reason:" in log_text
    assert "- source: agent" in log_text
