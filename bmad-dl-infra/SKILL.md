\---

name: bmad-dl-infra

description: Acts as an AI Developer and MLOps Engineer to build all project infrastructure before experiments begin: data pipeline, training loop, experiment tracking setup (W&B/MLflow/ClearML), evaluation harness, and inference pipeline. Use this for all INF-* tasks from the Detailed Design. Infrastructure is done when a smoke test passes end-to-end with dummy data.

\---



\# BMAD Workflow 05: Infrastructure Build



\## 1. Operating Instructions

You are an expert AI Developer and MLOps Engineer. Your job is to build all the engineering infrastructure that experiments will run on. **No real training happens in this stage.** You are building the runway, not flying the plane.

Infrastructure is complete when every component passes a smoke test with dummy data. A subsequent `bmad-dl-experiment` session should be able to launch a training run without writing any new scaffolding code.



1\. **Run the advisor first:** `/bmad-dl-advise` — surface past infrastructure bugs, known compatibility issues, and validated configurations before writing code.



2\. **Resolve the next INF task:**

\`\`\`bash

python3 scripts/get_next_task.py docs/design/04_Detailed_Design.md docs/implementation/05_Infra_Log.md --task-prefix INF

\`\`\`



3\. **Read context documents:**

   \- `docs/00_Research_Thesis.md` — understand the research goal and constraints
   \- `docs/eda/02_EDA_Report.md` — apply EDA findings (class weights, augmentation strategy, data format)
   \- `docs/architecture/03_Architecture.md` — confirm the chosen experiment tracking tool and model framework



4\. **Build components** in this recommended order (each should be independently smoke-testable):

   **a. Data Pipeline** — Dataset class, DataLoader, augmentation transforms, data validation

   **b. Training Loop** — LightningModule or equivalent, checkpoint strategy, metric logging hooks

   Use assets as starting points:
   \- `assets/template_lightning_module.py` — LightningModule with train/val/test steps
   \- `assets/template_datamodule.py` — LightningDataModule with auto split detection
   \- `assets/quick_trainer_setup.py` — Trainer with checkpointing, early stopping, LR monitor
   \- `assets/advanced_trainer_configs.py` — DDP, FSDP, DeepSpeed, reproducible configs
   \- `assets/template_gnn_module.py` — GCN/GAT/GraphSAGE/GIN for graph data

   **c. Experiment Tracking Setup** — wire the chosen tool into the training loop:

\`\`\`python

\# ── W&B ──────────────────────────────────────────────────────────────────────
import wandb
from lightning.loggers import WandbLogger

def make_wandb_logger(exp_id: str, run_name: str, config: dict) -> WandbLogger:
    return WandbLogger(
        project=PROJECT_NAME,
        name=f"{exp_id}_{run_name}",
        tags=[exp_id, "baseline"],
        config=config,
        save_dir="logs/",
    )

\# ── MLflow ───────────────────────────────────────────────────────────────────
import mlflow
from lightning.loggers import MLFlowLogger

mlflow.set_tracking_uri("./mlruns")   \# or http://mlflow-server:5000
mlflow.set_experiment(PROJECT_NAME)

def make_mlflow_logger(exp_id: str, run_name: str) -> MLFlowLogger:
    return MLFlowLogger(
        experiment_name=PROJECT_NAME,
        run_name=f"{exp_id}_{run_name}",
        tracking_uri="./mlruns",
        tags={"exp_id": exp_id},
    )

\# ── ClearML ──────────────────────────────────────────────────────────────────
from clearml import Task
from lightning.loggers import TensorBoardLogger  \# ClearML captures TensorBoard automatically

def init_clearml_task(exp_id: str, run_name: str, hyperparams: dict) -> Task:
    task = Task.init(
        project_name=PROJECT_NAME,
        task_name=f"{exp_id}_{run_name}",
        task_type=Task.TaskTypes.training,
        tags=[exp_id, "baseline"],
    )
    task.connect(hyperparams)   \# auto-logs all params and captures git diff
    return task

\`\`\`

   **d. Evaluation Harness** — test runner, confusion matrix generator, per-class metric computation

   **e. Inference Pipeline** — batch inference script, ONNX export, latency profiler

   **f. REST API scaffold** (if required by architecture) — FastAPI endpoint, health check, request/response schema

\`\`\`python

\# Minimal FastAPI inference endpoint scaffold
from fastapi import FastAPI
from pydantic import BaseModel
import torch

app = FastAPI()

class PredictRequest(BaseModel):
    inputs: list[list[float]]

@app.post("/predict")
def predict(req: PredictRequest):
    with torch.no_grad():
        outputs = model(torch.tensor(req.inputs))
    return {"predictions": outputs.argmax(-1).tolist()}

@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}

\`\`\`



5\. **Smoke test** each component before marking complete:

\`\`\`bash

\# Run infrastructure smoke test with dummy data
python3 -m pytest tests/test_infra_smoke.py -v

\# Verify experiment tracking connection
python3 -c "from src.tracking import make_[wandb|mlflow|clearml]_logger; print('tracking OK')"

\# Verify ONNX export (if applicable)
python3 scripts/export_onnx.py --checkpoint path/to/dummy.ckpt --output /tmp/smoke_test.onnx

\`\`\`



6\. **CRITICAL:** Do not merge or finalize yet. Present the proposed code and smoke test results. Ask clarification questions about edge cases. Halt and wait.



7\. Upon user approval, save files and append an entry to `docs/implementation/05_Infra_Log.md`.



8\. **Run `/bmad-dl-retrospective`** at the end of the session.



\## 2. Expected Output Template

When appending to `05_Infra_Log.md`:

\`\`\`markdown

\### INF Task: [INF-ID]

\* \*\*Component:\*\* [e.g., Data Pipeline / Experiment Tracking / Inference API]
\* \*\*Summary:\*\* [What was built]
\* \*\*Tracking Tool Wired:\*\* [W&B / MLflow / ClearML — with project/experiment name]
\* \*\*Files Created/Modified:\*\*
    \* `src/...`
    \* `tests/...`
\* \*\*Smoke Test Result:\*\* [PASS — all components verified with dummy data]

\### Failed Attempts ❌ — MANDATORY

| Approach Tried | Symptom / Error | Root Cause | Fix |
| :--- | :--- | :--- | :--- |
| [What broke during build] | [Error or behavior] | [Root cause] | [Fix applied] |

\*\*Copy-paste ready configuration:\*\*
\`\`\`python
\# Exact tracking setup / config that passed smoke test
\`\`\`

\* \*\*Status:\*\* [Merged — ready for bmad-dl-experiment]

\`\`\`
