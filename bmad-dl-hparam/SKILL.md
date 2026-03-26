\---

name: bmad-dl-hparam

description: Acts as a Data Scientist and MLOps Engineer to run structured hyperparameter optimization after a baseline architecture is confirmed to work. Uses Optuna, W&B Sweeps, Ray Tune, or ClearML HPO. Produces a validated best-parameter configuration for the next tuned experiment run. Use this only after Analysis confirms the baseline meets the TECHSPEC's minimum viable tier.

\---



\# BMAD Workflow 07.5: Hyperparameter Optimization (Conditional)



\## 1. Operating Instructions

You are a Data Scientist and MLOps Engineer running structured hyperparameter search. **This stage is conditional.** Run it only after `bmad-dl-analysis` confirms the baseline architecture meets at least the "Worst case (alive)" tier in the TECHSPEC. Running HPO on a broken architecture wastes compute.

Your goal is to find the optimal parameter configuration within the search space defined in the TECHSPEC, then hand off validated parameters to the next `bmad-dl-experiment` run.



1\. **Verify the prerequisite:** Read the latest `docs/experiments/07_Analysis_EXP_[ID].md`, Section F (TECHSPEC Evaluation). Confirm: "Worst case (alive)" tier or better was reached. If not, halt and recommend running `bmad-dl-revision` instead.



2\. **Read the TECHSPEC:** `docs/techspecs/TECHSPEC_EXP_[ID].md` — use Section C as the HPO search space. Do not expand it without updating the TECHSPEC first.



3\. **Run `/bmad-dl-advise`** — check if any past HPO runs exist for a similar search space. Reuse completed trials if possible.



4\. **Select the HPO tool** based on project setup and run the search:

