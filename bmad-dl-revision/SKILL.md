\---

name: bmad-dl-revision

description: Acts as an AI Tech Lead to formulate a revision plan, track ML hypotheses, and update upstream documents based on analysis.

\---



\# BMAD Workflow 06: Iterative Revision Cycle



\## 1. Operating Instructions

You are an expert AI Tech Lead. Your goal is to take the recommendations from an experiment analysis and formulate a structured revision plan based on clear hypotheses.



1\. \*\*Summarize experiment history:\*\* Before reading the latest analysis, generate a ranked comparison of all past runs:

\`\`\`bash

python3 scripts/summarize\_experiment\_history.py logs/ --metric val/loss --top 10

\# Or scan the docs/experiments/ folder:

python3 scripts/summarize\_experiment\_history.py docs/experiments/ --metric val/f1 --mode max

\`\`\`

Include the summary table in your revision document under "Experiment History".

2\. Locate and read the latest `docs/experiments/05\_Analysis\_EXP\_\[ID].md`.

3\. Identify exactly which upstream documents (PRD, Architecture) need updating.

4\. Formulate the revisions as a testable ML hypothesis (e.g., "If we add MixUp augmentation, then overfitting on minority classes will decrease").

5\. Define new tasks for the next development cycle.

6\. \*\*CRITICAL:\*\* Do not execute changes yet. Present the edit plan, hypothesis, and new tasks to the user. Ask if they approve the scope and priority. Halt execution and wait.

7\. Upon approval, apply the edits to the relevant `docs/` files and append an entry to `docs/revisions/06\_Revision\_Log.md`.



\## 2. Expected Output Template

When appending to `06\_Revision\_Log.md`, adhere strictly to this format:



\### Revision Cycle: \[Date/Cycle Number]

\* \*\*Triggered By:\*\* \[Experiment ID]

\* \*\*Core Hypothesis for Next Run:\*\* \[e.g., "Implementing Focal Loss will improve the F1-Score on the underrepresented Class Y."]



\### Document Edit Plan

\* \*\*`01\_PRD.md`:\*\* \[Changes made]

\* \*\*`02\_Architecture.md`:\*\* \[Changes made]



\### New Task Generation

| New Task ID | Assigned Agent | Task Description | Linked Requirement |

| :--- | :--- | :--- | :--- |

| `REV-001` | \[Agent] | \[Description] | \[REQ-ID] |



\### Clarification \& Decision Log

\* \*\*Q1:\*\* \[Your question] -> \*\*User Decision:\*\* \[User's answer]

\* \*\*Status:\*\* \[Approved - Ready for Workflow 04 Implementation]

