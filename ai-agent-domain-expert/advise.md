# Capability: Advisory

## Overview
Queries the project memory bank (local and imported) to surface validated parameters, failed approaches to avoid, and relevant prior findings — before starting new work. Run this before any new experiment cycle. This capability is a **read-only consumer** of the bank: it writes no entries, except copy-on-use of imported facts (below).

## Phase 1: Query Intent
Ask the user what they are about to do (or infer from context):
- "What are you about to build or experiment with?"
- Examples: "Starting HPO on a fine-tuned transformer", "Building an XGBoost baseline for tabular fraud detection", "Designing a new architecture for imbalanced classification"

## Phase 2: Memory Bank Query
The memory bank at `{ai_output_folder}/memory/` is the primary knowledge source. Query it index-first — do not bulk-read lifecycle documents.

1. **Filter the local index** — using `memory/index.md` (loaded at activation; read it now if not), select rows matching the user's intent: type ∈ {`result`, `decision`, `lesson`} plus any `background`/`finding`/`evolution` rows whose tags match the topic.
2. **Read matching entries** — Read only the matching `entries/*.md` files; follow `[[entry-id]]` links one hop when an entry references its justification. A `~~struck-through~~` hook means the entry was superseded — follow its `superseded_by` to the current fact.
3. **Search imported banks** — if `memory/imports.yaml` exists, read each import's `index.md` and repeat steps 1–2 against its `entries/`. Imports are **read-only — never write to them**; cite imported entries with a prefixed id (e.g. `fraud-v1:res-007`). **Copy-on-use:** if an imported fact becomes load-bearing for the recommendation, copy it into the local bank as a new entry (with a `Source: {import-name}:{entry-id}` line) and append its index row, so the local bank stays self-contained if the import path disappears.
4. **Archive fallback** — if the index yields nothing relevant and `memory/index-archive.md` exists, scan it the same way (it is never loaded at activation).
5. **Document fallback** — open a full lifecycle document only when an entry's `Source:` pointer needs verbatim detail (e.g. `{output_folder}/experiments/{ID}/ANALYSIS_*.md`, `DECISIONS.md`). If no memory bank exists at all, fall back to searching `{output_folder}/experiments/*/ANALYSIS_*.md`, `{output_folder}/experiments/*/DECISIONS.md`, and `{output_folder}/advisory/` directly.

From the matching entries extract:
- **Validated findings:** hyperparameter ranges, paradigm choices, or strategies confirmed to work
- **Dead ends:** approaches tried and failed (with documented reasons)
- **Warnings:** known failure modes, data pitfalls, integration issues

## Phase 3: Advisory Report
Produce `{output_folder}/advisory/Advisory_[topic]_[date].md` containing:
- **Query Context:** What the user is about to do
- **Validated Findings:** What has worked before that applies now (cite entry ids — prefixed for imports — and `Source:` documents)
- **Dead Ends to Avoid:** What was tried and failed, and why
- **Open Questions:** What remains unknown that this new work should address
- **Recommended Starting Point:** One concrete, actionable suggestion

If neither the local nor imported banks hold relevant entries, state this explicitly: "No prior experiments found for this domain/paradigm." This is useful information, not an error.

**Review Gate:** Stop after writing the Advisory Report. Summarize the key findings and recommended starting point, ask the user to review and comment, and wait for explicit approval before any next step.

> **Headless mode:** search all sources without interactive prompting, produce the advisory report at the configured output path, return the document path on completion.
