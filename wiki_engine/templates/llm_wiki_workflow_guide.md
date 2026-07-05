# LLM Wiki Workflow Guide

Project: {{ project_name }}
Wiki root: {{ wiki_root }}
Update command: python -m wiki_engine.cli update --project {{ project_name }}

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
- Preserve existing front matter keys and naming conventions.
- Never read, summarize, index, or update {{ wiki_root }}/stage/ unless the user names an exact stage file path.

## architecture/

Use for durable system concepts, data flows, configuration behavior, and cross-module contracts.

Capture:
- What mechanism exists and why it matters.
- Config parameters with business impact, safe ranges, and interactions.
- Non-obvious constraints a future change must preserve.

Omit:
- Line-by-line implementation descriptions.
- Temporary bugs or session history.

## decisions/

Use for architecture decision records.

Capture:
- The decision in one or two sentences.
- The business or operational force that made the decision valuable.
- Alternatives only when they explain future tradeoffs.

Omit:
- Debate transcripts, speculative options, and stale proposals.

## qa/

Use for questions and checks that validate expected behavior.

Capture:
- Business checks in `business.md`: stakeholder-visible outcomes, alert quality, operational risk, and decision impact.
- Technical checks in `technical.md`: regression risks, invariants, interfaces, and failure modes.

Omit:
- Generic test plans that do not connect to project behavior.

## sessions/

Use only when a failed approach led to a corrected implementation or a reusable constraint was discovered.

Write new artifacts as:
{{ wiki_root }}/sessions/YYYY-MM-DD-<topic-slug>.md

Use {{ wiki_root }}/sessions/_template.md.

Capture:
- Problem.
- Failed approach and concrete failure symptom.
- Final solution and key constraint discovered.
- Linked wiki pages that should be updated.

Omit:
- Narration, praise, status chatter, and routine successful implementation notes.

## glossary/

Use for domain terms, abbreviations, and project-specific meanings that reduce ambiguity.

Capture:
- The term.
- The project-specific meaning.
- A link to the most relevant wiki page when useful.

Omit:
- Generic dictionary definitions.

## log.md

The update command owns this append-only file. Do not hand-edit it unless repairing a malformed entry.

## qmd.yml

Keep the qmd collection name aligned with {{ wiki_root }}. Preserve exclusions for stage files and templates.
