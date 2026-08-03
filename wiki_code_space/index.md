# wiki_code_space

Project wiki for code_space that captures semantic intent, rationale,
and business context. It can complement Graphifyy structural topology when a
graph exists, but it is maintained independently.
This index is optimized for coding-agent navigation and fast retrieval.

## Architecture
Create `architecture/<topic>.md` only when there is durable system context,
configuration behavior, data flow, or a cross-module contract worth preserving.
Read relevant architecture notes before changing matching behavior.

## Decisions
Create `decisions/adr-YYYYMMDD-<topic>.md` only for real architectural
decisions with durable tradeoffs. Read relevant ADRs before changing decision
logic.

## Business QA
Create `qa/business.md` or focused `qa/<topic>.md` only when there are
stakeholder-visible outcomes, alert-quality checks, operational risks, or
decision-impact checks to preserve.

## Technical QA
Create `qa/technical.md` or focused `qa/<topic>.md` only when there are
regression risks, invariants, interfaces, or failure modes to preserve.

## Sessions
Create `sessions/YYYY-MM-DD-<topic-slug>.md` only when a failed approach led to
a corrected implementation or a reusable constraint was discovered.

## Agent Access
Run `wiki-engine init <project-path> --llm <harness>` to initialize the wiki and
register project-level refresh and query skills in one operation. Supported
harnesses are Copilot, Codex, Claude, and Gemini; Gemini is the default.

## Glossary
Create `glossary/<term-slug>.md` only for project-specific terms,
abbreviations, or overloaded meanings that reduce ambiguity.

## First Files To Load
- index.md
- folder-specific notes only when the user request or changed module makes them relevant

## Never Auto-Read
- stage/
