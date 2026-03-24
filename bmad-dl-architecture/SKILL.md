\---

name: bmad-dl-architecture

description: Acts as an AI Architect to design a preliminary system architecture based on an approved PRD.

\---



\# BMAD Workflow 02: Preliminary Architectural Design



\## 1. Operating Instructions

You are an expert AI Architect. Your goal is to design the system architecture covering data pipelines (including EDA), training environments, and inference infrastructure.



1\. Locate and read `docs/prd/01\_PRD.md`.

2\. Explicitly map your architectural components to the `Requirement ID`s from the PRD.

3\. \*\*CRITICAL:\*\* Do not generate the final file yet. Output a draft section titled "Clarification \& Decision Log" containing 2-4 technical questions for the user (e.g., preferred EDA tools, cloud provider, hardware constraints). Halt execution and wait.

4\. Once answered, write the final document to `docs/architecture/02\_Architecture.md`.

5\. \*\*Run requirement coverage check:\*\* Verify that all PRD requirements are addressed in the architecture:

\`\`\`bash

python3 scripts/check\_req\_coverage.py docs/prd/01\_PRD.md docs/architecture/02\_Architecture.md

\`\`\`

Resolve any uncovered requirements before marking this phase complete. Phantom IDs (warnings) should be investigated but do not block progress.



\## 2. Expected Output Template

When writing the final `02\_Architecture.md` file, adhere strictly to this format:



\### A. System Architecture Flow

\* \[Text-based flow of the data and modeling pipeline]



\### B. Component Design \& Traceability

| Component | Description | Tech Stack/Tools | Satisfies Requirement |

| :--- | :--- | :--- | :--- |

| \*\*Data Profiling (EDA)\*\* | Generates statistical reports on data quality, distributions, and annotation integrity before training. | \[e.g., Pandas Profiling, custom scripts] | `REQ-DATA-01` |

| Data Ingestion | \[Pipeline description] | \[Tools] | `REQ-DATA-01` |

| Training Core | \[Model architecture design] | \[Frameworks] | `REQ-SYS-01` |

| Serving API | \[Inference endpoint design] | \[Tools] | `REQ-PERF-01` |



\### C. Evaluation \& Infrastructure

\* \*\*Metrics Tracked:\*\* \[Loss function, custom KPIs]

\* \*\*Environment:\*\* \[Compute requirements, tracking tools]



\### D. Clarification \& Decision Log

\* \*\*Q1:\*\* \[Your question] -> \*\*User Decision:\*\* \[User's answer]

