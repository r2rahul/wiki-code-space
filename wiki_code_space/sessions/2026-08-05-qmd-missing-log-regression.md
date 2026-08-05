---
id: session-qmd-missing-log-regression
title: Missing qmd Log Regression
type: session
tags: [session, qmd, installation, logging]
last_updated: 2026-08-05
status: active
source: agent
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

- [[../architecture/install-and-index-ownership]]
- [[../qa/technical]]

# Distillation Status

Pending wiki refresh.
