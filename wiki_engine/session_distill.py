"""Session ingestion and deterministic distillation to permanent wiki notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterable


CHECKBOX_PATTERN = re.compile(r"^- \[ \] (Applied to permanent note\(s\)|Logged in log\.md)$")


@dataclass(frozen=True)
class DistillResult:
    """Captures files updated during a session distillation run."""

    session_path: Path
    changed_files: list[Path]


def route_reusable_knowledge_line(line: str) -> Path:
    """Route reusable knowledge snippets into deterministic permanent notes."""

    lower_line = line.lower()
    if "config" in lower_line or "parameter" in lower_line:
        return Path("architecture/config_params.md")
    if "business" in lower_line or "operator" in lower_line:
        return Path("qa/business.md")
    if "constraint" in lower_line or "failure" in lower_line:
        return Path("qa/technical.md")
    return Path("decisions/session_distill.md")


def extract_reusable_knowledge_block(session_text: str) -> list[str]:
    """Extract non-empty bullet lines from the reusable knowledge section."""

    lines = session_text.splitlines()
    collecting = False
    output: list[str] = []

    for line in lines:
        if line.strip().lower() == "# reusable knowledge":
            collecting = True
            continue
        if collecting and line.startswith("# "):
            break
        if collecting and line.strip().startswith("-"):
            output.append(line.strip())

    return output


def mark_distilled_checklist(session_text: str) -> str:
    """Mark distillation checklist items as complete."""

    updated_lines: list[str] = []
    for line in session_text.splitlines():
        if CHECKBOX_PATTERN.match(line.strip()):
            updated_lines.append(line.replace("[ ]", "[x]", 1))
        else:
            updated_lines.append(line)
    return "\n".join(updated_lines) + "\n"


def append_snippet(target_path: Path, snippet: str, current_date: date) -> None:
    """Append a distilled note snippet to a permanent markdown note."""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        target_path.write_text(
            (
                "---\n"
                f"id: {target_path.stem}\n"
                f"title: {target_path.stem.replace('_', ' ').title()}\n"
                "type: memory\n"
                "tags: [distilled]\n"
                f"last_updated: {current_date.isoformat()}\n"
                "status: active\n"
                "source: distilled\n"
                "---\n\n"
                "# Notes\n"
            ),
            encoding="utf-8",
        )

    existing_text = target_path.read_text(encoding="utf-8")
    with target_path.open("a", encoding="utf-8") as file_pointer:
        if not existing_text.endswith("\n"):
            file_pointer.write("\n")
        file_pointer.write(f"\n- {current_date.isoformat()}: {snippet.lstrip('- ').strip()}\n")


def distill_session_note(
    session_path: Path,
    wiki_root: Path,
    current_date: date,
) -> DistillResult:
    """Distill a session note into architecture/qa/decisions note updates."""

    session_text = session_path.read_text(encoding="utf-8")
    reusable_lines = extract_reusable_knowledge_block(session_text=session_text)

    changed_files: list[Path] = [session_path]
    for snippet in reusable_lines:
        routed_path = wiki_root / route_reusable_knowledge_line(snippet)
        append_snippet(target_path=routed_path, snippet=snippet, current_date=current_date)
        changed_files.append(routed_path)

    updated_session_text = mark_distilled_checklist(session_text=session_text)
    session_path.write_text(updated_session_text, encoding="utf-8")

    return DistillResult(session_path=session_path, changed_files=changed_files)


def discover_session_notes(session_dir: Path) -> Iterable[Path]:
    """Yield session notes while ignoring scaffold templates."""

    if not session_dir.exists():
        return []
    return sorted(path for path in session_dir.glob("*.md") if path.name != "_template.md")
