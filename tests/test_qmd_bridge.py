"""Validation tests for qmd command and stage exclusion contract."""

from types import SimpleNamespace
import logging
from pathlib import Path

import pytest

from wiki_engine.qmd_bridge import (
    assert_non_stage_path,
    build_qmd_query_command,
    refresh_qmd_index,
    search_wiki,
    search_wiki_markdown,
)


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


def test_search_wiki_uses_qmd_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """qmd search should be the preferred backend when the command succeeds."""

    def fake_run(
        command: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> SimpleNamespace:
        assert command == [
            "/usr/bin/qmd",
            "query",
            "volatility",
            "-c",
            "wiki_code_space",
            "--json",
            "-n",
            "2",
        ]
        assert not check
        assert capture_output
        assert text
        return SimpleNamespace(returncode=0, stdout='[{"path":"index.md"}]', stderr="")

    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: "/usr/bin/qmd")
    monkeypatch.setattr("wiki_engine.qmd_bridge.subprocess.run", fake_run)

    result = search_wiki(
        query_text="volatility",
        wiki_root=Path("wiki_code_space"),
        qmd_collection="wiki_code_space",
        exclude_paths=["stage/**"],
        result_count=2,
    )

    assert result["status"] == "ok"
    assert result["backend"] == "qmd"
    assert result["results"] == [{"path": "index.md"}]


def test_refresh_qmd_index_missing_falls_back_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Missing qmd should report fallback and warn operators."""

    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: None)
    with caplog.at_level(logging.WARNING):
        result = refresh_qmd_index(
            wiki_root=tmp_path,
            qmd_collection="wiki_code_space",
            exclude_paths=["stage/**"],
        )

    assert result["status"] == "fallback"
    assert result["reason"] == "qmd CLI not installed"
    assert "qmd is missing" in caplog.text


def test_refresh_qmd_index_failure_falls_back_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Unhealthy qmd should not block wiki updates."""

    monkeypatch.setattr("wiki_engine.qmd_bridge.shutil.which", lambda _: "/usr/bin/qmd")
    monkeypatch.setattr(
        "wiki_engine.qmd_bridge.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="sqlite unavailable",
        ),
    )

    with caplog.at_level(logging.WARNING):
        result = refresh_qmd_index(
            wiki_root=tmp_path,
            qmd_collection="wiki_code_space",
            exclude_paths=["stage/**"],
        )

    assert result["status"] == "fallback"
    assert result["return_code"] == 1
    assert result["stderr"] == "sqlite unavailable"
    assert "qmd index failed" in caplog.text


def test_search_wiki_markdown_excludes_stage(tmp_path: Path) -> None:
    """Markdown fallback must not read or return stage matches."""

    wiki_root = tmp_path / "wiki_code_space"
    wiki_root.mkdir()
    (wiki_root / "index.md").write_text(
        "Public volatility context\n",
        encoding="utf-8",
    )
    stage_dir = wiki_root / "stage"
    stage_dir.mkdir()
    (stage_dir / "draft.md").write_text(
        "volatility secret draft\n",
        encoding="utf-8",
    )

    results = search_wiki_markdown(
        query_text="volatility",
        wiki_root=wiki_root,
        exclude_paths=["stage/**"],
        result_count=10,
    )

    assert [result["path"] for result in results] == ["index.md"]


def test_search_wiki_qmd_disabled_uses_markdown(tmp_path: Path) -> None:
    """Config-disabled qmd should use markdown fallback directly."""

    wiki_root = tmp_path / "wiki_code_space"
    wiki_root.mkdir()
    (wiki_root / "index.md").write_text("qmd fallback note\n", encoding="utf-8")

    result = search_wiki(
        query_text="fallback",
        wiki_root=wiki_root,
        qmd_collection="wiki_code_space",
        exclude_paths=["stage/**"],
        qmd_enabled=False,
    )

    assert result["status"] == "fallback"
    assert result["backend"] == "markdown"
    assert result["reason"] == "qmd search disabled by config"
    assert result["results"][0]["path"] == "index.md"
