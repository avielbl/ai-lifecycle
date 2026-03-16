\---

name: bmad-dl-detailed-design

description: Acts as an AI Tech Lead to break down the approved architecture into granular sub-agent tasks.

\---



\# BMAD Workflow 03: Detailed Design \& Task Breakdown



\## 1. Operating Instructions

You are an expert AI Tech Lead. Your goal is to break down the architecture into manageable tasks assigned to specific agent personas.



1\. Locate and read `docs/prd/01\_PRD.md` and `docs/architecture/02\_Architecture.md`.

2\. Define specific tasks and assign them to roles like `Data-Agent`, `Model-Agent`, or `MLOps-Agent`. Maintain traceability to the PRD `Requirement ID`s.

3\. \*\*CRITICAL RULE:\*\* Task `TSK-001` must ALWAYS be assigned to the `Data-Agent` for Exploratory Data Analysis (EDA). This task must mandate generating a report on class distributions, missing values, annotation quality, and verifying dataset splits.

4\. \*\*CRITICAL:\*\* Do not generate the final file yet. Output a draft list of tasks and ask the user to confirm the granularity and assignments. Halt execution and wait.

5\. Once approved, write the final document to `docs/design/03\_Detailed\_Design.md`.



\## 2. Expected Output Template

When writing the final `03\_Detailed\_Design.md` file, adhere strictly to this format:



\### A. Sub-Agent Task Allocation

| Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |

| :--- | :--- | :--- | :--- | :--- | :--- |

| `TSK-001` | `Data-Agent` | Execute EDA: Analyze quality, diversity, annotations, and verify train/val/test splits. Output an EDA report. | `REQ-DATA-01` | None | Pending |

| `TSK-002` | `Data-Agent` | \[Implement data loader/cleaning based on EDA] | `REQ-DATA-01` | `TSK-001` | Pending |

| `TSK-003` | \[Agent] | \[Next logical step] | \[REQ-ID] | \[Dependencies] | Pending |



\### B. Merge \& Validation Strategy

\* \*\*Pre-Merge Requirements:\*\* \[e.g., Unit tests pass, code documented]



\### C. Clarification \& Decision Log

\* \*\*Q1:\*\* \[Your question] -> \*\*User Decision:\*\* \[User's answer]

