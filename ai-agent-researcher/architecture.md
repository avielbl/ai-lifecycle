# Capability: Architecture Design

## Overview
Designs the model architecture and experiment tracking setup based on the Research Thesis and EDA findings.

## Operating Instructions
1. **Inputs:** Read `docs/Research_Thesis.md` and `docs/eda/EDA_Report.md`. **Memory retrieval:** scan the memory index for `finding`, `result`, and `decision` entries whose tags match the problem or candidate paradigms, and read the matching entry files — rejected paradigms and validated results constrain the design.
2. **Design Strategy:** Determine the framework stack, model topology, loss functions, and optimizers. **Ask, don't guess:** present candidate paradigms/stacks with trade-offs and a brief recommendation, and let the user decide before writing the document.
3. **Tracking:** Choose and configure `wandb`, `mlflow`, or `clearml` (configuration only — do not install anything; the tracker SDK is installed in Stage 5, `infra`, via `uv sync`).
4. **Output:** Generate `docs/architecture/Architecture.md`.
5. **Review Gate:** Stop. Summarize the architecture decisions, ask the user to review and comment, and wait for explicit approval before handing off to Detailed Design.
6. **Memory Update (mandatory, after approval):** Distill new atomic facts from the Architecture document into `{ai_output_folder}/memory/entries/` using the entry template — `decision` entries (the paradigm choice **and each rejected paradigm, with reasons**) and `finding` entries (prior-art facts that drove the choice) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.
