"""Graph bridge utilities for syncing wiki notes with code graph structure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


CODE_REF_PATTERN = re.compile(r"(?P<path>[A-Za-z0-9_./-]+)\s*->\s*(?P<symbol>[A-Za-z0-9_().-]+)")


@dataclass(frozen=True)
class BridgeEdge:
    """Represents a semantic bridge edge from wiki note to code symbol."""

    note_path: str
    code_path: str
    symbol_name: str


def is_excluded_path(file_path: Path, exclude_paths: Iterable[str]) -> bool:
    """Return True when a path is under any excluded glob-like prefix."""

    normalized_path = file_path.as_posix()
    for raw_exclude in exclude_paths:
        clean_exclude = raw_exclude.replace("**", "").strip("/")
        if not clean_exclude:
            continue
        if normalized_path.startswith(clean_exclude):
            return True
    return False


def extract_bridge_edges(note_path: Path, content: str) -> list[BridgeEdge]:
    """Extract path+symbol references that bridge wiki notes with code nodes."""

    edges: list[BridgeEdge] = []
    for match in CODE_REF_PATTERN.finditer(content):
        code_path = match.group("path")
        symbol_name = match.group("symbol")
        edges.append(
            BridgeEdge(
                note_path=note_path.as_posix(),
                code_path=code_path,
                symbol_name=symbol_name,
            )
        )
    return edges


def collect_bridge_edges(
    wiki_root: Path,
    exclude_paths: Iterable[str],
) -> list[BridgeEdge]:
    """Collect bridge edges from markdown notes while respecting exclusions."""

    edges: list[BridgeEdge] = []
    for note_path in wiki_root.rglob("*.md"):
        relative_path = note_path.relative_to(wiki_root)
        if is_excluded_path(relative_path, exclude_paths):
            continue
        content = note_path.read_text(encoding="utf-8")
        edges.extend(extract_bridge_edges(relative_path, content))
    return edges


def update_graph_bridge(
    project_name: str,
    wiki_root: Path,
    exclude_paths: Iterable[str],
) -> dict[str, object]:
    """Build community bridge metadata for Graphifyy update workflows."""

    _ = project_name
    edges = collect_bridge_edges(wiki_root=wiki_root, exclude_paths=exclude_paths)
    return {
        "bridge_edge_count": len(edges),
        "bridge_edges": [
            {
                "note_path": edge.note_path,
                "code_path": edge.code_path,
                "symbol_name": edge.symbol_name,
            }
            for edge in edges
        ],
    }
