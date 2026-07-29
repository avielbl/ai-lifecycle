# Capability: Hyperparameter Optimization (HPO)

## Overview
Runs automated search for optimal hyperparameters using Optuna, W&B Sweeps, Ray Tune, or ClearML.

## Operating Instructions
1. **Verification:** Confirm with the AI Researcher that the baseline architecture is stable.
2. **Config:** Define the search space in `docs/techspecs/HPARAM_EXP_[ID].md`. **Memory retrieval:** scan the memory index for `result` entries whose tags match the model/paradigm, and read the matching entry files — confirmed ranges seed the search space. **Ask, don't guess:** present candidate search spaces and budgets with a brief recommendation, and let the user decide.
3. **Review Gate:** Stop after writing the search-space document. Summarize it, ask the user to review and comment, and wait for explicit approval before running the sweep.
4. **Execute:** Run the HPO sweep.
5. **Analyze:** Record the best parameters and update the TechSpec for the next full run.
6. **Review Gate:** Stop. Summarize the best parameters and TechSpec updates, ask the user to review and comment, and wait for explicit approval before the next full run.
7. **Memory Update (mandatory, after approval):** Distill new atomic facts from the HPO report into `{ai_output_folder}/memory/entries/` using the entry template — `result` entries (confirmed hyperparameter ranges and best values) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.
