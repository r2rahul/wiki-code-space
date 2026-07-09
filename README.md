# wiki-code-space

Lightweight Python-first wiki workflow package for analytics projects where
the wiki stores semantic context. When a Graphifyy graph exists, the wiki
bridge metadata can complement its structural context, but Graphifyy is not
required to maintain the wiki.

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

Download the pre-built `.whl` file from the [GitHub releases page](https://github.com/r2rahul/wiki_code_space/releases), then install:

```bash
pip install wiki_code_space-0.1.0-py3-none-any.whl
# or with uv:
uv pip install wiki_code_space-0.1.0-py3-none-any.whl
```

After installation, the `wiki-engine` command will be available:

```bash
wiki-engine --help
```

## Agent instruction installers

Install wiki maintenance instructions for a project assistant:

```bash
python -m wiki_engine.cli codex --project code_space
python -m wiki_engine.cli vscode --project code_space
python -m wiki_engine.cli claude --project code_space
python -m wiki_engine.cli gemini --project code_space
```

Installer commands write assistant instructions plus shared prompt guides under
`wiki_<project>/templates/` inside the initialized project.

Use the prompt guides by use case:

- `llm_wiki_workflow_guide.md`: normal incremental wiki maintenance during
  ongoing development.
- `wiki_first_init_bootstrap.md`: one-time `/wiki-bootstrap "<seed_text>"`
  workflow when enabling wiki maintenance in a project that already has working
  code and existing decisions.

This command orchestrates:

1. Wiki scaffold and note updates.
2. Session note distillation into permanent notes.
3. Graph-compatible bridge edge extraction from code references.
4. qmd collection refresh and best-effort embedding when qmd indexing is
   enabled.
5. Append-only `log.md` update entry.


## Core command

Run one coherent update call:

```bash
python -m wiki_engine.cli update --project code_space
# or if installed as a package:
wiki-engine update --project code_space
```

## Initialize existing projects

Initialize any existing project folder with this wiki workflow:

```bash
python -m wiki_engine.cli init /path/to/existing-project
```

Init creates the wiki folders, `index.md`, `log.md`, `qmd.yml`, agent
instructions, and shared prompt guides. It does not create example notes under
`sessions/`, `qa/`, `glossary/`, `architecture/`, or `decisions/`; those notes
are created later only when source-grounded project context exists.

qmd indexing is enabled by default. When qmd is installed, init/update register
the wiki folder as a collection, then try embeddings as a non-blocking
acceleration:

```bash
qmd collection add wiki_code_space --name wiki_code_space
qmd embed -c wiki_code_space
```

If embeddings fail because no embedding model is available, qmd keyword search
and the markdown fallback remain available. Use the explicit flags when you want
to make the indexing choice visible in automation:

```bash
python -m wiki_engine.cli init /path/to/existing-project --qmd-index
python -m wiki_engine.cli init /path/to/existing-project --no-qmd-index
```

Optional override for project name and config path:

```bash
python -m wiki_engine.cli init /path/to/existing-project --project demand_forecasting --config config/wiki_engine.yaml
```

Script variant:

```bash
python scripts/s01a_initialize_wiki_workflow.py /path/to/existing-project
```

## qmd indexing and search

qmd is the default accelerator for wiki indexing and search. If qmd is missing
or unhealthy, wiki_engine logs a warning and falls back to deterministic
markdown search over the wiki, while preserving the stage-folder exclusions.

Use collection-qualified queries:

```bash
qmd query "why volatility_penalty changed" -c wiki_code_space --json -n 10
```

Or use the wiki_engine search command, which applies the same qmd-first
fallback behavior:

```bash
python -m wiki_engine.cli search "why volatility_penalty changed" --project code_space -n 10
```

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
