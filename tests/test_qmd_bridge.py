"""Validation tests for qmd command and stage exclusion contract."""

from pathlib import Path

import pytest

from wiki_engine.qmd_bridge import assert_non_stage_path, build_qmd_query_command


def test_build_qmd_query_command_uses_required_flags() -> None:
    """qmd query must include collection, json output, and result count."""

    command = build_qmd_query_command(
        query_text="why volatility_penalty changed",
        qmd_collection="wiki_code_space",
        result_count=10,
    )

    assert command == [
        "qmd",
        "query",
        "why volatility_penalty changed",
        "-c",
        "wiki_code_space",
        "--json",
        "-n",
        "10",
    ]


def test_assert_non_stage_path_blocks_stage_paths() -> None:
    """qmd bridge must reject stage paths from indexing actions."""

    with pytest.raises(ValueError):
        assert_non_stage_path(
            file_path=Path("stage/spec/draft.md"),
            exclude_paths=["stage/**"],
        )
