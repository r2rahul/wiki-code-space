"""qmd integration helpers for indexing and query command conventions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable

from wiki_engine.graph_bridge import is_excluded_path

LOGGER = logging.getLogger(__name__)


def assert_non_stage_path(file_path: Path, exclude_paths: Iterable[str]) -> None:
    """Raise when a caller attempts to index a path from excluded stage folders."""

    if is_excluded_path(file_path=file_path, exclude_paths=exclude_paths):
        raise ValueError(f"Refusing stage path for qmd operation: {file_path}")


def build_qmd_query_command(
    query_text: str,
    qmd_collection: str,
    result_count: int = 10,
) -> list[str]:
    """Build qmd query command with required collection and output options."""

    return [
        "qmd",
        "query",
        query_text,
        "-c",
        qmd_collection,
        "--json",
        "-n",
        str(result_count),
    ]


def refresh_qmd_index(
    wiki_root: Path,
    qmd_collection: str,
    exclude_paths: Iterable[str],
    qmd_enabled: bool = True,
) -> dict[str, object]:
    """Refresh qmd collection index when qmd CLI is available."""

    if not qmd_enabled:
        return {
            "status": "disabled",
            "reason": "qmd indexing disabled by config",
            "collection": qmd_collection,
        }

    assert_non_stage_path(Path("index.md"), exclude_paths)

    qmd_bin = shutil.which("qmd")
    if qmd_bin is None:
        LOGGER.warning("qmd is missing; using markdown-based wiki search fallback")
        return {
            "status": "fallback",
            "reason": "qmd CLI not installed",
            "collection": qmd_collection,
        }

    command = [
        qmd_bin,
        "index",
        str(wiki_root),
        "-c",
        qmd_collection,
    ]
    process = subprocess.run(command, check=False, capture_output=True, text=True)
    if process.returncode != 0:
        LOGGER.warning(
            "qmd index failed; using markdown-based wiki search fallback: %s",
            process.stderr.strip() or process.stdout.strip(),
        )
        return {
            "status": "fallback",
            "reason": "qmd index command unavailable or failed",
            "collection": qmd_collection,
            "return_code": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
        }

    return {
        "status": "ok",
        "collection": qmd_collection,
        "return_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }


def search_wiki(
    query_text: str,
    wiki_root: Path,
    qmd_collection: str,
    exclude_paths: Iterable[str],
    result_count: int = 10,
    qmd_enabled: bool = True,
) -> dict[str, Any]:
    """Search wiki content with qmd first and deterministic markdown fallback."""

    if qmd_enabled:
        qmd_result = _search_wiki_with_qmd(
            query_text=query_text,
            qmd_collection=qmd_collection,
            result_count=result_count,
        )
        if qmd_result["status"] == "ok":
            return qmd_result
    else:
        qmd_result = {
            "status": "disabled",
            "reason": "qmd search disabled by config",
            "collection": qmd_collection,
        }

    fallback_results = search_wiki_markdown(
        query_text=query_text,
        wiki_root=wiki_root,
        exclude_paths=exclude_paths,
        result_count=result_count,
    )
    return {
        "status": "fallback",
        "backend": "markdown",
        "collection": qmd_collection,
        "reason": qmd_result["reason"],
        "qmd_result": qmd_result,
        "results": fallback_results,
    }


def search_wiki_markdown(
    query_text: str,
    wiki_root: Path,
    exclude_paths: Iterable[str],
    result_count: int = 10,
) -> list[dict[str, Any]]:
    """Search markdown files without reading excluded wiki paths."""

    query_normalized = query_text.casefold()
    results: list[dict[str, Any]] = []

    if not query_normalized.strip() or not wiki_root.exists():
        return results

    for markdown_path in sorted(wiki_root.rglob("*.md")):
        relative_path = markdown_path.relative_to(wiki_root)
        if is_excluded_path(file_path=relative_path, exclude_paths=exclude_paths):
            continue

        line_matches: list[tuple[int, str]] = []
        score = 0
        for line_number, line_text in enumerate(
            markdown_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            line_score = line_text.casefold().count(query_normalized)
            if line_score:
                score += line_score
                line_matches.append((line_number, line_text.strip()))

        if score:
            first_line, first_snippet = line_matches[0]
            results.append(
                {
                    "path": relative_path.as_posix(),
                    "line": first_line,
                    "score": score,
                    "snippet": first_snippet,
                }
            )

    results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    return results[:result_count]


def _search_wiki_with_qmd(
    query_text: str,
    qmd_collection: str,
    result_count: int,
) -> dict[str, Any]:
    """Run qmd query and normalize success/fallback metadata."""

    qmd_bin = shutil.which("qmd")
    if qmd_bin is None:
        LOGGER.warning("qmd is missing; using markdown-based wiki search fallback")
        return {
            "status": "fallback",
            "backend": "qmd",
            "reason": "qmd CLI not installed",
            "collection": qmd_collection,
        }

    command = build_qmd_query_command(
        query_text=query_text,
        qmd_collection=qmd_collection,
        result_count=result_count,
    )
    command[0] = qmd_bin
    process = subprocess.run(command, check=False, capture_output=True, text=True)
    if process.returncode != 0:
        LOGGER.warning(
            "qmd query failed; using markdown-based wiki search fallback: %s",
            process.stderr.strip() or process.stdout.strip(),
        )
        return {
            "status": "fallback",
            "backend": "qmd",
            "reason": "qmd query command unavailable or failed",
            "collection": qmd_collection,
            "return_code": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
        }

    parsed_stdout: Any
    try:
        parsed_stdout = json.loads(process.stdout)
    except json.JSONDecodeError:
        parsed_stdout = process.stdout.strip()

    return {
        "status": "ok",
        "backend": "qmd",
        "collection": qmd_collection,
        "return_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "results": parsed_stdout,
    }
