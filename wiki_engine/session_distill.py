"""Session ingestion and deterministic distillation to permanent wiki notes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterable

from wiki_engine.okf_frontmatter import (
    ACTOR_WIKI_WSPACE_AGENT,
    render_concept_frontmatter,
)


CHECKBOX_PATTERN = re.compile(
    r"^- \[ \] (Applied to permanent note\(s\)|Logged in log\.md)$"
)
COMPLETED_CHECKBOX_PATTERN = re.compile(
    r"^- \[x\] Applied to permanent note\(s\)$",
    re.MULTILINE,
)
SESSION_NOTE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
DATED_SNIPPET_PREFIX_PATTERN = re.compile(r"^-\s*\d{4}-\d{2}-\d{2}:\s*")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")
WHITESPACE_PATTERN = re.compile(r"\s+")
# Ignore tiny prefix matches so short shared phrases do not block distinct notes.
MIN_PREFIX_DEDUP_LENGTH = 48


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


def snippet_display_body(snippet: str) -> str:
    """Return human-readable snippet text for writing into permanent notes."""

    cleaned = snippet.strip()
    cleaned = DATED_SNIPPET_PREFIX_PATTERN.sub("", cleaned)
    return cleaned.lstrip("- ").strip()


def normalize_snippet_body(snippet: str) -> str:
    """Return comparable snippet text, ignoring date stamps and link chrome.

    Strips list markers, leading ``YYYY-MM-DD:`` stamps, markdown links, and
    collapses whitespace so the same knowledge line dated differently is treated
    as one note.
    """

    cleaned = snippet_display_body(snippet=snippet)
    cleaned = MARKDOWN_LINK_PATTERN.sub("", cleaned)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip(" -:;,.")
    return cleaned


def note_contains_snippet(existing_text: str, snippet: str) -> bool:
    """Return True when the snippet body is already present in a note.

    Date stamps do not count as differences: ``- 2026-08-19: text`` and
    ``- 2026-08-20: text`` are the same knowledge line. Also matches snippets
    embedded in a longer distilled line and truncated prior appends.
    """

    body = normalize_snippet_body(snippet=snippet)
    if not body:
        return True

    for line in existing_text.splitlines():
        existing_body = normalize_snippet_body(snippet=line)
        if not existing_body:
            continue
        if body == existing_body:
            return True
        if body in existing_body:
            return True
        if (
            existing_body in body
            and len(existing_body) >= MIN_PREFIX_DEDUP_LENGTH
        ):
            return True
    return False


def is_session_already_distilled(session_text: str) -> bool:
    """Return True when Distillation Status shows permanent notes were applied."""

    return COMPLETED_CHECKBOX_PATTERN.search(session_text) is not None


def mark_distilled_checklist(session_text: str) -> str:
    """Mark distillation checklist items as complete."""

    updated_lines: list[str] = []
    for line in session_text.splitlines():
        if CHECKBOX_PATTERN.match(line.strip()):
            updated_lines.append(line.replace("[ ]", "[x]", 1))
        else:
            updated_lines.append(line)
    return "\n".join(updated_lines) + "\n"


def ensure_distillation_status_complete(session_text: str) -> str:
    """Ensure Distillation Status records that permanent notes were applied.

    Adds a completed checklist when the section is missing or only has free
    prose such as ``Pending wiki refresh.``. Leaves existing completed
    checkboxes unchanged.
    """

    if is_session_already_distilled(session_text=session_text):
        return (
            session_text
            if session_text.endswith("\n")
            else f"{session_text}\n"
        )

    lines = session_text.splitlines()
    status_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().lower() == "# distillation status"
        ),
        None,
    )
    checklist = [
        "- [x] Applied to permanent note(s)",
        "- [x] Logged in log.md",
    ]
    if status_index is None:
        updated = [*lines, "", "# Distillation Status", "", *checklist]
        return "\n".join(updated) + "\n"

    next_heading = next(
        (
            index
            for index in range(status_index + 1, len(lines))
            if lines[index].startswith("# ")
        ),
        len(lines),
    )
    updated = [
        *lines[: status_index + 1],
        "",
        *checklist,
        *lines[next_heading:],
    ]
    return "\n".join(updated) + "\n"


def append_snippet(target_path: Path, snippet: str, current_date: date) -> bool:
    """Append a distilled note snippet when it is not already present.

    Args:
        target_path (Path): Permanent wiki note path.
        snippet (str): Reusable-knowledge bullet text.
        current_date (date): Distillation date stamp for new lines.

    Returns:
        bool: True when the target file was created or modified.
    """

    target_path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    if not target_path.exists():
        note_title = target_path.stem.replace("_", " ").replace("-", " ").title()
        frontmatter = render_concept_frontmatter(
            note_path=target_path,
            title=note_title,
            description=f"Distilled notes for {note_title}.",
            tags=[target_path.parent.name, "distilled"],
            generated_at=current_date,
            generated_by=ACTOR_WIKI_WSPACE_AGENT,
        )
        target_path.write_text(
            f"{frontmatter}\n# Notes\n",
            encoding="utf-8",
        )
        created = True

    existing_text = target_path.read_text(encoding="utf-8")
    if note_contains_snippet(existing_text=existing_text, snippet=snippet):
        return created

    body = snippet_display_body(snippet=snippet)
    with target_path.open("a", encoding="utf-8") as file_pointer:
        if not existing_text.endswith("\n"):
            file_pointer.write("\n")
        file_pointer.write(f"\n- {current_date.isoformat()}: {body}\n")
    return True


def distill_session_note(
    session_path: Path,
    wiki_root: Path,
    current_date: date,
) -> DistillResult:
    """Distill a session note into architecture/qa/decisions note updates.

    Idempotent: already-distilled sessions and duplicate reusable-knowledge
    bullets do not rewrite permanent notes or report false file changes.
    """

    if not SESSION_NOTE_PATTERN.match(session_path.name):
        return DistillResult(session_path=session_path, changed_files=[])

    session_text = session_path.read_text(encoding="utf-8")
    if is_session_already_distilled(session_text=session_text):
        return DistillResult(session_path=session_path, changed_files=[])

    reusable_lines = extract_reusable_knowledge_block(session_text=session_text)
    if not reusable_lines:
        return DistillResult(session_path=session_path, changed_files=[])

    changed_files: list[Path] = []
    for snippet in reusable_lines:
        routed_path = wiki_root / route_reusable_knowledge_line(snippet)
        was_updated = append_snippet(
            target_path=routed_path, snippet=snippet, current_date=current_date
        )
        if was_updated:
            changed_files.append(routed_path)

    updated_session_text = ensure_distillation_status_complete(
        session_text=mark_distilled_checklist(session_text=session_text)
    )
    if updated_session_text != (
        session_text if session_text.endswith("\n") else f"{session_text}\n"
    ):
        session_path.write_text(updated_session_text, encoding="utf-8")
        changed_files.append(session_path)

    return DistillResult(session_path=session_path, changed_files=changed_files)


def discover_session_notes(session_dir: Path) -> Iterable[Path]:
    """Yield dated session notes, ignoring templates and folder indexes."""

    if not session_dir.exists():
        return []
    return sorted(
        path
        for path in session_dir.glob("*.md")
        if SESSION_NOTE_PATTERN.match(path.name)
    )
