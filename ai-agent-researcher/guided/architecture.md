# Guided Scaffolding for Architecture Design

Follow `architecture.md` (canonical). This overlay adds explicit scaffolding — same artifact, same path, same gate. Where it conflicts with the canonical file, this file wins.

If your model has a reasoning toggle (e.g. Nemotron's `/no_think`), keep reasoning ON for this capability.

## Micro-Steps (do not reorder)

1. Read `docs/Research_Thesis.md` and `docs/eda/EDA_Report.md`. Do not continue until you have restated the Active Hypothesis and the 3 EDA findings that most constrain the design.
2. Scan `{ai_output_folder}/memory/index.md` for `finding`, `result`, and `decision` rows whose tags match the problem or candidate paradigms; Read only those entry files. Do not continue until step 2's output exists (list of entries read, or "none matched") — rejected paradigms constrain the design.
3. Present the closed choices below to the user and record the answers. Do not continue until the user has decided.
4. Fill in the Architecture skeleton below and write it to `docs/architecture/Architecture.md`. Do not continue until the file exists with every `<placeholder>` replaced.
5. **Review Gate (hard stop):** complete the self-check below, summarize the architecture decisions, wait for explicit user approval before handing off to Detailed Design.
6. Write the memory entries (template below) and their index rows. Then stop.

## Closed Choices (ask, don't guess — present these to the user)

- **Model paradigm** — choose exactly one: (a) gradient boosting / classical ML (tabular, small-to-medium data), (b) neural network trained from scratch, (c) fine-tuned pretrained model (transformer or other foundation model), (d) statistical/rule baseline only (validate the pipeline first). If unsure, pick (a).
- **Experiment tracking** — choose exactly one: (a) keep the tracker already set in `ai_experiment_tracker` config (do not revisit without explicit user consent), (b) mlflow, (c) wandb, (d) clearml. If unsure, pick (a). Configuration only — install nothing; the tracker SDK arrives in Stage 5 (`infra`) via `uv sync`.
- **Optimization setup** — choose exactly one: (a) the framework's standard loss/objective for the task type, (b) a cost-sensitive or weighted variant (justified by EDA class imbalance), (c) a custom objective (justify from the Thesis). If unsure, pick (a).

## Copy-This Skeleton — `docs/architecture/Architecture.md`

```markdown
# Architecture

## Paradigm Choice
<chosen paradigm and one-paragraph justification tracing to the Research Thesis and EDA findings>

## Framework Stack
- <framework/library>: <role> (recorded only — nothing installed before Stage 5)

## Model Topology
<model family, layers/trees/components, input and output shapes>

## Loss & Optimization
<loss/objective function(s), optimizer or boosting parameters>

## Experiment Tracking
- Tool: <wandb | mlflow | clearml>
- <project/workspace naming, what gets logged>

## Thesis Traceability
<how each choice above serves the Active Hypothesis>

## Rejected Alternatives
- <paradigm/stack>: <reason rejected>
```

## Pre-Gate Self-Check (complete before the Review Gate)

- [ ] Every section header from the skeleton is present; no `<placeholder>` remains
- [ ] The paradigm choice traces explicitly to the Research Thesis and at least one EDA finding
- [ ] At least one rejected alternative is documented with its reason
- [ ] The tracker choice respects an existing `ai_experiment_tracker` config value (or the user explicitly consented to change it)
- [ ] Nothing was installed — the stack is recorded only

## Memory Entries — fill in literally (this capability writes `decision` and `finding` entries)

One `decision` entry for the paradigm choice AND one per rejected paradigm; `finding` entries for prior-art facts that drove the choice. File: `{ai_output_folder}/memory/entries/<id>-<slug>.md`

```markdown
---
id: <dec-|fnd-><slug>
type: <decision | finding>
stage: 3
exp_id: null
tags: [<tag1>, <tag2>]
date: <YYYY-MM-DD>
status: active
superseded_by: null
---
**Fact:** <one atomic, reusable fact — the choice made or paradigm rejected, with reason; entry ≤15 lines>
**Why:** <what a future cycle needs this for>
**Links:** [[<related-entry-id>]] — Source: docs/architecture/Architecture.md
```

Index row per entry, appended to `{ai_output_folder}/memory/index.md`:
`| <id> | <decision|finding> | 3 | - | <tags> | <hook, ≤100 chars> |`

## Hard Rule

One capability per session: finish Architecture, write the memory entries and their index rows, then stop. Do not start Detailed Design or any other capability in this session.
