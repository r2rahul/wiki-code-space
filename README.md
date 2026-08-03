# wiki-code-space

Lightweight Python-first wiki workflow package for analytics projects where
the wiki stores semantic context. Blog link for motivation behind this repository [Blog Wiki Code Space](https://r2rahul.github.io/r2rahul/posts/2026-07-09-wiki-code-space/)

## Installation

### Option 1: Using `uv` (Recommended)

Build and install from source with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python -m wiki_engine.cli --help
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
pip install wiki_code_space-0.3.0-py3-none-any.whl
# or with uv:
uv pip install wiki_code_space-0.3.0-py3-none-any.whl
```

After installation, the `wiki-engine` command will be available:

```bash
wiki-engine --help
```

qmd is optional and is not installed as a wheel dependency. Without it,
wiki_engine uses deterministic index-based Markdown search. That fallback is a
good fit for wikis with roughly 100 Markdown files or fewer; install qmd for
larger wikis.

## Agent Skill installers

The base package is CLI-only. `init` and `update` never install Agent Skills or
modify assistant instruction files. Run the installer from a project root to
register wiki support for the harness used in that project:

```bash
cd /path/to/project
wiki-engine install copilot
wiki-engine install codex
wiki-engine install claude
wiki-engine install gemini
```

Each command installs two project-specific skills and adds a small, marked
section to the selected harness instruction file. Existing handwritten content
is preserved, repeated installation is idempotent, and legacy unsuffixed
`wiki-engine` blocks are migrated automatically. If
`config/wiki_engine.yaml` does not exist, installation creates it in that
project root using the normalized directory name (or `--project` value).

### Supported harnesses and project paths

| Harness | Instruction file | Skill directory |
| --- | --- | --- |
| GitHub Copilot | `.github/copilot-instructions.md` | `.agents/skills/` |
| Codex | `AGENTS.md` | `.agents/skills/` |
| Claude | `CLAUDE.md` | `.claude/skills/` |
| Gemini | `GEMINI.md` | `.gemini/skills/` |

Installation is project-scoped by default. Omitting the harness selects Gemini:

```bash
wiki-engine install
```

Use `--project` only to override the `project_name` loaded from
`config/wiki_engine.yaml`:

```bash
wiki-engine install codex --project demand_forecasting
```

### User-level installation

Pass `--user` to write only beneath the user profile. No project instruction or
skill files are changed:

```bash
wiki-engine install codex --user
```

| Harness | User instruction file | User skill directory |
| --- | --- | --- |
| GitHub Copilot | `~/.copilot/copilot-instructions.md` | `~/.agents/skills/` |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills/` |
| Claude | `~/.claude/CLAUDE.md` | `~/.claude/skills/` |
| Gemini | `~/.gemini/GEMINI.md` | `~/.gemini/skills/` |

User-level skills are still project-specific, so run the command from a project
containing `config/wiki_engine.yaml`, or provide `--config` and `--project`.

### Generated commands

For a project named `code_space`, installation exposes:

- `/wiki-ref-code-space` — updates the semantic wiki after code,
  configuration, test, architecture, or business-behavior changes.
- `/wiki-query-code-space` — searches the wiki for rationale, architecture,
  decisions, configuration semantics, business context, QA constraints,
  glossary terms, and reusable failure lessons.

Command names use lowercase kebab-case. Projects with four or fewer words use
all words; longer names use the first two and last two words. Special characters
are removed, and names are capped at the Agent Skills 64-character limit.

## Recommended workflow

Install the harness you use, then query and refresh the wiki as part of normal
development. A separate `init` step is optional because `install` creates a
missing project configuration:

```bash
# 1. Run commands from the project root.
cd /path/to/project

# 2. Register one harness. Gemini is the default when omitted.
wiki-engine install codex

# 3. Create the wiki scaffold immediately (otherwise the first refresh does it).
wiki-engine update

# 4. Search durable project knowledge before broad code exploration.
wiki-engine search "why is volatility_penalty capped" -n 10

# 5. Refresh semantic artifacts after behavior or documentation changes.
wiki-engine update
```

The equivalent module form is available for every command:

```bash
python -m wiki_engine.cli install codex
python -m wiki_engine.cli search "why is volatility_penalty capped" -n 10
python -m wiki_engine.cli update
```

## Initialize an existing project

Initialize any existing project directory:

```bash
wiki-engine init /path/to/existing-project
```

`init` normalizes the directory name into a project identifier unless
`--project` is supplied. It creates:

- `config/wiki_engine.yaml`
- `wiki_<project>/index.md`
- `wiki_<project>/log.md`
- `wiki_<project>/qmd.yml`
- the wiki architecture, decisions, QA, sessions, glossary, and protected
  `stage/` directories

It does not install Agent Skills, modify harness prompts, or create placeholder
knowledge notes. Semantic notes are added later only when source-grounded
project context exists.

For a newly created configuration, qmd indexing is enabled by default. Make the
choice explicit with:

```bash
wiki-engine init /path/to/existing-project --qmd-index
wiki-engine init /path/to/existing-project --no-qmd-index
```

Override the inferred project name or config location when needed:

```bash
wiki-engine init /path/to/existing-project \
  --project demand_forecasting \
  --config config/wiki_engine.yaml
```

## Search the wiki

Use the wrapper command instead of calling qmd directly. It automatically uses
qmd when available and healthy, then falls back to deterministic Markdown
search while preserving configured exclusions:

```bash
wiki-engine search "why volatility_penalty changed" --project code_space -n 10
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
wiki-engine update --project code_space
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
qmd collection add wiki_code_space --name wiki_code_space
qmd embed -c wiki_code_space
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
