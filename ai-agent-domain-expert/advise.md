# Capability: Advisory

## Overview
Searches past experiment logs, retrospectives, and the team knowledge base to surface validated parameters, failed approaches to avoid, and relevant prior findings — before starting new work. Run this before any new experiment cycle.

## Phase 1: Query Intent
Ask the user what they are about to do (or infer from context):
- "What are you about to build or experiment with?"
- Examples: "Starting HPO on a fine-tuned transformer", "Building an XGBoost baseline for tabular fraud detection", "Designing a new architecture for imbalanced classification"

## Phase 2: Knowledge Base Search
Search the following sources in order:

1. **Retrospectives** — `{output_folder}/knowledge/RETRO_EXP_*.md`
   - Look for: validated configurations, failure post-mortems, lessons learned

2. **Analysis reports** — `{output_folder}/experiments/07_Analysis_EXP_*.md`
   - Look for: TECHSPEC tier outcomes, which approaches met or missed targets

3. **Agent memory** (if enabled) — past architectural patterns and paradigm-specific knowledge

4. **Advisory reports** — `{output_folder}/advisory/` — any prior advisory documents relevant to this query

For each source extract:
- **Validated findings:** hyperparameter ranges, paradigm choices, or strategies confirmed to work
- **Dead ends:** approaches tried and failed (with documented reasons)
- **Warnings:** known failure modes, data pitfalls, integration issues

## Phase 3: Advisory Report
Produce `{output_folder}/advisory/Advisory_[topic]_[date].md` containing:
- **Query Context:** What the user is about to do
- **Validated Findings:** What has worked before that applies now (with source references)
- **Dead Ends to Avoid:** What was tried and failed, and why
- **Open Questions:** What remains unknown that this new work should address
- **Recommended Starting Point:** One concrete, actionable suggestion

If no relevant past experiments exist, state this explicitly: "No prior experiments found for this domain/paradigm." This is useful information, not an error.

> **Headless mode:** search all sources without interactive prompting, produce the advisory report at the configured output path, return the document path on completion.
