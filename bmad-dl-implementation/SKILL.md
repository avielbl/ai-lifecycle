\---

name: bmad-dl-implementation

description: Acts as an AI Developer to execute a specific task, write code, tests, and update the integration log.

\---



\# BMAD Workflow 04: Implementation \& Integration



\## 1. Operating Instructions

You are an expert AI Developer. Your goal is to execute a specific task assigned in the detailed design.



1\. \*\*Resolve the next task:\*\* Run the task resolver to find the next unblocked task (or validate a specific one):

\`\`\`bash

python3 scripts/get\_next\_task.py docs/design/03\_Detailed\_Design.md docs/implementation/04\_Integration\_Log.md

\# Or for a specific task:

python3 scripts/get\_next\_task.py docs/design/03\_Detailed\_Design.md docs/implementation/04\_Integration\_Log.md --task-id TSK-001

\`\`\`

2\. For \*\*TSK-001 (EDA)\*\*, run the EDA analyzer on the project data directory and attach the report:

\`\`\`bash

python3 scripts/eda\_analyzer.py data/ --splits train val test --output docs/experiments/TSK001\_eda\_report.md

\`\`\`

Use `assets/template\_lightning\_module.py`, `assets/template\_datamodule.py`, and `assets/quick\_trainer\_setup.py` as starting points for TSK-002 and beyond.

3\. Locate and read `docs/design/03\_Detailed\_Design.md` to understand the task scope and linked requirements.

4\. Write the necessary source code and test files.

5\. \*\*CRITICAL:\*\* Do not merge or finalize yet. Present the proposed code and tests in the chat. Ask clarification questions regarding edge cases or implementation details. Halt execution and wait.

6\. Upon user approval, save the code files and append an entry to `docs/implementation/04\_Integration\_Log.md`.



\## 2. Expected Output Template

When appending to `04\_Integration\_Log.md`, adhere strictly to this format:



\### Task Execution: \[Task ID]

\* \*\*Target Requirement:\*\* \[Linked REQ-ID]

\* \*\*Implementation Summary:\*\* \[Brief description of the logic implemented]

\* \*\*Files Modified/Created:\*\*

&#x20;   \* `src/...`

&#x20;   \* `tests/...`

\* \*\*Validation:\*\* \[e.g., Pytest results]



\### Clarification \& Decision Log

\* \*\*Q1:\*\* \[Your question] -> \*\*User Decision:\*\* \[User's answer]

\* \*\*Status:\*\* \[Merged to `main`]

