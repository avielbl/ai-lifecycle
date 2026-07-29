# Capability: Infrastructure Build

## Overview
Builds the data pipelines, training loops, and evaluation harnesses (INF-* tasks).

## Operating Instructions
1. **Input:** Read `{ai_output_folder}/design/Detailed_Design.md`. **Memory retrieval:** scan the memory index for `lesson` entries whose tags match the stack, tooling, or environment, and read the matching entry files — known infra bugs and workarounds save debugging time.
2. **Build:** Implement the data loaders, model code, loss functions, and logging.
3. **Provision:** Run `uv sync` to install dependencies. This is the **first and only** package installation in the lifecycle — no capability before or besides this one installs anything. For remote/cloud training images, reuse the scaffold's `docker/Dockerfile.train` instead of writing a new one — this first `uv sync` also validates that Dockerfile's dependency layer.
4. **Tracker Verification:** Read `ai_experiment_tracker`, `ai_tracker_url`, and `ai_tracker_offline` from the resolved config. If the tracker is `none`, log "tracking: local files only" in the Infra Log and skip to Validation. If `ai_tracker_offline` is `true`, skip the ping and go straight to the offline fallback below.
   - **Connectivity ping** (one-liner per tool, via `uv run python -c ...`, using `ai_tracker_url` when set):
     - **W&B:** `wandb.login(timeout=10)` then `wandb.Api().viewer` — verifies `WANDB_API_KEY` and host (`WANDB_BASE_URL` for self-hosted).
     - **MLflow:** `mlflow.MlflowClient(tracking_uri=...).search_experiments(max_results=1)` — verifies URI and auth.
     - **ClearML:** `Task.get_projects()` after `clearml.conf`/env check — verifies the api/web/files server triplet.
   - **On success:** record tracker, resolved URL, and project/workspace name in the Infra Log; create the project/experiment container if missing.
   - **On failure (or forced offline):** **warn the user, switch to offline mode, record it prominently in the Infra Log, and continue — never hard-fail Stage 5 on a dead tracker** (offline artifacts are always recoverable):
     - W&B → `WANDB_MODE=offline` (sync later with `wandb sync`)
     - MLflow → `tracking_uri: file:./mlruns` (local store; point at the server later)
     - ClearML → `Task.set_offline(True)` (import later with `Task.import_offline_session`)
   - **Credentials** live in env vars (`WANDB_API_KEY`, `MLFLOW_TRACKING_TOKEN`, `CLEARML_API_*`) — never in config files, matching the `llm_config.yaml` rule.
5. **Validation:** Run a smoke test with dummy data.
6. **Output:** Update `{ai_output_folder}/implementation/Infra_Log.md` with results, including the tracker verification outcome (online with resolved URL, or offline mode and why).
7. **Review Gate:** Stop. Summarize what was built and the smoke-test results, ask the user to review and comment, and wait for explicit approval before handing off to Experiment Execution.
8. **Memory Update (mandatory, after approval):** Distill new atomic facts from the Infra Log into `{ai_output_folder}/memory/entries/` using the entry template — `lesson` entries (infra bugs, fixes, and generalizable rules) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.
