# Guided Scaffolding for Ideation & Problem Framing

Follow `ideation.md` (canonical). This overlay adds explicit scaffolding — same artifacts, same paths, same gates. Where it conflicts with the canonical file, this file wins.

If your model has a reasoning toggle (e.g. Nemotron's `/no_think`), keep reasoning ON for this capability.

## Micro-Steps (do not reorder)

1. Read `{output_folder}/research/Domain_Knowledge_Base.md`. Do not continue until you have quoted its 3 strongest findings back to the user. If the file is missing, stop — run Domain Research first.
2. Scan `{ai_output_folder}/memory/index.md` for `background` and `finding` rows whose tags match the domain; Read only those entry files. Do not continue until step 2's output exists (a short list of the entries you read, or "none matched").
3. Fill in the Research Thesis skeleton below and write it to `docs/Research_Thesis.md`. Do not continue until the file exists with every `<placeholder>` replaced.
4. **Review Gate (hard stop):** complete the self-check below, summarize hypothesis + tiers, wait for explicit user approval.
5. Fill in the PRD skeleton below and write it to `docs/prd/PRD.md`. Do not continue until the file exists with every `<placeholder>` replaced.
6. **Review Gate (hard stop):** complete the self-check below, summarize requirements + scope, wait for explicit user approval.
7. List candidate packages; after user confirmation only, record them via `uv add --no-sync <package>`. Never run `uv sync` or install anything.
8. Write the memory entry (template below) and its index row. Then stop.

## Closed Choices (ask, don't guess — present these to the user)

- **Hypothesis framing** — choose exactly one: (a) performance hypothesis ("a model can reach X on task Y with the available data"), (b) comparative hypothesis ("paradigm/approach A beats the current baseline B"), (c) feasibility hypothesis ("the available data is sufficient to support task Y at all"). If unsure, pick (a).
- **Success-tier basis** — choose exactly one: (a) absolute metric thresholds derived from domain failure costs, (b) relative improvement over an existing system or naive baseline, (c) cost/error-budget thresholds (e.g. false-positive cost per month). If unsure, pick (a).

## Copy-This Skeleton — `docs/Research_Thesis.md`

```markdown
# Research Thesis

## Active Hypothesis
<one sentence: the single most important question this project must answer>

## Domain Failure Costs
<what failure looks like in real-world terms; quantify where possible>

## Data Characterization
<what data is available, its known quality, and its known limitations>

## Success Tiers
- **Minimum viable:** <metric> >= <numeric threshold> on <dataset/split>
- **Target:** <metric> >= <numeric threshold> on <dataset/split>
- **Aspirational:** <metric> >= <numeric threshold> on <dataset/split>

## Hypothesis History
_Blank at v1.0; updated at each Revision Audit cycle._
```

## Copy-This Skeleton — `docs/prd/PRD.md`

```markdown
# Product Requirements Document

## Problem Statement
<one paragraph, no jargon>

## User/Stakeholder Needs
<who is affected and what they need>

## Functional Requirements
- FR-001: <requirement> (source: <Domain Knowledge Base finding>)
- FR-002: <requirement> (source: <Domain Knowledge Base finding>)

## Non-Functional Requirements
- NFR-001: <latency / throughput / resource / regulatory constraint>

## Out of Scope
- <explicit exclusion>
```

## Pre-Gate Self-Check (complete before each Review Gate)

- [ ] Every section header from the skeleton is present; no `<placeholder>` remains
- [ ] Every success tier has a numeric threshold and a named metric
- [ ] Every FR-* references a finding in the Domain Knowledge Base (unrooted requirements rejected)
- [ ] Out of Scope is non-empty
- [ ] No package was installed (`uv add --no-sync` placeholders only, and only after user confirmation)

## Memory Entry — fill in literally (this capability writes `evolution` entries only)

File: `{ai_output_folder}/memory/entries/evo-<slug>.md`

```markdown
---
id: evo-<slug>
type: evolution
stage: 1.5
exp_id: null
tags: [<tag1>, <tag2>]
date: <YYYY-MM-DD>
status: active
superseded_by: null
---
**Fact:** <why this hypothesis was chosen — one atomic, reusable fact, entry ≤15 lines>
**Why:** <what a future cycle needs this for>
**Links:** Source: docs/Research_Thesis.md
```

Index row to append to `{ai_output_folder}/memory/index.md`:
`| evo-<slug> | evolution | 1.5 | - | <tags> | <hook, ≤100 chars> |`

## Hard Rule

One capability per session: finish Ideation, write the memory entry and its index row, then stop. Do not start EDA, Architecture, or any other capability in this session.
