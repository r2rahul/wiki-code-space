# LLM Wiki Workflow Guide

Project: {{ project_name }}
Wiki root: {{ wiki_root }}
Update command: wiki_wspace update --project {{ project_name }}

Use this guide when maintaining the wiki. Capture semantic context that helps a future human or agent understand why the project works as it does. Keep each note brief, atomic, and source-grounded.

## Global Rules

- Read {{ wiki_root }}/index.md first.
- Prefer qmd query "<question>" -c {{ wiki_root }} --json -n 10 when qmd is installed.
- Do not duplicate function docs, docstrings, stack traces, or long implementation listings.
- Link to code by stable path and symbol when it clarifies business or architectural context, for example `src/models/forecasting.py -> run_forecast()`.
- For Graphifyy-friendly communities, name the concrete file path, function
  or class, config file/key, and business rationale in the same note when they
  are related. Example:
  `Target: src/models/forecasting.py -> run_forecast()`;
  `Config Parameter: volatility_penalty inside config.yaml`;
  `Business Context: higher volatility_penalty reduces false-positive alerts`.
- Preserve OKF front matter keys and naming conventions; do not invent fields.
- Treat `{{ wiki_root }}/index.md` as project-owned after initialization. Edit it
  directly when progressive-disclosure listings change; do not create a shadow
  `wiki_engine/templates/index.md.j2` in the project. Root index MAY carry only
  `okf_version` front matter; subdirectory `index.md` files have no front matter.
- Never read, summarize, index, or update {{ wiki_root }}/stage/ unless the user names an exact stage file path.
- Do not create placeholder notes. Create a wiki note only when it captures
  source-grounded project knowledge that will help future maintenance.

## Metadata Contract (OKF v0.2)

Every concept note under `architecture/`, `decisions/`, `qa/`,
`sessions/`, or `glossary/` must start with YAML front matter. Concept ID is
the bundle-relative path without `.md` (for example `architecture/config_params`).

```yaml
---
type: <architecture|decision|qa|session|glossary>
title: <Human Title>
description: <One-sentence summary for index listings>
tags: [<folder>, <specific-topic>]
status: stable
generated: { by: wiki_wspace/agent, at: YYYY-MM-DDTHH:MM:SSZ }
---
```

Rules:
- `type` is required. Use lowercase kebab-case filenames; keep paths stable.
- `status` is `draft`, `stable`, or `deprecated` (default `stable`).
- Update `generated.at` when concept semantics change. Use actor
  `wiki_wspace/agent` for agent-authored notes, `human:<id>` when the user
  provides the note content, and `process:<id>` for automation.
- Optional OKF fields (`verified`, `sources`, `stale_after`, `resource`) may be
  added when provenance or trust signals are known; do not fabricate them.
- Cross-link with standard markdown links (prefer bundle-absolute paths such as
  `[Technical QA](/qa/technical.md)`). Do not use `[[wikilinks]]`.
- Include a `## Related` section with those links when another note is directly
  relevant. Omit it when there is no grounded relationship.
- Keep directory `index.md` files as progressive-disclosure lists:
  `* [Title](./note.md) - description from frontmatter`.

## architecture/

Use for durable system concepts, data flows, configuration behavior, and cross-module contracts.

Capture:
- What mechanism exists and why it matters.
- Config parameters with business impact, safe ranges, and interactions.
- Non-obvious constraints a future change must preserve.

Suggested sections:
- `# Context`
- `## Constraints`
- `## Related`

Omit:
- Line-by-line implementation descriptions.
- Temporary bugs or session history.

## decisions/

Use for architecture decision records.

Capture:
- The decision in one or two sentences.
- The business or operational force that made the decision valuable.
- Alternatives only when they explain future tradeoffs.

Suggested filename: `adr-YYYYMMDD-<topic>.md`.

Suggested sections:
- `# Decision`
- `## Context`
- `## Consequences`
- `## Related`

Omit:
- Debate transcripts, speculative options, and stale proposals.

## qa/

Use for questions and checks that validate expected behavior.

Capture:
- Business checks in `business.md`: stakeholder-visible outcomes, alert quality, operational risk, and decision impact.
- Technical checks in `technical.md`: regression risks, invariants, interfaces, and failure modes.

Suggested sections:
- `# Questions`
- `## Evidence`
- `## Related`

Omit:
- Generic test plans that do not connect to project behavior.

## sessions/

Use only when a failed approach led to a corrected implementation or a reusable constraint was discovered.

Write new artifacts as:
{{ wiki_root }}/sessions/YYYY-MM-DD-<topic-slug>.md

Capture:
- Problem.
- Failed approach and concrete failure symptom.
- Final solution and key constraint discovered.
- Linked wiki pages that should be updated.

Use this section order:
- `# Problem`
- `# Approaches Tried`
- `# Solution`
- `# Reusable Knowledge`
- `# Related`
- `# Distillation Status`

`# Reusable Knowledge` must use markdown bullets (`- ...`). Distillation routes
each bullet once into a permanent note and then marks Distillation Status
complete. Later `wiki_wspace update` runs must not re-append the same bullet.

Omit:
- Narration, praise, status chatter, and routine successful implementation notes.

## glossary/

Use for domain terms, abbreviations, and project-specific meanings that reduce ambiguity.

Capture:
- The term.
- The project-specific meaning.
- A link to the most relevant wiki page when useful.

Suggested sections:
- `# Meaning`
- `## Usage`
- `## Related`

Omit:
- Generic dictionary definitions.

## log.md

The update command owns this OKF log: ``## YYYY-MM-DD`` headings, newest first.
Do not hand-edit it unless repairing a malformed entry.

## qmd.yml

Keep the qmd collection name aligned with {{ wiki_root }}. Preserve exclusions
for stage files and underscore-prefixed utility files.
