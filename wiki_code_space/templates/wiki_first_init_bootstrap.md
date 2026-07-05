# Wiki First-Init Bootstrap Prompt

Use this only once when enabling wiki maintenance in an already working project.
The goal is to start semantic knowledge capture from the current point in time,
not to reconstruct full project history.

When the user types `/wiki-bootstrap "<seed_text>"`, do this sequence:

1. Treat `<seed_text>` as the initial scope anchor: features, modules, decisions,
   constraints, business context, open questions, or known risks.
2. Check whether `wiki_code_space/index.md` and `wiki_code_space/log.md`
   already exist.
3. If the wiki is not initialized, run:

   ```bash
   python -m wiki_engine.cli init <target_dir> --project code_space
   ```

   Init creates wiki folders, index/log/qmd metadata, agent instructions, and
   prompt guides. It does not create example notes in `architecture/`,
   `decisions/`, `qa/`, `sessions/`, or `glossary/`.

4. Load the shared LLM maintenance guide if present:

   ```text
   wiki_code_space/templates/llm_wiki_workflow_guide.md
   ```

5. Add one baseline session note under:

   ```text
   wiki_code_space/sessions/YYYY-MM-DD-first-init-bootstrap.md
   ```

   The note must summarize only:
   - user-provided seed context
   - directly referenced files from `<seed_text>`
   - observable current state
   - assumptions
   - open questions
   - immediate next tracking targets

   Follow the metadata contract and session section order in the shared guide.

6. Run once:

   ```bash
   python -m wiki_engine.cli update --project code_space
   ```

   This refreshes the wiki scaffold, agent guide, bridge metadata, qmd index if
   available, and log entries.

## Rules

- One-time only: do not re-run bootstrap if `wiki_code_space/index.md` and
  `wiki_code_space/log.md` already exist, unless the user explicitly requests
  re-bootstrap.
- Use `init`, not `migrate`, for the public bootstrap path. `migrate` may exist
  only as a compatibility alias.
- Time boundary: record `start_timestamp` using the current timestamp and state
  that wiki knowledge capture starts from that point forward.
- No invented history: do not infer past rationale, old decisions, or business
  context unless grounded in user seed text, directly referenced files, existing
  docs, tests, config, commits, or session artifacts.
- Token-efficient seed handling: prefer `<seed_text>` over wide repo scans. Read
  only files directly referenced in the seed unless the user asks for broader
  discovery.
- Keep the baseline concise: scope, current state, assumptions, open questions,
  and next tracking targets.
- Never scan `wiki_code_space/stage/` unless the user gives an exact file path.
- After bootstrap completes, switch to normal incremental wiki maintenance using
  the installed `wiki maintenance` / `wiki auto refresh` rules.
- In the final response, report:

  ```text
  wiki_bootstrap: ran
  ```

  or:

  ```text
  wiki_bootstrap: skipped (<reason>)
  ```
