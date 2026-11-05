---
type: session
title: Missing qmd Log Regression
description: Stale npm qmd launcher must fall back to Markdown search without dumping npm package errors.
tags: [session, qmd, installation, logging]
status: stable
generated: { by: wiki_wspace/agent, at: 2026-08-05T00:00:00Z }
---

# Problem

Initialization with a stale npm-backed qmd launcher exposed the full npm
missing-package error even though wiki installation completed with Markdown
search fallback.

# Approaches Tried

The first focused CLI regression test failed before exercising the behavior
because `tests/test_wiki_wspace.py` did not import `logging`; pytest raised
`NameError: name 'logging' is not defined`.

# Solution

Import `logging` in the CLI test and classify only recognized npm
missing-package signatures as an unavailable qmd installation. Emit a concise
informational fallback message without logging the captured npm output. Preserve
existing warning diagnostics for genuine qmd operational failures.

# Reusable Knowledge

A command returned by `shutil.which()` is not necessarily usable. Optional CLI
probes must distinguish stale package-manager launchers from operational
failures while keeping captured diagnostics out of user-facing logs for the
expected missing-tool path.

# Related

- [Install and Index Ownership](/architecture/install-and-index-ownership.md)
- [Technical QA](/qa/technical.md)

# Distillation Status

Pending wiki refresh.
