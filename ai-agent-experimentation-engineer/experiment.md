# Capability: Experiment Execution

## Overview
Executes training runs and logs execution details.

## Operating Instructions
1. **Input:** Read `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`.
2. **Setup:** Ensure data pipelines and tracking tools are initialized.
3. **Run:** Execute training scripts per TECHSPEC execution plan. **Ask, don't guess:** if the TECHSPEC is ambiguous or a run must deviate from it, stop and ask the user — never improvise parameters.
4. **Log:** Create `{ai_output_folder}/experiments/{ID}/RUN_{timestamp}.md` with:
   - Per-arm tables: script command, tracker task ID, model summary, total params (pretrained vs random), best metric, convergence status, wall-clock time
   - Execution timeline with hour-level UTC timestamps
   - Notes on any issues encountered during execution
5. **Archive configs:** Copy all config files used into `{ai_output_folder}/experiments/{ID}/configs/`.
6. **Review Gate:** Stop after writing the RUN log. Summarize run outcomes and issues, ask the user to review and comment, and wait for explicit approval before handing off to Results.

## Timestamp Format
Use `YYYY-MM-DD_HH-MM-SS` in filenames (e.g., `RUN_2026-05-20_08-00-00.md`).
Within the doc body, use `YYYY-MM-DD ~HH:MM UTC` for event timestamps.
