"""Canonical project naming for wiki_engine artifacts."""

from __future__ import annotations

import re


def normalize_project_name(raw_name: str) -> str:
    """Return the first two and last two cleaned lowercase characters.

    Non-alphanumeric characters are removed before shortening. Names containing
    four or fewer characters are returned in full.
    """

    cleaned_name = re.sub(r"[^a-zA-Z0-9]", "", raw_name).lower()
    if not cleaned_name:
        raise ValueError("Project name must contain at least one letter or number")
    if len(cleaned_name) <= 4:
        return cleaned_name
    return f"{cleaned_name[:2]}{cleaned_name[-2:]}"
