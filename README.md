# wiki-code-space

Lightweight Python-first wiki workflow package for analytics projects where
the wiki stores semantic context. When a Graphifyy graph exists, the wiki
bridge metadata can complement its structural context, but Graphifyy is not
required to maintain the wiki.

## Core command

Run one coherent update call:

```bash
python -m wiki_engine.cli update --project code_space
```

## Initialize existing projects

Initialize any existing project folder with this wiki workflow:

```bash
python -m wiki_engine.cli init /path/to/existing-project
```

Optional override for project name and config path:

```bash
python -m wiki_engine.cli init /path/to/existing-project --project demand_forecasting --config config/wiki_engine.yaml
```

Script variant:

```bash
python scripts/s01a_initialize_wiki_workflow.py /path/to/existing-project
```

## Agent instruction installers

Install wiki maintenance instructions for a project assistant:

```bash
python -m wiki_engine.cli codex --project code_space
python -m wiki_engine.cli vscode --project code_space
python -m wiki_engine.cli claude --project code_space
python -m wiki_engine.cli gemini --project code_space
```

This command orchestrates:

1. Wiki scaffold and note updates.
2. Session note distillation into permanent notes.
3. Graph-compatible bridge edge extraction from code references.
4. qmd index refresh if qmd is installed.
5. Append-only `log.md` update entry.

## qmd query convention

Use collection-qualified queries:

```bash
qmd query "why volatility_penalty changed" -c wiki_code_space --json -n 10
```

## Build and test

```bash
make test
make build
```
