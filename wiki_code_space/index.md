# wiki_code_space

Project wiki for code_space that captures semantic intent, rationale,
and business context. It can complement Graphifyy structural topology when a
graph exists, but it is maintained independently.
This index is optimized for coding-agent navigation and fast retrieval.

## Architecture
- architecture/config_params.md
    Canonical explanation of config knobs and business impact. Read before changing any config defaults.

## Decisions
- decisions/adr-0001-wiki-engine.md
    Decision record for coherent wiki update orchestration and bridging contracts. Read when modifying update behavior.

## Business QA
- qa/business.md
    Business validation checks and expected impact on operators and downstream decisions. Read before changing model thresholds.

## Technical QA
- qa/technical.md
    Technical constraints, failure modes, and regression concerns. Read before refactoring pipelines.

## Sessions
- sessions/_template.md
    Template for session ingestion notes before distillation. Read before adding a new session note.

## LLM Maintenance
- templates/llm_wiki_workflow_guide.md
    Shared agent guide for deciding what semantic content belongs in each wiki folder.
- templates/wiki_first_init_bootstrap.md
    One-time bootstrap prompt for enabling wiki maintenance in an already-developed project.

## Glossary
- glossary/terms.md
    Shared domain and engineering terms for this workspace. Read when terms seem ambiguous.

## First Files To Load
- index.md
- architecture/config_params.md
- qa/business.md
- decisions/adr-0001-wiki-engine.md

## Never Auto-Read
- stage/
