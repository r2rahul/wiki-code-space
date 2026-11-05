"""Unit tests for OKF log date headings and newest-first insertion."""

from datetime import date

from wiki_engine.okf_log import (
    format_update_bullet,
    insert_okf_log_entry,
    migrate_legacy_timestamp_log,
)


def test_format_update_bullet_includes_changed_files() -> None:
    """Bullets include update type, source, reason, and changed files."""

    bullet = format_update_bullet(
        update_type="code_sync",
        changed_files=["wiki_coce/index.md"],
        reason="Coherent wiki+graph+qmd update run",
        source="agent",
    )
    assert bullet.startswith("* **Update**: `code_sync` by agent — ")
    assert "changed_files: [wiki_coce/index.md]" in bullet


def test_insert_okf_log_entry_is_newest_first() -> None:
    """Newer dates and same-day bullets are ordered newest first."""

    seed = (
        "# Update Log\n\n"
        "Initialized on 2026-08-03.\n\n"
        "## 2026-08-03\n"
        "* **Update**: `code_sync` by agent — older\n"
    )
    after_aug_05 = insert_okf_log_entry(
        log_text=seed,
        entry_date=date(2026, 8, 5),
        bullet="* **Update**: `session_distill` by agent — newer day",
    )
    after_same_day = insert_okf_log_entry(
        log_text=after_aug_05,
        entry_date=date(2026, 8, 5),
        bullet="* **Update**: `code_sync` by agent — newest same day",
    )

    aug_05_pos = after_same_day.find("## 2026-08-05")
    aug_03_pos = after_same_day.find("## 2026-08-03")
    assert aug_05_pos != -1
    assert aug_03_pos != -1
    assert aug_05_pos < aug_03_pos
    newest_pos = after_same_day.find("newest same day")
    older_same_day_pos = after_same_day.find("newer day")
    assert newest_pos < older_same_day_pos


def test_migrate_legacy_timestamp_log_groups_by_date() -> None:
    """Legacy timestamp headings migrate to OKF date headings."""

    legacy = (
        "# Update Log\n\n"
        "Entry schema:\n"
        "- `## YYYY-MM-DDTHH:MM:SS`\n\n"
        "Initialized on 2026-08-03.\n\n"
        "## 2026-08-03T19:46:39\n"
        "- update_type: code_sync\n"
        "- changed_files: [wiki_coce/index.md]\n"
        "- reason: Coherent wiki+graph+qmd update run\n"
        "- source: agent\n\n"
        "## 2026-08-05T10:57:50\n"
        "- update_type: session_distill\n"
        "- changed_files: []\n"
        "- reason: Coherent wiki+graph+qmd update run\n"
        "- source: agent\n"
    )
    migrated = migrate_legacy_timestamp_log(log_text=legacy)
    assert "## 2026-08-05\n" in migrated
    assert "## 2026-08-03\n" in migrated
    assert "T19:46:39" not in migrated
    assert migrated.find("## 2026-08-05") < migrated.find("## 2026-08-03")
    assert "* **Update**: `session_distill` by agent" in migrated
