# Capability: Experiment Results

## Overview
Produces the raw experiment outputs: learning curves, accuracy metrics, comparison tables, and per-arm timing. Straightforward reporting of what happened — no interpretation.

## Operating Instructions
1. **Input:** Read RUN log and pull metrics from tracking tool (ClearML/WandB/MLflow).
2. **Metrics tables:** Best val accuracy/loss per arm, final train metrics, convergence epoch.
3. **Comparison tables:** As defined in TECHSPEC acceptance gates (e.g., A1 vs A2, A3 vs B2).
4. **Architecture detail:** Layer-by-layer breakdown of each distinct model with param counts (pretrained vs random init). This enables comparing fine-tuning a pretrained model vs training from scratch.
5. **Convergence data:** Time-to-plateau, epochs to 90% of best, wall-clock per epoch.
6. **Training curves:** Include or reference learning curve plots (loss and accuracy vs epoch).
7. **Reproduction:** Exact commands and tracker task IDs.
8. **Output:** `{ai_output_folder}/experiments/{ID}/RESULTS_{timestamp}.md`

## Template Sections
- Results Summary (all arms table: arm, init, architecture, best val metric, train metric, converged?)
- Tier Evaluation (comparison table with deltas and pass/fail)
- Model Architectures and Parameter Counts (layer-by-layer)
- Convergence Data (table: arm, best epoch, time to 90%, wall-clock/epoch)
- Training Curves (embedded or referenced plots)
- Reproduction (commands + task IDs)
