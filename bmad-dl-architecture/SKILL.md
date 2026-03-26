\---

name: bmad-dl-architecture

description: Acts as an AI Architect to design a system architecture grounded in the Research Thesis and EDA findings.

\---



\# BMAD Workflow 03: Preliminary Architectural Design



\## 1. Operating Instructions

You are an expert AI Architect. Your goal is to design the system architecture covering data pipelines, training environments, and inference infrastructure. Your decisions must be **grounded in EDA findings** — you are not designing for a hypothetical dataset, but for the specific data characteristics already established in Stage 02.



1\. **Read the Research Thesis first:** Locate and read `docs/00_Research_Thesis.md`. Pay close attention to:

   \- Section II (Core Research Hypothesis) — what are we trying to prove?
   \- Section III (Domain Context) — what constraints are non-negotiable?
   \- Section IV (Data Characterization) — what did EDA reveal?



2\. Locate and read `docs/prd/01_PRD.md` and `docs/eda/02_EDA_Report.md`.

   \- For each architectural decision, explicitly cite which EDA finding or PRD requirement drives it.
   \- Consult Section F of the EDA report ("Architectural Constraints & Recommendations") — these are mandatory constraints.



3\. Explicitly map every architectural component to the `Requirement ID`s from the PRD.



4\. **CRITICAL:** Do not generate the final file yet. Output a draft "Clarification & Decision Log" with 2–4 technical questions. These must address open questions surfaced by the EDA, not just generic architecture choices. Halt execution and wait.



5\. Once answered, write the final document to `docs/architecture/03_Architecture.md`.



6\. **Run requirement coverage check:**

\`\`\`bash

python3 _bmad/bmad-dl-lifecycle/bmad-dl-architecture/scripts/check_req_coverage.py docs/prd/01_PRD.md docs/architecture/03_Architecture.md

\`\`\`

Resolve any uncovered requirements before marking this phase complete.



\## 2. Expected Output Template

When writing the final `03_Architecture.md` file, adhere strictly to this format:



\### A. System Architecture Flow

\* [Text-based flow of the data and modeling pipeline, from raw data to inference]



\### B. Component Design & Traceability

| Component | Description | Tech Stack/Tools | Satisfies Requirement | EDA Justification |
| :--- | :--- | :--- | :--- | :--- |
| Data Ingestion | [Pipeline description] | [Tools] | \`REQ-DATA-01\` | [EDA finding that drives this choice] |
| Training Core | [Model architecture design] | [Frameworks] | \`REQ-SYS-01\` | [e.g., "Baseline F1=0.42 → deep features required"] |
| Class Imbalance Handling | [Strategy] | [e.g., weighted loss, oversampling] | \`REQ-PERF-01\` | [e.g., "Severe imbalance (10:1) confirmed in EDA"] |
| Serving API | [Inference endpoint design] | [Tools] | \`REQ-PERF-02\` | — |



\### C. Evaluation & Infrastructure

\* \*\*Metrics Tracked:\*\* [Loss function, custom KPIs]
\* \*\*Environment:\*\* [Compute requirements, tracking tools]
\* \*\*Hypothesis Validation Plan:\*\* [How will we know if the Core Research Hypothesis is proven or falsified?]



\### D. Clarification & Decision Log

\* \*\*Q1:\*\* [Your question] -> \*\*User Decision:\*\* [User's answer]
