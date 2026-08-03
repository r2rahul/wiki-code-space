"""Tests for canonical compact project naming."""

from __future__ import annotations

import pytest

from wiki_engine.naming import normalize_project_name


@pytest.mark.parametrize(
    ("raw_name", "expected_name"),
    [
        ("code_space", "coce"),
        ("My Project!", "myct"),
        ("!!! My Project @2026 ###", "my26"),
        ("A! B@", "ab"),
        ("123456", "1256"),
        ("xy", "xy"),
    ],
)
def test_normalize_project_name(raw_name: str, expected_name: str) -> None:
    """Names should be cleaned before first-two/last-two compaction."""

    assert normalize_project_name(raw_name) == expected_name


def test_normalize_project_name_rejects_only_special_characters() -> None:
    """A name with no usable characters cannot identify a wiki."""

    with pytest.raises(ValueError, match="at least one letter or number"):
        normalize_project_name("!!!___---")
