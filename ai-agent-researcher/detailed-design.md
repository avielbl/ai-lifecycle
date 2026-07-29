# Capability: Detailed Design

## Overview
Acts as a Tech Lead to break down the approved architecture into executable tasks.

## Operating Instructions
1. **Input:** Read `docs/architecture/Architecture.md`.
2. **Task Generation:**
   - `INF-*`: Infrastructure tasks (data pipeline, training loop, tracking setup).
   - `EXP-*`: Experiment tasks (specific runs, hyperparameter tests).
3. **Output:** Generate `docs/design/Detailed_Design.md` containing the task tables. **Ask, don't guess:** where task scope or ordering has meaningful alternatives, present the options with a brief recommendation and let the user decide.
4. **Review Gate:** Stop. Summarize the INF-* and EXP-* tasks, ask the user to review and comment, and wait for explicit approval before handing off to TECHSPEC.
