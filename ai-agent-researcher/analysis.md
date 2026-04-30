# Capability: Experiment Analysis

## Overview
Analyzes experiment results against TECHSPEC tiers and determines if the hypothesis was validated.

## Operating Instructions
1. **Inputs:** Read `docs/techspecs/TECHSPEC_EXP_[ID].md` and logs from tracking tools (`wandb`/`mlflow`/`clearml`).
2. **Evaluation:** Compare metrics against the "Best case", "Target", and "Worst case" tiers.
3. **Verdict:**
   - **Pass:** Move to next experiment or HPO.
   - **Fail:** Trigger a Revision cycle.
4. **Output:** Generate `docs/experiments/07_Analysis_EXP_[ID].md`.
