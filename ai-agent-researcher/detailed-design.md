# Capability: Detailed Design

## Overview
Acts as a Tech Lead to break down the approved architecture into executable tasks.

## Operating Instructions
1. **Input:** Read `docs/architecture/Architecture.md`. **Memory retrieval:** scan the memory index for `decision` and `lesson` entries whose tags match the stack or tasks at hand, and read the matching entry files — known workarounds and rejected alternatives shape the task breakdown. (This capability reads the bank only; it writes no entries.)
2. **Task Generation:**
   - `INF-*`: Infrastructure tasks (data pipeline, training loop, tracking setup).
   - `EXP-*`: Experiment tasks (specific runs, hyperparameter tests).
3. **Output:** Generate `docs/design/Detailed_Design.md` containing the task tables. **Ask, don't guess:** where task scope or ordering has meaningful alternatives, present the options with a brief recommendation and let the user decide.
4. **Review Gate:** Stop. Summarize the INF-* and EXP-* tasks, ask the user to review and comment, and wait for explicit approval before handing off to TECHSPEC.
