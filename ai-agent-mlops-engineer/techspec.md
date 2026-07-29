# Capability: Technical Specification (TECHSPEC)

## Overview
Locks the experiment contract: parameters, compute budget, dataset choices, and tiered success criteria.

## Operating Instructions
1. **Input:** Read architecture doc and detailed design. **Memory retrieval:** scan the memory index for `result` and `decision` entries whose tags intersect the current experiment's topic, and read the matching entry files before locking parameters — validated params and rejected alternatives inform the contract. (This capability reads the bank only; contracts are per-experiment, so it writes no entries.)
2. **Create experiment folder:** `{ai_output_folder}/experiments/{ID}/` (e.g., `docs/experiments/E1/`).
3. **Contract writing:** Define hypothesis, dataset substitutions, preprocessing pipelines, model architectures with param counts, training spec, fine-tuning arms, acceptance gates (Tier 1/2/3), compute placement, execution plan, and risks. **Ask, don't guess:** for contested choices (tier thresholds, dataset substitutions, compute placement), present the options with a brief recommendation and let the user decide.
4. **Sign-off:** Request approval from the AI Researcher.
5. **Output:** `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`
6. **Review Gate:** Stop. Summarize the contract (hypothesis, arms, gates, compute), ask the user to review and comment, and wait for explicit approval before any infra or experiment work begins.

## Template Sections
- Experiment Identity (ID, title, branch, hypothesis, owner)
- Paper/Prior-Art Reference (if reproducing)
- Dataset Substitutions (if applicable)
- Preprocessing Pipelines (per modality)
- Pretraining / Training Specification (params table)
- Fine-Tuning Arms (table: arm, init, architecture, data, task, param counts)
- Acceptance Gates (Tier 1 mandatory, Tier 2 informational, Tier 3 stretch)
- Compute (instance, GPU, zone, estimated wall-clock)
  - Read `configs/project_infra.yaml` for the data location, artifact registry, and compute topology set at scaffold time.
- Execution Plan (numbered phases)
- Key Scripts
- Risks
