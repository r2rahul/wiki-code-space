"""Unit tests for OKF v0.2 concept front matter rendering."""

from datetime import date
from pathlib import Path

from wiki_engine.okf_frontmatter import (
    ACTOR_WIKI_WSPACE_AGENT,
    render_concept_frontmatter,
    to_okf_timestamp,
)


def test_to_okf_timestamp_from_date() -> None:
    """Dates serialize to midnight UTC OKF timestamps."""

    assert to_okf_timestamp(value=date(2026, 8, 4)) == "2026-08-04T00:00:00Z"


def test_render_concept_frontmatter_includes_required_okf_fields() -> None:
    """Rendered front matter includes type plus recommended OKF fields."""

    frontmatter = render_concept_frontmatter(
        note_path=Path("architecture/config_params.md"),
        title="Config Params",
        description="Configuration parameters with business impact.",
        tags=["architecture", "distilled"],
        generated_at=date(2026, 8, 4),
        generated_by=ACTOR_WIKI_WSPACE_AGENT,
    )

    assert frontmatter.startswith("---\n")
    assert "type: architecture\n" in frontmatter
    assert "title: Config Params\n" in frontmatter
    assert "description: Configuration parameters with business impact.\n" in frontmatter
    assert "tags: [architecture, distilled]\n" in frontmatter
    assert "status: stable\n" in frontmatter
    assert (
        "generated: { by: wiki_wspace/agent, at: 2026-08-04T00:00:00Z }\n"
        in frontmatter
    )
    assert "id:" not in frontmatter
    assert "last_updated:" not in frontmatter
    assert "source:" not in frontmatter
