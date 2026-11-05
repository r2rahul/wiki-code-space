"""Regression tests for idempotent session distillation."""

from datetime import date
from pathlib import Path

from wiki_engine.session_distill import (
    append_snippet,
    discover_session_notes,
    distill_session_note,
    note_contains_snippet,
)


def test_discover_session_notes_skips_index_and_templates(tmp_path: Path) -> None:
    """Only dated session notes are distillable."""

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "index.md").write_text("# Sessions\n", encoding="utf-8")
    (sessions / "_template.md").write_text("# Template\n", encoding="utf-8")
    note = sessions / "2026-08-19-remote-tools.md"
    note.write_text("# Session\n", encoding="utf-8")

    discovered = list(discover_session_notes(session_dir=sessions))
    assert discovered == [note]


def test_append_snippet_does_not_duplicate_existing_knowledge(tmp_path: Path) -> None:
    """Repeated distill of the same reusable line must not append again."""

    target = tmp_path / "qa" / "technical.md"
    snippet = (
        "- If chat file tools in a Remote-SSH workspace report success/failure that "
        "does not match local behavior, check settings.json remote.extensionKind."
    )
    first = append_snippet(
        target_path=target, snippet=snippet, current_date=date(2026, 8, 19)
    )
    second = append_snippet(
        target_path=target, snippet=snippet, current_date=date(2026, 8, 20)
    )
    truncated = append_snippet(
        target_path=target,
        snippet=(
            "- If chat file tools in a Remote-SSH workspace report success/failure that"
        ),
        current_date=date(2026, 8, 21),
    )

    text = target.read_text(encoding="utf-8")
    assert first is True
    assert second is False
    assert truncated is False
    assert text.count("If chat file tools in a Remote-SSH workspace") == 1


def test_same_content_with_new_date_is_not_duplicated(tmp_path: Path) -> None:
    """A later date stamp must not create a second copy of the same note body."""

    target = tmp_path / "qa" / "technical.md"
    target.parent.mkdir(parents=True)
    target.write_text(
        (
            "---\n"
            "type: qa\n"
            "title: Technical\n"
            "description: Distilled technical notes.\n"
            "tags: [qa, distilled]\n"
            "status: stable\n"
            "generated: { by: wiki_wspace/agent, at: 2026-08-19T00:00:00Z }\n"
            "---\n\n"
            "# Notes\n\n"
            "- 2026-08-19: If chat file tools in a Remote-SSH workspace report "
            "success/failure that does not match local behavior, check "
            "settings.json remote.extensionKind.\n"
        ),
        encoding="utf-8",
    )

    appended = append_snippet(
        target_path=target,
        snippet=(
            "- If chat file tools in a Remote-SSH workspace report success/failure "
            "that does not match local behavior, check settings.json "
            "remote.extensionKind."
        ),
        current_date=date(2026, 8, 20),
    )
    text = target.read_text(encoding="utf-8")
    assert appended is False
    assert "2026-08-20:" not in text
    assert text.count("If chat file tools in a Remote-SSH workspace") == 1


def test_new_session_with_same_body_does_not_redate_technical_note(
    tmp_path: Path,
) -> None:
    """A second session carrying the same bullet must not re-append under a new date."""

    wiki_root = tmp_path / "wiki"
    technical = wiki_root / "qa" / "technical.md"
    technical.parent.mkdir(parents=True)
    technical.write_text(
        (
            "# Notes\n\n"
            "- 2026-08-19: If chat file tools in a Remote-SSH workspace report "
            "success/failure that does not match local behavior, check "
            "settings.json remote.extensionKind. "
            "[session 2026-08-19](../sessions/2026-08-19-a.md)\n"
        ),
        encoding="utf-8",
    )

    session_path = wiki_root / "sessions" / "2026-08-20-remote-tools-again.md"
    session_path.parent.mkdir(parents=True)
    session_path.write_text(
        (
            "# Reusable Knowledge\n"
            "- If chat file tools in a Remote-SSH workspace report success/failure "
            "that does not match local behavior, check settings.json "
            "remote.extensionKind.\n\n"
            "# Distillation Status\n"
            "- [ ] Applied to permanent note(s)\n"
            "- [ ] Logged in log.md\n"
        ),
        encoding="utf-8",
    )

    result = distill_session_note(
        session_path=session_path,
        wiki_root=wiki_root,
        current_date=date(2026, 8, 20),
    )
    text = technical.read_text(encoding="utf-8")
    assert technical not in result.changed_files
    assert "2026-08-20:" not in text
    assert text.count("If chat file tools in a Remote-SSH workspace") == 1


