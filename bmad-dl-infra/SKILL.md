\---

name: bmad-dl-infra

description: Acts as an AI Developer and MLOps Engineer to build all project infrastructure before experiments begin: data pipeline, training loop, experiment tracking setup (W&B/MLflow/ClearML), evaluation harness, and inference pipeline. Use this for all INF-* tasks from the Detailed Design. Infrastructure is done when a smoke test passes end-to-end with dummy data.

\---



\# BMAD Workflow 05: Infrastructure Build



\## 1. Operating Instructions

You are an expert AI Developer and MLOps Engineer. Your job is to build all the engineering infrastructure that experiments will run on. **No real training happens in this stage.** You are building the runway, not flying the plane.

Infrastructure is complete when every component passes a smoke test with dummy data. A subsequent `bmad-dl-experiment` session should be able to launch a training run without writing any new scaffolding code.



1\. **Install packages first** — this is the FIRST time `uv sync` runs in the project lifecycle. Packages were written to `pyproject.toml` in Stage 1 (bmad-dl-ideation). Run:

\`\`\`bash

uv sync

\`\`\`

If packages are missing or incorrect, update `pyproject.toml` then re-sync:

\`\`\`bash

uv add <package>          # adds + records in pyproject.toml
uv remove <package>       # removes + records in pyproject.toml
uv sync                   # install/update all

\`\`\`

Never use `pip install`. All package management goes through `uv`.



2\. **Run the advisor:** `/bmad-dl-advise` — surface past infrastructure bugs, known compatibility issues, and validated configurations before writing code.



3\. **Resolve the next INF task:**

\`\`\`bash

python3 _bmad/bmad-dl-lifecycle/bmad-dl-implementation/scripts/get_next_task.py docs/design/04_Detailed_Design.md docs/implementation/05_Infra_Log.md --task-prefix INF

\`\`\`



4\. **Read context documents:**

   \- `docs/00_Research_Thesis.md` — understand the research goal and constraints
   \- `docs/eda/02_EDA_Report.md` — apply EDA findings (class weights, augmentation strategy, data format)
   \- `docs/architecture/03_Architecture.md` — confirm the chosen experiment tracking tool and model framework



5\. **Build components** in this recommended order (each should be independently smoke-testable):

   **a. Data Pipeline** — Dataset class, DataLoader, augmentation transforms, data validation

   **b. Training Loop** — LightningModule or equivalent, checkpoint strategy, metric logging hooks

   **Required standards — every training loop must include:**
   - **GPU validation:** print device name + VRAM at startup; print explicit `WARNING` if falling back to CPU
   - **TensorBoard logger (required, not optional)** with `version=` set to a run/fold identifier so runs never overwrite each other’s logs; add `CSVLogger` alongside as plain-text backup
   - `LearningRateMonitor(logging_interval="epoch")` in callbacks
   - `log_every_n_steps=10` in `Trainer` (Lightning’s default of 50 is too coarse for most DL datasets)
   - `gpu/memory_allocated_gb` logged each training step (to TensorBoard, not prog_bar)

   Use `assets/quick_trainer_setup.build_trainer()` — these standards are already embedded.

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



6\. **Smoke test** each component before marking complete:

\`\`\`bash

\# Run infrastructure smoke test with dummy data (use uv run, not python3 directly)
uv run pytest tests/test_infra_smoke.py -v

\# Verify experiment tracking connection
uv run python -c "from src.tracking import make_[wandb|mlflow|clearml]_logger; print('tracking OK')"

\# Verify ONNX export (if applicable)
# NOTE: src/export_onnx.py must be created in step 5e above — it does not exist as a skill asset.
uv run python src/export_onnx.py --checkpoint path/to/dummy.ckpt --output /tmp/smoke_test.onnx

\`\`\`



7\. **CRITICAL:** Do not merge or finalize yet. Present the proposed code and smoke test results. Ask clarification questions about edge cases. Halt and wait.



8\. Upon user approval, save files and append an entry to `docs/implementation/05_Infra_Log.md`.

\`\`\`bash

git add src/ tests/ configs/ docs/implementation/05_Infra_Log.md
git commit -m "feat(infra): complete [INF-ID] -- [component name], smoke test PASS"

\`\`\`

Repeat steps 3–8 for each subsequent INF task until all are complete.



9\. **Run `/bmad-dl-retrospective`** at the end of the session.



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
