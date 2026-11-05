---
okf_version: "0.2"
---

# wiki_code_space

Project wiki for code_space that captures semantic intent, rationale,
and business context. It can complement Graphifyy structural topology when a
graph exists, but it is maintained independently.
This index supports progressive disclosure for coding-agent navigation.

# Architecture

* [Architecture](./architecture/) - Durable system context, configuration behavior, data flow, and cross-module contracts
* [Install and Index Ownership](./architecture/install-and-index-ownership.md) - Harness installation paths and project-owned index rules

# Decisions

* [Decisions](./decisions/) - Architecture decision records with durable tradeoffs

# QA

* [QA](./qa/) - Business and technical checks for expected behavior
* [Technical QA](./qa/technical.md) - Regression risks, invariants, interfaces, and failure modes

# Sessions

* [Sessions](./sessions/) - Failed approaches that produced reusable constraints
* [Missing qmd Log Regression](./sessions/2026-08-05-qmd-missing-log-regression.md) - Stale npm qmd launcher fallback logging

# Glossary

* [Glossary](./glossary/) - Project-specific terms and overloaded meanings

# Agent Access

* Run `wiki_wspace init <project-path> --llm <harness>` to initialize the wiki and register refresh/query skills. Supported harnesses: Copilot, Codex, Claude, Gemini (default), Cursor.

# First Files To Load

* [index.md](./index.md) - Bundle root; load first for orientation
* Folder-specific notes only when the user request or changed module makes them relevant

# Never Auto-Read

* `stage/` - Scratch area excluded from indexing and default agent browse