def test_note_contains_snippet_detects_embedded_full_line() -> None:
    """A longer distilled line with a session link still counts as present."""

    existing = (
        "- 2026-08-19: If chat file tools in a Remote-SSH workspace report "
        "success/failure that does not match local behavior, check settings.json "
        "remote.extensionKind. "
        "[session 2026-08-19](../sessions/2026-08-19-vscode-remote-extension-kind-file-tools.md)\n"
    )
    snippet = (
        "If chat file tools in a Remote-SSH workspace report success/failure that "
        "does not match local behavior, check settings.json remote.extensionKind."
    )
    assert note_contains_snippet(existing_text=existing, snippet=snippet) is True
    assert note_contains_snippet(
        existing_text=existing,
        snippet="- 2026-08-20: If chat file tools in a Remote-SSH workspace report "
        "success/failure that does not match local behavior, check settings.json "
        "remote.extensionKind.",
    ) is True


def test_distill_session_note_is_idempotent(tmp_path: Path) -> None:
    """Second distill reports no changes and leaves qa note unchanged."""

    wiki_root = tmp_path / "wiki"
    session_path = wiki_root / "sessions" / "2026-08-19-remote-tools.md"
    session_path.parent.mkdir(parents=True)
    session_path.write_text(
        (
            "---\n"
            "type: session\n"
            "title: Remote Tools\n"
            "description: Distill idempotency fixture.\n"
            "tags: [session]\n"
            "status: stable\n"
            "generated: { by: wiki_wspace/agent, at: 2026-08-19T00:00:00Z }\n"
            "---\n\n"
            "# Reusable Knowledge\n"
            "- If chat file tools fail inconsistently, treat that failure mode as a "
            "constraint for remote.extensionKind troubleshooting.\n\n"
            "# Distillation Status\n"
            "- [ ] Applied to permanent note(s)\n"
            "- [ ] Logged in log.md\n"
        ),
        encoding="utf-8",
    )

    first = distill_session_note(
        session_path=session_path,
        wiki_root=wiki_root,
        current_date=date(2026, 8, 19),
    )
    technical = wiki_root / "qa" / "technical.md"
    assert technical.exists()
    first_text = technical.read_text(encoding="utf-8")
    assert "remote.extensionKind" in first_text
    assert any(path == technical for path in first.changed_files)

    second = distill_session_note(
        session_path=session_path,
        wiki_root=wiki_root,
        current_date=date(2026, 8, 20),
    )
    assert second.changed_files == []
    assert technical.read_text(encoding="utf-8") == first_text
    assert "- [x] Applied to permanent note(s)" in session_path.read_text(
        encoding="utf-8"
    )


def test_distill_without_reusable_bullets_is_a_no_op(tmp_path: Path) -> None:
    """Prose-only reusable knowledge sections do not rewrite files."""

    wiki_root = tmp_path / "wiki"
    session_path = wiki_root / "sessions" / "2026-08-05-example.md"
    session_path.parent.mkdir(parents=True)
    original = (
        "# Reusable Knowledge\n\n"
        "A command returned by shutil.which() is not necessarily usable.\n\n"
        "# Distillation Status\n\n"
        "Pending wiki refresh.\n"
    )
    session_path.write_text(original, encoding="utf-8")

    result = distill_session_note(
        session_path=session_path,
        wiki_root=wiki_root,
        current_date=date(2026, 8, 5),
    )
    assert result.changed_files == []
    assert session_path.read_text(encoding="utf-8") == original
