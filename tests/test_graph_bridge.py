"""Tests for wiki-to-code bridge extraction and exclusions."""

from pathlib import Path

from wiki_engine.graph_bridge import collect_bridge_edges, is_excluded_path


def test_is_excluded_path_handles_stage_prefix() -> None:
    """Stage notes must be excluded from graph bridge extraction."""

    assert is_excluded_path(Path("stage/plan/roadmap.md"), ["stage/**"])
    assert not is_excluded_path(Path("architecture/config_params.md"), ["stage/**"])


def test_collect_bridge_edges_extracts_code_reference(tmp_path: Path) -> None:
    """Bridge extractor should parse lexical path+symbol references."""

    wiki_root = tmp_path / "wiki_code_space"
    architecture_dir = wiki_root / "architecture"
    architecture_dir.mkdir(parents=True)
    note_path = architecture_dir / "config_params.md"
    note_path.write_text(
        "Target: src/models/forecasting.py -> run_forecast()\n",
        encoding="utf-8",
    )

    edges = collect_bridge_edges(wiki_root=wiki_root, exclude_paths=["stage/**"])

    assert len(edges) == 1
    assert edges[0].code_path == "src/models/forecasting.py"
    assert edges[0].symbol_name == "run_forecast()"