\`\`\`python

\# ── Optuna ───────────────────────────────────────────────────────────────────
import optuna

def objective(trial: optuna.Trial) -> float:
    lr = trial.suggest_float("lr", 1e-5, 1e-2, log=True)
    batch_size = trial.suggest_categorical("batch_size", [256, 512, 1024, 2048])
    dropout = trial.suggest_float("dropout", 0.1, 0.5)
    weight_decay = trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True)
    \# train model, return primary metric
    return val_f1

study = optuna.create_study(
    study_name=f"HPO-EXP-{exp_id}",
    direction="maximize",
    pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=10),
    sampler=optuna.samplers.TPESampler(seed=42),
)
study.optimize(objective, n_trials=50, n_jobs=1, show_progress_bar=True)

print("Best params:", study.best_params)
print("Best value:", study.best_value)
optuna.visualization.plot_param_importances(study).show()

\`\`\`

\`\`\`yaml

\# ── W&B Sweeps (sweeps/sweep_EXP_[ID].yaml) ──────────────────────────────────
program: train.py
method: bayes
metric:
  name: val/f1
  goal: maximize
early_terminate:
  type: hyperband
  min_iter: 5
parameters:
  learning_rate:
    distribution: log_uniform_values
    min: 0.00001
    max: 0.01
  batch_size:
    values: [256, 512, 1024, 2048]
  dropout:
    distribution: uniform
    min: 0.1
    max: 0.5

\`\`\`

\`\`\`bash

\# Launch W&B sweep
wandb sweep sweeps/sweep_EXP_[ID].yaml
wandb agent SWEEP_ID --count 50

\`\`\`

\`\`\`python

\# ── Ray Tune ─────────────────────────────────────────────────────────────────
from ray import tune
from ray.tune.schedulers import ASHAScheduler

def train_fn(config):
    \# your training function using config["lr"], config["batch_size"], etc.
    pass

result = tune.run(
    train_fn,
    config={
        "lr": tune.loguniform(1e-5, 1e-2),
        "batch_size": tune.choice([256, 512, 1024, 2048]),
        "dropout": tune.uniform(0.1, 0.5),
    },
    num_samples=50,
    scheduler=ASHAScheduler(metric="val_f1", mode="max", max_t=100, grace_period=10),
    resources_per_trial={"gpu": 1},
    name=f"HPO-EXP-{exp_id}",
)
best_config = result.get_best_config(metric="val_f1", mode="max")
print("Best config:", best_config)

\`\`\`

\`\`\`python

\# ── ClearML HPO ──────────────────────────────────────────────────────────────
from clearml import Task
from clearml.automation import (
    HyperParameterOptimizer, UniformParameterRange,
    DiscreteParameterRange, LogUniformParameterRange,
)
from clearml.automation.optuna import OptimizerOptuna

\# base_task_id = ID of a completed baseline training Task in ClearML
optimizer = HyperParameterOptimizer(
    base_task_id=base_task_id,
    hyper_parameters=[
        LogUniformParameterRange("lr", min_value=1e-5, max_value=1e-2),
        DiscreteParameterRange("batch_size", values=[256, 512, 1024, 2048]),
        UniformParameterRange("dropout", min_value=0.1, max_value=0.5),
    ],
    objective_metric_title="val",
    objective_metric_series="f1",
    objective_metric_sign="max",
    max_number_of_concurrent_tasks=4,
    optimizer_class=OptimizerOptuna,
    execution_queue="default",
    total_max_jobs=50,
    min_iteration_per_job=10,
    max_iteration_per_job=100,
)
optimizer.start_locally()
optimizer.wait()
top_exps = optimizer.get_top_experiments(top_k=3)
best_params = top_exps[0].get_parameters()

\`\`\`



5\. **CRITICAL:** Do not write the HPO report yet. Present the top-5 parameter configurations with their metrics. Ask:

   \- "Do the best params make domain sense? Are any values outside acceptable real-world constraints?"
   \- "Should we run a confirmation run with the best config before finalizing, or accept these results?"

   Halt and wait.



6\. Upon confirmation, write `docs/techspecs/HPARAM_EXP_[ID].md` with the validated best configuration and update the TECHSPEC for the next tuned run.

\`\`\`bash

git add docs/techspecs/HPARAM_EXP_[ID].md docs/techspecs/TECHSPEC_EXP_[ID].md
git commit -m "docs(hparam): validated best config for EXP-[ID] -- best val/f1=[score]"

\`\`\`



\## 2. Expected Output Template

\`\`\`markdown

\# HPO Results: EXP-[ID]

\## A. Search Summary

\* \*\*Linked Experiment:\*\* EXP-[ID]
\* \*\*HPO Tool:\*\* [Optuna / W&B Sweeps / Ray Tune / ClearML HPO]
\* \*\*Total Trials:\*\* [N completed / M budget]
\* \*\*Search Space:\*\* [Reference to TECHSPEC Section C]
\* \*\*Sweep URL:\*\* [Link to W&B sweep / ClearML HPO task / MLflow experiment]

\## B. Top Configurations

| Rank | lr | batch_size | dropout | val/f1 | Run URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 (best) | 2.3e-4 | 1024 | 0.22 | 0.94 | [link] |
| 2 | 1.8e-4 | 512 | 0.19 | 0.93 | [link] |

\## C. Parameter Importance

\* [Which parameters had the highest impact — from Optuna plot or sweep analysis]
\* [Interactions observed: e.g., "LR and batch size are strongly coupled"]

\## D. Validated Best Configuration (copy-paste ready)

\`\`\`yaml
learning_rate: 2.3e-4
batch_size: 1024
dropout: 0.22
weight_decay: 4.1e-5
\# All other params: fixed as per TECHSPEC_EXP_[ID].md Section C
\`\`\`

\## E. Domain Expert Sign-off

\* [ ] Best params are within real-world acceptable ranges
\* [ ] No anomalous values (e.g., batch size too large for production hardware)
\* \*\*Signed off by:\*\* [Domain Expert name / date]

\## F. Next Step

\* Run `bmad-dl-experiment` with run_type="tuned" using the above config
\* Update `docs/techspecs/TECHSPEC_EXP_[ID+1].md` with these as the baseline params

\`\`\`
