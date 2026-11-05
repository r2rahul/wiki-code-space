"""OKF v0.2 front matter helpers for wiki concept notes."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path


STATUS_STABLE = "stable"
ACTOR_WIKI_WSPACE_AGENT = "wiki_wspace/agent"
ACTOR_PROCESS_WIKI_ENGINE = "process:wiki_engine"


def to_okf_timestamp(value: date | datetime) -> str:
    """Convert a date or datetime to an OKF ISO 8601 UTC timestamp.

    Args:
        value (date | datetime): Date or datetime to serialize.

    Returns:
        str: Timestamp in ``YYYY-MM-DDTHH:MM:SSZ`` form.
    """

    if isinstance(value, datetime):
        if value.tzinfo is None:
            utc_value = value.replace(tzinfo=timezone.utc)
        else:
            utc_value = value.astimezone(timezone.utc)
        return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{value.isoformat()}T00:00:00Z"


def note_type_for_path(note_path: Path) -> str:
    """Map a concept path to its OKF ``type`` value.

    Args:
        note_path (Path): Path of the concept markdown file.

    Returns:
        str: Free-form OKF type string for the concept folder.
    """

    return {
        "architecture": "architecture",
        "qa": "qa",
        "decisions": "decision",
        "glossary": "glossary",
        "sessions": "session",
    }.get(note_path.parent.name, "session")


def render_concept_frontmatter(
    *,
    note_path: Path,
    title: str,
    description: str,
    tags: list[str],
    generated_at: date | datetime,
    generated_by: str = ACTOR_WIKI_WSPACE_AGENT,
    status: str = STATUS_STABLE,
) -> str:
    """Render OKF-conformant YAML front matter for a concept note.

    Concept identity is the bundle-relative path without ``.md``; no separate
    ``id`` field is emitted. Required OKF field is ``type``; recommended fields
    ``title``, ``description``, ``tags``, ``status``, and ``generated`` are
    included for agent navigation and trust signals.

    Args:
        note_path (Path): Concept file path used to derive ``type``.
        title (str): Human-readable display name.
        description (str): One-sentence summary for indexes and search.
        tags (list[str]): Cross-cutting categorization tags.
        generated_at (date | datetime): Content generation timestamp.
        generated_by (str): OKF actor string for ``generated.by``.
        status (str): Lifecycle status: ``draft``, ``stable``, or ``deprecated``.

    Returns:
        str: Front matter block including opening and closing ``---`` lines.
    """

    note_type = note_type_for_path(note_path=note_path)
    tag_list = ", ".join(tags)
    timestamp = to_okf_timestamp(value=generated_at)
    return (
        "---\n"
        f"type: {note_type}\n"
        f"title: {title}\n"
        f"description: {description}\n"
        f"tags: [{tag_list}]\n"
        f"status: {status}\n"
        f"generated: {{ by: {generated_by}, at: {timestamp} }}\n"
        "---\n"
    )
