# Capability: Infrastructure Build

## Overview
Builds the data pipelines, training loops, and evaluation harnesses (INF-* tasks).

## Operating Instructions
1. **Input:** Read `{ai_output_folder}/design/Detailed_Design.md`. **Memory retrieval:** scan the memory index for `lesson` entries whose tags match the stack, tooling, or environment, and read the matching entry files — known infra bugs and workarounds save debugging time.
2. **Build:** Implement the data loaders, model code, loss functions, and logging.
3. **Provision:** Run `uv sync` to install dependencies. This is the **first and only** package installation in the lifecycle — no capability before or besides this one installs anything. For remote/cloud training images, reuse the scaffold's `docker/Dockerfile.train` instead of writing a new one — this first `uv sync` also validates that Dockerfile's dependency layer.
4. **Validation:** Run a smoke test with dummy data.
5. **Output:** Update `{ai_output_folder}/implementation/Infra_Log.md` with results.
6. **Review Gate:** Stop. Summarize what was built and the smoke-test results, ask the user to review and comment, and wait for explicit approval before handing off to Experiment Execution.
7. **Memory Update (mandatory, after approval):** Distill new atomic facts from the Infra Log into `{ai_output_folder}/memory/entries/` using the entry template — `lesson` entries (infra bugs, fixes, and generalizable rules) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.
