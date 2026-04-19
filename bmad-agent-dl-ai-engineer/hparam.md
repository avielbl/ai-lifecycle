# Capability: Hyperparameter Optimization (HPO)

## Overview
Runs automated search for optimal hyperparameters using Optuna, W&B Sweeps, Ray Tune, or ClearML.

## Operating Instructions
1. **Verification:** Confirm with the AI Researcher that the baseline architecture is stable.
2. **Config:** Define the search space in `docs/techspecs/HPARAM_EXP_[ID].md`.
3. **Execute:** Run the HPO sweep.
4. **Analyze:** Record the best parameters and update the TechSpec for the next full run.
