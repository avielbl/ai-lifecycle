# Capability: Technical Specification (TECHSPEC)

## Overview
Locks the experiment contract: parameters, compute budget, dataset choices, and tiered success criteria.

## Operating Instructions
1. **Input:** Read architecture doc and detailed design.
2. **Create experiment folder:** `{ai_output_folder}/experiments/{ID}/` (e.g., `docs/experiments/E1/`).
3. **Contract writing:** Define hypothesis, dataset substitutions, preprocessing pipelines, model architectures with param counts, training spec, fine-tuning arms, acceptance gates (Tier 1/2/3), compute placement, execution plan, and risks.
4. **Sign-off:** Request approval from the AI Researcher.
5. **Output:** `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`

## Template Sections
- Experiment Identity (ID, title, branch, hypothesis, owner)
- Paper/Prior-Art Reference (if reproducing)
- Dataset Substitutions (if applicable)
- Preprocessing Pipelines (per modality)
- Pretraining / Training Specification (params table)
- Fine-Tuning Arms (table: arm, init, architecture, data, task, param counts)
- Acceptance Gates (Tier 1 mandatory, Tier 2 informational, Tier 3 stretch)
- Compute (instance, GPU, zone, estimated wall-clock)
- Execution Plan (numbered phases)
- Key Scripts
- Risks
