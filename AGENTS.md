# Agents Prompt Template

Use this file as the default agent operating contract for this repository.
Keep it concise and operational.

## Project

Project name: <project_name>
Primary command: python -m wiki_engine.cli update --project <project_name>
Wiki root: wiki_<project_name>
QMD collection: wiki_<project_name>

## Mission

Implement production-grade, reproducible changes for analytics and scientific workflows.
Prioritize correctness, testability, and clear business impact.

## Required Workflow

1. Read wiki_<project_name>/index.md first.
2. If changing configuration behavior, read wiki_<project_name>/architecture/config_params.md fully.
3. If changing decision logic, read wiki_<project_name>/decisions/adr-*.md before coding.
4. After implementation, run tests.
5. Run python -m wiki_engine.cli update --project <project_name>.

## Stage Folder Rule (Hard Gate)

Never read any file under wiki_<project_name>/stage/ unless the user names an exact file path in this conversation.
Do not browse, glob, or summarize the stage folder by default.

## Context Loading (Token Efficient)

Load context in this order:

1. wiki_<project_name>/index.md
2. wiki_<project_name>/architecture/config_params.md (if config-related)
3. wiki_<project_name>/qa/business.md and wiki_<project_name>/qa/technical.md (if behavior-related)
4. wiki_<project_name>/decisions/adr-*.md (if architectural changes)
5. wiki_<project_name>/sessions/*.md only when directly relevant to the changed module

If qmd is installed, prefer query-first lookup:

qmd query "<question>" -c wiki_<project_name> --json -n 10

## Coding Rules

1. Prefer small, single-purpose functions.
2. Use snake_case naming and common-part-first naming for related variables.
3. Use YAML-driven configuration and avoid duplicated constants.
4. Add or update regression tests for every bug fix.
5. Use logging instead of print statements in runtime code.

## Output Contract

When responding with implementation work:

1. State changed files.
2. State behavior change in one sentence.
3. State test evidence.
4. State whether wiki update command was run.

## Session Capture

When a failed approach leads to a corrected implementation, capture lessons in:

wiki_<project_name>/sessions/YYYY-MM-DD-<topic>.md

Include:
- Problem
- Failed approach and concrete failure symptom
- Final solution and key constraint discovered
- Linked wiki pages that should be updated

## Repo-Specific Defaults For This Workspace

- project_name: code_space
- wiki root: wiki_code_space
- qmd collection: wiki_code_space
- update command: python -m wiki_engine.cli update --project code_space

<!-- wiki-engine:code-space:start -->
## wiki_engine skills

This project keeps rationale, architecture, decisions, QA constraints, glossary terms, and reusable lessons in `wiki_code_space/`.

- Use `/wiki-query-code-space` before broad exploration when a task depends on why the system behaves as it does, business context, configuration semantics, prior decisions, constraints, or known failure modes.
- Use `/wiki-ref-code-space` after code, configuration, tests, or documentation change project semantics.
- The query command uses qmd when available and otherwise performs index-based Markdown search.
- Never inspect `wiki_code_space/stage/` unless the user names an exact file path there.
<!-- wiki-engine:code-space:end -->
