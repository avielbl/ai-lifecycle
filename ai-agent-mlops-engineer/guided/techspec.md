# Guided Scaffolding for Technical Specification (TECHSPEC)

Follow `techspec.md` (canonical). This overlay adds explicit scaffolding — same artifact, same path, same gate. Where it conflicts with the canonical file, this file wins.

If your model has a reasoning toggle (e.g. Nemotron's `/no_think`), keep reasoning ON for this capability.

## Micro-Steps (do not reorder)

1. Read `docs/architecture/Architecture.md` and `docs/design/Detailed_Design.md`. Do not continue until you have listed the EXP-* task(s) this contract covers.
2. Scan `{ai_output_folder}/memory/index.md` for `result` and `decision` rows whose tags intersect this experiment's topic; Read only those entry files. Do not continue until step 2's output exists (list of entries read, or "none matched") — validated params and rejected alternatives inform the contract.
3. Create the experiment folder `{ai_output_folder}/experiments/{ID}/` (e.g. `docs/experiments/E1/`). Do not continue until the folder exists.
4. Read `configs/project_infra.yaml` for data location, artifact registry, and compute topology. Present the closed choices below to the user. Do not continue until the user has decided.
5. Fill in the TECHSPEC skeleton below and write it to `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`. Do not continue until the file exists with every `<placeholder>` replaced.
6. Request sign-off from the AI Researcher.
7. **Review Gate (hard stop):** complete the self-check below, summarize the contract (hypothesis, arms, gates, compute), wait for explicit user approval before any infra or experiment work begins. Then stop.

## Closed Choices (ask, don't guess — present these to the user)

- **Tier-1 threshold basis** — choose exactly one: (a) the Research Thesis "minimum viable" tier applied to this experiment's metric, (b) beat the EDA baseline by a stated margin, (c) a domain-mandated hard threshold (regulatory/cost). If unsure, pick (a).
- **Dataset choice** — choose exactly one: (a) the full dataset as characterized in EDA, (b) a documented substitution (smaller/proxy dataset — record it in Dataset Substitutions), (c) a stratified subsample for a fast first contract. If unsure, pick (a).
- **Compute placement** — choose exactly one: (a) as declared in `configs/project_infra.yaml`, (b) local smoke-scale only for this experiment, (c) a documented deviation (record the reason). If unsure, pick (a).

## Copy-This Skeleton — `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`

```markdown
# TECHSPEC — <ID>: <title>

## Experiment Identity
- ID: <ID> | Title: <title> | Branch: <git branch> | Owner: <name>
- Hypothesis: <one sentence>

## Paper/Prior-Art Reference
<citation or "none — original design">

## Dataset Substitutions
<table or "none">

## Preprocessing Pipelines
- <modality>: <steps>

## Pretraining / Training Specification
| param | value |
|-------|-------|
| <param> | <value> |

## Fine-Tuning Arms
| arm | init | architecture | data | task | param count |
|-----|------|--------------|------|------|-------------|
| <arm> | <init> | <arch> | <data> | <task> | <count> |

## Acceptance Gates
- Tier 1 (mandatory): <metric> >= <numeric threshold>
- Tier 2 (informational): <metric> >= <numeric threshold>
- Tier 3 (stretch): <metric> >= <numeric threshold>

## Compute
- Instance: <instance> | GPU: <gpu or n/a> | Zone: <zone or local> | Est. wall-clock: <estimate>
- (from configs/project_infra.yaml: <data location, artifact registry, compute topology>)

## Execution Plan
1. <phase>
2. <phase>

## Key Scripts
- <path>: <purpose>

## Risks
- <risk>: <mitigation>
```

## Pre-Gate Self-Check (complete before the Review Gate)

- [ ] Every section header from the skeleton is present; no `<placeholder>` remains
- [ ] Every tier has a numeric threshold and a named metric; Tier 1 is marked mandatory
- [ ] Every arm row has a param count
- [ ] Compute section reflects `configs/project_infra.yaml` (or documents the deviation)
- [ ] Execution Plan phases are numbered and each names its script
- [ ] Nothing was installed — installs happen only in `infra` (Stage 5)

## Memory — read-only for this capability

This capability writes NO memory entries (contracts are per-experiment). You already read `result`/`decision` entries in step 2 — do not write to `{ai_output_folder}/memory/` at all.

## Hard Rule

One capability per session: finish the TECHSPEC and its Review Gate, then stop (no memory rows to write here). Do not start infra, experiment, or any other capability in this session.
