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
- Does a second update preserve a directly customized `index.md` byte for byte,
  including optional root `okf_version` front matter and glossary links?
- If the index is missing, does the updater recreate it from the installed
  package template while ignoring a target-project shadow template?
- Does initialization avoid adding legacy prompt-template files to the wiki
  while still installing refresh/query skills and the workflow reference?
- Do concept notes carry OKF-required `type` plus recommended
  `title`/`description`/`status`/`generated` fields?

## Evidence

Regression coverage lives in `tests/test_agent_install.py`,
`tests/test_updater.py`, and `tests/test_wiki_wspace.py`.

## Related

- [Install and Index Ownership](/architecture/install-and-index-ownership.md)
