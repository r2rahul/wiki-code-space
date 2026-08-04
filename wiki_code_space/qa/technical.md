---
id: qa-technical
title: Technical QA
type: qa
tags: [qa, technical]
last_updated: 2026-08-04
status: active
source: agent
---

# Questions

- Does Copilot initialization write its instruction file and both skills below
  `.github/`, without creating `.agents/`?
- Does a second update preserve a directly customized `index.md` byte for byte,
  including YAML front matter and glossary links?
- If the index is missing, does the updater recreate it from the installed
  package template while ignoring a target-project shadow template?
- Does initialization avoid adding legacy prompt-template files to the wiki
  while still installing refresh/query skills and the workflow reference?

## Evidence

Regression coverage lives in `tests/test_agent_install.py`,
`tests/test_updater.py`, and `tests/test_wiki_wspace.py`.

## Related

- [[../architecture/install-and-index-ownership]]
