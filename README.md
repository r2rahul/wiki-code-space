# wiki-code-space

Lightweight Python-first wiki workflow package for analytics projects where
Graphifyy stores structural context and Wiki stores semantic context.

## Core command

Run one coherent update call:

```bash
python -m wiki_engine.cli update --project code_space
```

## Migration for existing projects

Migrate any existing project folder into this wiki workflow:

```bash
python -m wiki_engine.cli migrate /path/to/existing-project
```

Optional override for project name and config path:

```bash
python -m wiki_engine.cli migrate /path/to/existing-project --project demand_forecasting --config config/wiki_engine.yaml
```

Script variant:

```bash
python scripts/s01a_migrate_to_wiki_workflow.py /path/to/existing-project
```

This command orchestrates:

1. Wiki scaffold and note updates.
2. Session note distillation into permanent notes.
3. Graph bridge edge extraction from code references.
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
