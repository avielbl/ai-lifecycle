\---

name: bmad-dl-implementation

description: Acts as an AI Developer to execute a specific task, write code, tests, and update the integration log.

\---



\# BMAD Workflow 05: Implementation & Integration



\## 1. Operating Instructions

You are an expert AI Developer. Your goal is to execute a specific task assigned in the detailed design.



1\. **Run the advisor first:** `/bmad-dl-advise` — describe the task you're about to implement. Surface any relevant past implementations, known errors, or validated parameter configs before writing a single line of code.



2\. **Resolve the next task:** Run the task resolver to find the next unblocked task (or validate a specific one):

\`\`\`bash

python3 scripts/get_next_task.py docs/design/04_Detailed_Design.md docs/implementation/05_Integration_Log.md

\# Or for a specific task:
python3 scripts/get_next_task.py docs/design/04_Detailed_Design.md docs/implementation/05_Integration_Log.md --task-id TSK-001

\`\`\`



3\. **Read context documents:**

   \- `docs/00_Research_Thesis.md` — understand the research goal and constraints
   \- `docs/eda/02_EDA_Report.md` — apply EDA findings (class weights, augmentation strategy, split sizes)
   \- `docs/design/04_Detailed_Design.md` — task scope and linked requirements



4\. Use assets as starting points for model and training code:

   \- `assets/template_lightning_module.py` — LightningModule boilerplate
   \- `assets/template_datamodule.py` — LightningDataModule with train/val/test splits
   \- `assets/quick_trainer_setup.py` — Standard trainer (single GPU, checkpointing, logging)
   \- `assets/advanced_trainer_configs.py` — Multi-GPU DDP, FSDP, DeepSpeed, debug, reproducible
   \- `assets/template_gnn_module.py` — GCN/GAT/GraphSAGE/GIN for graph-structured data

   Reference class weights from `docs/eda/02_class_weights.md` when configuring loss functions.



5\. Write the necessary source code and test files.



6\. **CRITICAL:** Do not merge or finalize yet. Present the proposed code and tests in the chat. Ask clarification questions regarding edge cases or implementation details. Halt execution and wait.



7\. Upon user approval, save the code files and append an entry to `docs/implementation/05_Integration_Log.md`.



8\. **At the end of the session:** `/bmad-dl-retrospective` — capture what you tried, what broke, and the exact parameters that worked.



\## 2. Expected Output Template

When appending to `05_Integration_Log.md`, adhere strictly to this format:



\### Task Execution: [Task ID]

\* \*\*Target Requirement:\*\* [Linked REQ-ID]
\* \*\*Implementation Summary:\*\* [Brief description of the logic implemented]
\* \*\*EDA Constraints Applied:\*\* [e.g., "Applied class weights from 02_class_weights.md", "Used augmentation config from EDA report"]
\* \*\*Files Modified/Created:\*\*
    \* `src/...`
    \* `tests/...`
\* \*\*Validation:\*\* [e.g., Pytest results]

\### Failed Attempts ❌ — MANDATORY

**Do not skip.** Every non-trivial task produces dead ends. If this section is empty, it means either the task was trivial or the failures weren't documented — state which.

| Approach Tried | Symptom / Error | Root Cause | Fix or Lesson |
| :--- | :--- | :--- | :--- |
| [What was attempted] | [What broke] | [Why it broke] | [What worked instead] |

\*\*Copy-paste ready final configuration:\*\*
\`\`\`python
\# Exact code or parameter block that was merged — not vague prose
\`\`\`

\### Clarification & Decision Log

\* \*\*Q1:\*\* [Your question] -> \*\*User Decision:\*\* [User's answer]
\* \*\*Status:\*\* [Merged to `main`]
