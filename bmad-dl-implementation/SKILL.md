\---

name: bmad-dl-implementation

description: DEPRECATED as of v2.0.0. Implementation has been split into bmad-dl-infra (infrastructure build, INF-* tasks) and bmad-dl-experiment (training runs, EXP-* tasks). Use those skills instead.

\---



\# DEPRECATED: bmad-dl-implementation



This skill has been split into two dedicated stages in v2.0.0:



\## Use `bmad-dl-infra` for infrastructure tasks (INF-*)

Build data pipelines, training loop, experiment tracking setup, evaluation harness, inference pipeline. Infrastructure is done when smoke test passes with dummy data.

\`\`\`

/bmad-dl-infra

\`\`\`



\## Use `bmad-dl-experiment` for training runs (EXP-*)

Execute training experiments against a locked TECHSPEC, log to W&B/MLflow/ClearML, produce the Experiment Log.

\`\`\`

/bmad-dl-experiment

\`\`\`



\## How to determine which to use

\- Is the task prefixed `INF-` in `docs/design/04_Detailed_Design.md`? → Use `bmad-dl-infra`
\- Is the task prefixed `EXP-` in `docs/design/04_Detailed_Design.md`? → Use `bmad-dl-experiment`



\## Assets (still available)

The following assets remain available for use in both stages:

\- `assets/template_lightning_module.py` — LightningModule boilerplate
\- `assets/template_datamodule.py` — LightningDataModule
\- `assets/quick_trainer_setup.py` — Standard Trainer config
\- `assets/advanced_trainer_configs.py` — DDP, FSDP, DeepSpeed, debug configs
\- `assets/template_gnn_module.py` — GNN architectures (GCN/GAT/GraphSAGE/GIN)
