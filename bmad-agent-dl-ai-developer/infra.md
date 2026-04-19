# Capability: Infrastructure Build

## Overview
Builds the data pipelines, training loops, and evaluation harnesses (INF-* tasks).

## Operating Instructions
1. **Input:** Read `docs/design/04_Detailed_Design.md`.
2. **Build:** Implement the data loaders, model code, loss functions, and logging.
3. **Provision:** Run `uv sync` to install dependencies.
4. **Validation:** Run a smoke test with dummy data.
5. **Output:** Update `docs/implementation/05_Infra_Log.md` with results.
