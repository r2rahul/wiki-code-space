"""qmd integration helpers for indexing and query command conventions."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Iterable

from wiki_engine.graph_bridge import is_excluded_path


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
) -> dict[str, object]:
    """Refresh qmd collection index when qmd CLI is available."""

    assert_non_stage_path(Path("index.md"), exclude_paths)

    qmd_bin = shutil.which("qmd")
    if qmd_bin is None:
        return {
            "status": "skipped",
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
        return {
            "status": "skipped",
            "reason": "qmd index command unavailable or failed",
            "collection": qmd_collection,
            "return_code": process.returncode,
            "stderr": process.stderr.strip(),
        }

    return {
        "status": "ok",
        "collection": qmd_collection,
        "return_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
    }
