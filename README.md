# wiki-code-space

Lightweight Python-first wiki workflow package for analytics projects where
the wiki stores semantic context. Blog link for motivation behind this repository [Blog Wiki Code Space](https://r2rahul.github.io/r2rahul/posts/2026-07-09-wiki-code-space/)

## Installation

### Option 1: Using `uv` (Recommended)

Build and install from source with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run wiki_wspace --help
```

Alternatively, use the provided Makefile:

```bash
make install
```

### Option 2: Using `make`

Install dependencies and build the wheel:

```bash
make build
```

Then install the generated wheel:

```bash
pip install dist/wiki_code_space-*.whl
# or with uv:
uv pip install dist/wiki_code_space-*.whl
```

### Option 3: Install pre-built wheel

Download the pre-built `.whl` file from the [GitHub releases page](https://github.com/r2rahul/wiki-code-space/releases), then install:

```bash
pip install wiki_code_space-0.5.0-py3-none-any.whl
# or with uv:
uv pip install wiki_code_space-0.5.0-py3-none-any.whl
```

After installation, one command-line entry point is available:

```bash
wiki_wspace --help
```

qmd is optional and is not installed as a wheel dependency. Without it,
`wiki_wspace` uses deterministic index-based Markdown search. That fallback is a
good fit for wikis with roughly 100 Markdown files or fewer; install qmd for
larger wikis.

## Initialize a project and its Agent Skills

One command initializes the wiki workflow and the selected agent harness in an
existing project directory:

```bash
wiki_wspace init /path/to/existing-project --qmd-index --llm gemini
```

Gemini is the default, so `--llm gemini` can be omitted:

```bash
wiki_wspace init /path/to/existing-project --qmd-index
```

Use `--llm` to select any supported harness:

```bash
wiki_wspace init /path/to/existing-project --llm copilot
wiki_wspace init /path/to/existing-project --llm codex
wiki_wspace init /path/to/existing-project --llm claude
wiki_wspace init /path/to/existing-project --llm gemini
```

Initialization creates the configuration and wiki scaffold, installs two
project-specific skills, and adds a marked section to the selected harness
instruction file. Existing handwritten instructions are preserved and skill
installation is idempotent.

### Supported harness paths

| Harness | Instruction file | Skill directory |
| --- | --- | --- |
| GitHub Copilot | `.github/copilot-instructions.md` | `.agents/skills/` |
| Codex | `AGENTS.md` | `.agents/skills/` |
| Claude | `CLAUDE.md` | `.claude/skills/` |
| Gemini | `GEMINI.md` | `.gemini/skills/` |

### Generated commands

Project names are cleaned to lowercase ASCII letters and numbers, then shortened
to their first two and last two characters. Names with four or fewer characters
remain unchanged. For example, `code_space` becomes `coce`, which creates
`wiki_coce` and exposes:

- `/wiki-ref-coce` — updates the semantic wiki after code,
  configuration, test, architecture, or business-behavior changes.
- `/wiki-query-coce` — searches the wiki for rationale, architecture,
  decisions, configuration semantics, business context, QA constraints,
  glossary terms, and reusable failure lessons.

The rule applies to both the target directory name and a value supplied with
`--project`. For example, `My Project!` becomes `myct`.

## Recommended workflow

Initialize the project and chosen harness, then query and refresh the wiki as
part of normal development:

```bash
# 1. Create the wiki scaffold and Codex skills in the target project.
wiki_wspace init /path/to/project --qmd-index --llm codex

# 2. Run subsequent commands from that project root.
cd /path/to/project

# 3. Search durable project knowledge before broad code exploration.
wiki_wspace search "why is volatility_penalty capped" -n 10

# 4. Refresh semantic artifacts after behavior or documentation changes.
wiki_wspace update
```

## Initialize an existing project

The unified command creates:

- `config/wiki_engine.yaml`
- `wiki_<project>/index.md`
- `wiki_<project>/log.md`
- `wiki_<project>/qmd.yml`
- the wiki architecture, decisions, QA, sessions, glossary, and protected
  `stage/` directories
- the selected harness instruction file
- the refresh and query Agent Skills, including the refresh workflow reference

Without `--project`, every initialization derives the compact name from the
target directory. Supplying `--project` applies the same cleaning and shortening
rule to that value. Existing config naming keys are updated consistently.
Initialization does not create placeholder knowledge notes; semantic notes are
added later only when source-grounded context exists.

For a newly created configuration, qmd indexing is enabled by default. Make the
choice explicit with:

```bash
wiki_wspace init /path/to/existing-project --qmd-index
wiki_wspace init /path/to/existing-project --no-qmd-index
```

Override the inferred project name or config location when needed:

```bash
wiki_wspace init /path/to/existing-project \
  --project demand_forecasting \
  --config config/wiki_engine.yaml \
  --llm claude
```

## Search the wiki

Use the wrapper command instead of calling qmd directly. It automatically uses
qmd when available and healthy, then falls back to deterministic Markdown
search while preserving configured exclusions:

```bash
wiki_wspace search "why volatility_penalty changed" --project code_space -n 10
```

The output reports `backend=qmd` or `backend=markdown`. Markdown results include
the relative path, first matching line, relevance score, and snippet. The
fallback is intended for wikis of roughly 100 Markdown files or fewer; install
qmd for larger collections.

The `stage/` subtree is excluded from both qmd indexing and Markdown fallback
search. Agents should inspect it only when the user names an exact stage path.

## Update the wiki

Run one coherent update after changes that affect durable project semantics:

```bash
wiki_wspace update --project code_space
```

The update command orchestrates:

1. Wiki scaffold and note updates.
2. Session note distillation into permanent notes.
3. Graph-compatible bridge edge extraction from code references.
4. qmd collection refresh and best-effort embedding when qmd indexing is
   enabled.
5. Append-only `log.md` update entry.

## qmd indexing and search

qmd is an optional accelerator, not a Python package dependency. When enabled
and installed, `init` and `update` register the wiki collection and attempt
embedding refresh as a non-blocking optimization:

```bash
qmd collection add wiki_coce --name wiki_coce
qmd embed -c wiki_coce
```

If qmd is missing, collection registration fails, or embeddings are unavailable,
the CLI reports the fallback and continues. Search remains usable without qmd.

## Graphify integration

To help Graphifyy cluster business logic with code, write wiki entries with
explicit code paths, function names, and config names. Graphifyy can use these
lexical overlaps as bridge signals when building graph communities.

Example wiki entry:

```markdown
Target: src/models/forecasting.py -> run_forecast()
Config Parameter: volatility_penalty inside config.yaml
Business Context: Increasing volatility_penalty above 0.5 reduces false-positive
alerts in the dashboard. We prioritize reducing false positives because the ops
team experiences alert fatigue.
```

Because `src/models/forecasting.py`, `run_forecast()`, and `config.yaml` are
named directly, graph communities can connect the wiki rationale to the
forecasting code. When an agent queries the graph about forecasting, it can
retrieve both implementation context and business rationale.
