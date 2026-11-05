---
type: qa
title: Technical QA
description: Regression risks, invariants, interfaces, and failure modes for wiki install and index ownership.
tags: [qa, technical]
status: stable
generated: { by: wiki_wspace/agent, at: 2026-08-04T00:00:00Z }
---

# Questions

- Does Copilot initialization write its instruction file and both skills below
  `.github/`, without creating `.agents/`?
- Does Cursor initialization write `.cursor/rules/wiki-wspace.mdc` plus both
  skills under `.cursor/skills/`, without touching unrelated Cursor rules?
- Does a second update preserve a directly customized `index.md` byte for byte,
  including optional root `okf_version` front matter and glossary links?
- If the index is missing, does the updater recreate it from the installed
  package template while ignoring a target-project shadow template?
- Does initialization avoid adding legacy prompt-template files to the wiki
  while still installing refresh/query skills and the workflow reference?
- Do concept notes carry OKF-required `type` plus recommended
  `title`/`description`/`status`/`generated` fields?
- Does a second `wiki_wspace update` avoid re-appending the same session
  reusable-knowledge bullet into `qa/technical.md` or other permanent notes?
- Does the same knowledge body with only a new date stamp stay as one line in
  permanent notes (no `- YYYY-MM-DD:` duplicates)?

## Evidence

Regression coverage lives in `tests/test_agent_install.py`,
`tests/test_updater.py`, `tests/test_session_distill.py`, and
`tests/test_wiki_wspace.py`.

## Related

- [Install and Index Ownership](/architecture/install-and-index-ownership.md)
