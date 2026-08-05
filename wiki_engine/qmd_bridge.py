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
QMD_MISSING_MESSAGE = "qmd is not installed; defaulting to Markdown index-based search"


def _qmd_process_reports_missing(process: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a discovered qmd launcher reports a missing npm package."""

    combined_output = f"{process.stderr}\n{process.stdout}".casefold()
    launcher_missing_markers = (
        "cannot find module",
        "cannot find package",
        "module_not_found",
        "could not determine executable to run",
    )
    if any(marker in combined_output for marker in launcher_missing_markers):
        return True

    npm_error = "npm error" in combined_output or "npm err!" in combined_output
    npm_missing_markers = (
        "code e404",
        "code enoent",
        "404 not found",
    )
    return npm_error and any(
        marker in combined_output for marker in npm_missing_markers
    )


def _qmd_collection_already_exists(process: subprocess.CompletedProcess[str]) -> bool:
    """Return True when qmd reports an existing collection as a command failure.

    Helper to detect idempotency: qmd collection add fails with a known message
    when the collection already exists. This distinguishes transient failures
    from successful idempotent registration.

    Args:
        process (subprocess.CompletedProcess[str]): Completed qmd subprocess result.

    Returns:
        bool: True if stdout/stderr contain both "already exists" and "collection"
            (case-insensitive), False otherwise.
    """

    combined_output = f"{process.stderr}\n{process.stdout}".casefold()
    return "already exists" in combined_output and "collection" in combined_output


def assert_non_stage_path(file_path: Path, exclude_paths: Iterable[str]) -> None:
    """Raise when a caller attempts to index a path from excluded stage folders.

    Enforces the invariant that stage paths are never indexed. Used as a guard
    in public qmd functions to prevent accidental exposure of draft/confidential content.

    Args:
        file_path (Path): File path to validate.
        exclude_paths (Iterable[str]): Glob patterns for excluded paths (e.g., ["stage/**"]).

    Raises:
        ValueError: If file_path matches any exclude pattern.
    """

    if is_excluded_path(file_path=file_path, exclude_paths=exclude_paths):
        raise ValueError(f"Refusing stage path for qmd operation: {file_path}")


def build_qmd_query_command(
    query_text: str,
    qmd_collection: str,
    result_count: int = 10,
) -> list[str]:
    """Build qmd query command with required collection and output options.

    Constructs a shell command list for the qmd CLI query subcommand.

    Args:
        query_text (str): Search query string.
        qmd_collection (str): Registered qmd collection name.
        result_count (int): Maximum results to return. Defaults to 10.

    Returns:
        list[str]: Command list for subprocess.run() [qmd, query, ...].
    """

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


def build_qmd_collection_add_command(
    wiki_root: Path,
    qmd_collection: str,
) -> list[str]:
    """Build qmd collection registration command for a wiki folder.

    Constructs a shell command list for the qmd CLI collection add subcommand.

    Args:
        wiki_root (Path): Absolute path to wiki root directory to register.
        qmd_collection (str): Canonical name for the collection in qmd.

    Returns:
        list[str]: Command list for subprocess.run() [qmd, collection, add, ...].
    """

    return [
        "qmd",
        "collection",
        "add",
        str(wiki_root),
        "--name",
        qmd_collection,
    ]


def build_qmd_embed_command(qmd_collection: str) -> list[str]:
    """Build qmd embedding refresh command for a registered collection.

    Constructs a shell command list for the qmd CLI embed subcommand to refresh
    semantic embeddings for all documents in a collection.

    Args:
        qmd_collection (str): Canonical name for the collection in qmd.

    Returns:
        list[str]: Command list for subprocess.run() [qmd, embed, -c, collection].
    """

    return [
        "qmd",
        "embed",
        "-c",
        qmd_collection,
    ]


def refresh_qmd_index(
    wiki_root: Path,
    qmd_collection: str,
    exclude_paths: Iterable[str],
    qmd_enabled: bool = True,
) -> dict[str, object]:
    """Refresh qmd collection index when qmd CLI is available.

    Orchestrates qmd collection registration and embedding refresh. Gracefully
    degrades to fallback if qmd is unavailable or disabled. Logs warnings for
    non-critical failures (embedding refresh) while attempting embedding refresh.

    Args:
        wiki_root (Path): Absolute path to wiki root directory.
        qmd_collection (str): Canonical collection name.
        exclude_paths (Iterable[str]): Glob patterns to exclude from indexing.
        qmd_enabled (bool): Whether to attempt qmd operations. Defaults to True.

    Returns:
        dict[str, object]: Status payload with 'status' key:
            - "disabled": qmd disabled by config
            - "fallback": qmd unavailable or registration failed
            - "ok": registration successful (embedding refresh may have failed)
            Includes detailed return codes and stderr/stdout for debugging.
    """

    if not qmd_enabled:
        return {
            "status": "disabled",
            "reason": "qmd indexing disabled by config",
            "collection": qmd_collection,
        }

    assert_non_stage_path(Path("index.md"), exclude_paths)

    qmd_bin = shutil.which("qmd")
    if qmd_bin is None:
        LOGGER.info(QMD_MISSING_MESSAGE)
        return {
            "status": "fallback",
            "reason": "qmd CLI not installed",
            "collection": qmd_collection,
        }

    collection_command = build_qmd_collection_add_command(
        wiki_root=wiki_root,
        qmd_collection=qmd_collection,
    )
    collection_command[0] = qmd_bin
    collection_process = subprocess.run(
        collection_command,
        check=False,
        capture_output=True,
        text=True,
    )
    collection_already_exists = _qmd_collection_already_exists(collection_process)
    if collection_process.returncode != 0 and not collection_already_exists:
        if _qmd_process_reports_missing(collection_process):
            LOGGER.info(QMD_MISSING_MESSAGE)
            return {
                "status": "fallback",
                "reason": "qmd CLI not installed",
                "collection": qmd_collection,
                "return_code": collection_process.returncode,
                "stdout": collection_process.stdout.strip(),
                "stderr": collection_process.stderr.strip(),
            }
        LOGGER.warning(
            "qmd collection add failed; using markdown-based wiki search fallback: %s",
            collection_process.stderr.strip() or collection_process.stdout.strip(),
        )
        return {
            "status": "fallback",
            "reason": "qmd collection add command unavailable or failed",
            "collection": qmd_collection,
            "return_code": collection_process.returncode,
            "stdout": collection_process.stdout.strip(),
            "stderr": collection_process.stderr.strip(),
        }

    embed_command = build_qmd_embed_command(qmd_collection=qmd_collection)
    embed_command[0] = qmd_bin
    embed_process = subprocess.run(
        embed_command,
        check=False,
        capture_output=True,
        text=True,
    )
    if embed_process.returncode != 0:
        LOGGER.warning(
            "qmd embed failed; continuing with qmd keyword search fallback: %s",
            embed_process.stderr.strip() or embed_process.stdout.strip(),
        )
        return {
            "status": "ok",
            "collection": qmd_collection,
            "collection_status": (
                "exists" if collection_already_exists else "registered"
            ),
            "return_code": collection_process.returncode,
            "stdout": collection_process.stdout.strip(),
            "stderr": collection_process.stderr.strip(),
            "embed_status": "fallback",
            "embed_reason": "qmd embed command unavailable or failed",
            "embed_return_code": embed_process.returncode,
            "embed_stdout": embed_process.stdout.strip(),
            "embed_stderr": embed_process.stderr.strip(),
        }

    return {
        "status": "ok",
        "collection": qmd_collection,
        "collection_status": "exists" if collection_already_exists else "registered",
        "return_code": collection_process.returncode,
        "stdout": collection_process.stdout.strip(),
        "stderr": collection_process.stderr.strip(),
        "embed_status": "ok",
        "embed_return_code": embed_process.returncode,
        "embed_stdout": embed_process.stdout.strip(),
        "embed_stderr": embed_process.stderr.strip(),
    }


def search_wiki(
    query_text: str,
    wiki_root: Path,
    qmd_collection: str,
    exclude_paths: Iterable[str],
    result_count: int = 10,
    qmd_enabled: bool = True,
) -> dict[str, Any]:
    """Search wiki content with qmd first and deterministic markdown fallback.

    Attempts semantic search via qmd; if qmd fails or is disabled, falls back to
    deterministic markdown text matching. Always returns results from one backend.

    Args:
        query_text (str): Search query string.
        wiki_root (Path): Absolute path to wiki root directory.
        qmd_collection (str): Canonical collection name.
        exclude_paths (Iterable[str]): Glob patterns to exclude from fallback search.
        result_count (int): Maximum results to return. Defaults to 10.
        qmd_enabled (bool): Whether to attempt qmd search. Defaults to True.

    Returns:
        dict[str, Any]: Search result with 'status' key ("ok" or "fallback"),
            'backend' key, and 'results' list. Each result includes path,
            line number, match score, and snippet text.
    """

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
    """Search markdown files without reading excluded wiki paths.

    Performs deterministic case-insensitive text search across all .md files
    in wiki_root, respecting exclude patterns (e.g., stage/**). Results are
    scored by match frequency per line and sorted by score descending,
    then path ascending.

    Args:
        query_text (str): Search query string (case-insensitive).
        wiki_root (Path): Absolute path to wiki root directory.
        exclude_paths (Iterable[str]): Glob patterns to exclude from search.
        result_count (int): Maximum results to return. Defaults to 10.

    Returns:
        list[dict[str, Any]]: Sorted list of matches (limited to result_count).
            Each match dict contains: path (relative POSIX), line (line number),
            score (match frequency), snippet (matched line text).
    """

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
    """Run qmd query and normalize success/fallback metadata.

    Executes qmd query command and parses JSON results. Returns a status dict
    indicating success or fallback reason. Handles JSON parsing errors gracefully.

    Args:
        query_text (str): Search query string.
        qmd_collection (str): Canonical collection name.
        result_count (int): Maximum results to return.

    Returns:
        dict[str, Any]: Status dict with 'status' key:
            - "ok": qmd query succeeded; 'results' contains parsed JSON
            - "fallback": qmd unavailable or failed; includes stderr/stdout
            Also includes backend, collection, and return_code fields.
    """

    qmd_bin = shutil.which("qmd")
    if qmd_bin is None:
        LOGGER.info(QMD_MISSING_MESSAGE)
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
