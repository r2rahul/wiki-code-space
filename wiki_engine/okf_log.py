"""OKF v0.2 log.md helpers: date headings and newest-first entries."""

from __future__ import annotations

from datetime import date, datetime
import re


DATE_HEADING_PATTERN = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)
LEGACY_TIMESTAMP_HEADING_PATTERN = re.compile(
    r"^## (\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}\s*$",
    re.MULTILINE,
)
LEGACY_ENTRY_PATTERN = re.compile(
    r"^## (?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s*\n"
    r"- update_type: (?P<update_type>.+)\n"
    r"- changed_files: \[(?P<changed_files>.*)\]\n"
    r"- reason: (?P<reason>.+)\n"
    r"- source: (?P<source>.+)\n?",
    re.MULTILINE,
)


def format_update_bullet(
    *,
    update_type: str,
    changed_files: list[str],
    reason: str,
    source: str = "agent",
) -> str:
    """Format one OKF log bullet for a wiki update run.

    Args:
        update_type (str): Update kind such as ``session_distill`` or ``code_sync``.
        changed_files (list[str]): Relative paths changed in the run.
        reason (str): One-line reason for the update.
        source (str): Actor label for the run (``agent`` or ``human``).

    Returns:
        str: Single markdown list item without a trailing newline.
    """

    changed_file_list = ", ".join(changed_files)
    files_clause = (
        f"; changed_files: [{changed_file_list}]" if changed_files else ""
    )
    return (
        f"* **Update**: `{update_type}` by {source} — {reason}{files_clause}"
    )


def _split_preamble_and_sections(log_text: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Split a log into preamble text and ordered (date, bullets) sections."""

    normalized = log_text.replace("\r\n", "\n")
    if not normalized.endswith("\n") and normalized:
        normalized = f"{normalized}\n"

    matches = list(DATE_HEADING_PATTERN.finditer(normalized))
    if not matches:
        preamble = normalized.rstrip("\n") + "\n"
        return preamble, []

    preamble = normalized[: matches[0].start()].rstrip("\n") + "\n"
    sections: list[tuple[str, list[str]]] = []
    for index, match in enumerate(matches):
        section_date = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        body = normalized[start:end].strip("\n")
        bullets = [
            line
            for line in body.splitlines()
            if line.startswith("* ") or line.startswith("- ")
        ]
        sections.append((section_date, bullets))
    return preamble, sections


def _render_log(preamble: str, sections: list[tuple[str, list[str]]]) -> str:
    """Render preamble plus date sections newest-first."""

    ordered = sorted(sections, key=lambda item: item[0], reverse=True)
    parts = [preamble.rstrip("\n"), ""]
    for section_date, bullets in ordered:
        parts.append(f"## {section_date}")
        parts.extend(bullets)
        parts.append("")
    rendered = "\n".join(parts).rstrip("\n") + "\n"
    return rendered


def insert_okf_log_entry(
    log_text: str,
    *,
    entry_date: date,
    bullet: str,
) -> str:
    """Insert a log bullet under a YYYY-MM-DD heading, newest date first.

    Args:
        log_text (str): Existing log.md content.
        entry_date (date): Calendar date for the OKF heading.
        bullet (str): Formatted list item to insert.

    Returns:
        str: Updated log content with trailing newline.
    """

    preamble, sections = _split_preamble_and_sections(log_text=log_text)
    date_text = entry_date.isoformat()
    section_map = {section_date: list(bullets) for section_date, bullets in sections}
    existing = section_map.get(date_text, [])
    section_map[date_text] = [bullet, *existing]
    rebuilt = [(section_date, section_map[section_date]) for section_date in section_map]
    return _render_log(preamble=preamble, sections=rebuilt)


def migrate_legacy_timestamp_log(log_text: str) -> str:
    """Convert legacy timestamp-headed log entries to OKF date headings.

    Args:
        log_text (str): Log content that may contain ``## YYYY-MM-DDTHH:MM:SS``
            headings and structured field bullets.

    Returns:
        str: OKF-conformant log with ``## YYYY-MM-DD`` headings, newest first.
    """

    normalized = log_text.replace("\r\n", "\n")
    legacy_entries = list(LEGACY_ENTRY_PATTERN.finditer(normalized))
    if not legacy_entries:
        # Already date-headed or empty of entries: normalize ordering only.
        preamble, sections = _split_preamble_and_sections(log_text=normalized)
        return _render_log(preamble=preamble, sections=sections)

    first_legacy_start = legacy_entries[0].start()
    preamble_raw = normalized[:first_legacy_start]
    initialized_match = re.search(
        r"(?m)^Initialized on .+$",
        preamble_raw,
    )
    initialized_line = (
        initialized_match.group(0)
        if initialized_match
        else "Initialized on unknown date."
    )
    preamble = (
        "# Update Log\n\n"
        "Chronological record of coherent wiki update runs (newest first).\n\n"
        "Entry schema:\n"
        "- Date heading: `## YYYY-MM-DD` (newest first)\n"
        "- Bullet: `* **Update**: update_type by source — reason; "
        "changed_files: [...]`\n\n"
        f"{initialized_line}\n"
    )

    dated_bullets: dict[str, list[tuple[datetime, str]]] = {}
    for match in legacy_entries:
        stamp = datetime.strptime(match.group("stamp"), "%Y-%m-%dT%H:%M:%S")
        changed_raw = match.group("changed_files").strip()
        changed_files = (
            [part.strip() for part in changed_raw.split(",") if part.strip()]
            if changed_raw
            else []
        )
        bullet = format_update_bullet(
            update_type=match.group("update_type").strip(),
            changed_files=changed_files,
            reason=match.group("reason").strip(),
            source=match.group("source").strip(),
        )
        day = stamp.date().isoformat()
        dated_bullets.setdefault(day, []).append((stamp, bullet))

    sections: list[tuple[str, list[str]]] = []
    for day in sorted(dated_bullets.keys(), reverse=True):
        day_entries = sorted(dated_bullets[day], key=lambda item: item[0], reverse=True)
        sections.append((day, [bullet for _, bullet in day_entries]))

    return _render_log(preamble=preamble, sections=sections)
