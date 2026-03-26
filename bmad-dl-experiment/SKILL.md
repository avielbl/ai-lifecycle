\---

name: bmad-dl-experiment

description: Acts as an AI Developer and Data Scientist to execute training runs against a locked TECHSPEC, log all metrics and artifacts to the experiment tracker (W&B/MLflow/ClearML), and produce an Experiment Log. Use this for all EXP-* tasks. Requires infrastructure from bmad-dl-infra to be complete first.

\---



\# BMAD Workflow 06: Experiment Execution



\## 1. Operating Instructions

You are an expert AI Developer and Data Scientist executing a training experiment. Your job is to run the experiment defined in the TECHSPEC, log everything to the experiment tracker, and capture the run URL for downstream analysis. You do not interpret results here — that is the Analysis skill's job.

**Prerequisite:** `docs/implementation/05_Infra_Log.md` must show smoke test PASS for all required components before starting.



1\. **Run the advisor first:** `/bmad-dl-advise` — surface validated parameters and failure warnings specific to this experiment type.



2\. **Read the TECHSPEC:** Locate `docs/techspecs/TECHSPEC_EXP_[ID].md`.

   \- What is the exact parameter search space? (Section C)
   \- What is the compute budget? (Section D — do not exceed it)
   \- Is this a **baseline run** (first time testing this architecture) or a **tuned run** (using HPO-validated params)?

   > **Baseline runs** use the parameter defaults or a single reasonable starting config.
   > HPO happens only after a baseline confirms the architecture works. Do not sweep during a baseline.



3\. **Configure the experiment run** using the project's tracking tool:

\`\`\`python

\# ── W&B ──────────────────────────────────────────────────────────────────────
import wandb
from lightning.loggers import WandbLogger

logger = WandbLogger(
    project=PROJECT_NAME,
    name=f"EXP-{exp_id}_{run_name}",
    tags=[f"EXP-{exp_id}", run_type],   \# run_type: "baseline" or "tuned"
    config=hyperparams,
    group=f"EXP-{exp_id}",              \# groups all runs for this experiment
)
\# After training:
print("Run URL:", logger.experiment.url)

\# ── MLflow ───────────────────────────────────────────────────────────────────
import mlflow
from lightning.loggers import MLFlowLogger

logger = MLFlowLogger(
    experiment_name=PROJECT_NAME,
    run_name=f"EXP-{exp_id}_{run_name}",
    tracking_uri="./mlruns",
    tags={"exp_id": exp_id, "run_type": run_type, "hypothesis_id": hypothesis_id},
)
\# Log artifacts after training:
mlflow.log_artifact(best_checkpoint_path, artifact_path="checkpoints")
mlflow.pytorch.log_model(model, artifact_path="model")
print("Run URI:", mlflow.get_artifact_uri())

\# ── ClearML ──────────────────────────────────────────────────────────────────
from clearml import Task

task = Task.init(
    project_name=PROJECT_NAME,
    task_name=f"EXP-{exp_id}_{run_name}",
    task_type=Task.TaskTypes.training,
    tags=[f"EXP-{exp_id}", run_type],
)
task.connect(hyperparams)
\# ClearML auto-captures: console output, TensorBoard, git diff, installed packages
\# Manual artifact logging:
task.upload_artifact("best_checkpoint", artifact_object=best_checkpoint_path)
print("Task URL:", task.get_output_log_web_page())

\`\`\`



4\. **Execute training.** Log each run's result (metric + tracking URL) to the Experiment Log as it completes. Do not wait until all runs are done to start logging.



5\. **Stay within the compute budget.** If the budget from the TECHSPEC is exhausted before all planned runs complete, stop. Do not request exceptions. Record what completed.



6\. Present a summary of completed runs with links to the tracking tool before writing the log. Ask: "Do any of these runs need to be restarted or do you want to add runs before closing this experiment?" Halt and wait.



7\. Append results to `docs/experiments/06_Experiment_Log.md`.



8\. **Run `/bmad-dl-retrospective`** at the end of the session.



\## 2. Expected Output Template

When appending to `docs/experiments/06_Experiment_Log.md`:

\`\`\`markdown

\### Experiment: EXP-[ID]

\* \*\*Run Type:\*\* [Baseline / Tuned / Ablation]
\* \*\*TECHSPEC:\*\* `docs/techspecs/TECHSPEC_EXP_[ID].md`
\* \*\*Tracking Tool:\*\* [W&B / MLflow / ClearML]
\* \*\*Experiment/Project URL:\*\* [link to W&B project / MLflow experiment / ClearML project]

\### Run Summary

| Run Name | Key Params | val/loss | val/f1 | Best Epoch | Run URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| EXP-001_run_a | lr=1e-4, bs=512 | 0.23 | 0.87 | 42 | [link] |
| EXP-001_run_b | lr=3e-4, bs=512 | 0.19 | 0.91 | 38 | [link] |

\* \*\*Best Run:\*\* [run name + URL]
\* \*\*Budget Used:\*\* [X / Y GPU-hours]

\### Failed Attempts ❌ — MANDATORY

| Run / Config | Symptom | Root Cause | Lesson |
| :--- | :--- | :--- | :--- |
| lr=1e-3, bs=2048 | Loss diverged at epoch 3 | LR too high for batch size | Scale LR with batch size |

\* \*\*Status:\*\* [Complete — ready for bmad-dl-analysis]

\`\`\`
