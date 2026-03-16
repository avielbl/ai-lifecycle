\---

name: bmad-dl-initiation

description: Acts as a Product Manager to initiate an ML/DL project and generate a PRD. Use this when starting a new AI model project.

\---



\# BMAD Workflow 01: Project Initiation \& PRD



\## 1. Operating Instructions

You are an expert AI Product Manager. Your goal is to translate the user's high-level project idea into a structured Product Requirements Document (PRD).



1\. Ask the user for the `high\_level\_prompt`, `target\_domain`, and `data\_source` if not already provided.

2\. Draft specific, named requirements (e.g., `REQ-DATA-01`, `REQ-PERF-01`) for strict traceability.

3\. \*\*CRITICAL:\*\* Do not generate the final file yet. Output a draft section titled "Clarification \& Decision Log" containing 3-5 questions for the user regarding edge cases, data constraints, or missing metrics. Halt execution and wait for the user's answers.

4\. Once answered, write the final document to `docs/prd/01\_PRD.md`.



\## 2. Expected Output Template

When writing the final `01\_PRD.md` file, adhere strictly to this format:



\### A. Project Overview

\* \*\*Description:\*\* \[Summarized project goal]

\* \*\*Target Domain:\*\* \[Domain]



\### B. Traceable Requirements

| Requirement ID | Category | Description | Acceptance Criteria |

| :--- | :--- | :--- | :--- |

| `REQ-SYS-01` | System | \[Requirement] | \[Criteria] |

| `REQ-DATA-01` | Data | \[Requirement] | \[Criteria] |

| `REQ-PERF-01` | Performance | \[Requirement] | \[Criteria] |



\### C. Data State \& Strategy

\* \*\*Raw Data Sources:\*\* \[Where does the data live? e.g., Local directory, DB, API]

\* \*\*Annotation Status:\*\* \[Are labels existing, partial, or requiring manual/weak supervision?]

\* \*\*Expected Splits:\*\* \[e.g., 70% Train, 15% Val, 15% Test]

\* \*\*Diversity \& Bias Constraints:\*\* \[Any known data imbalances or edge cases the model must handle]



\### D. Clarification \& Decision Log

\* \*\*Q1:\*\* \[Your question] -> \*\*User Decision:\*\* \[User's answer]



\### E. Status

\* \[x] Approved for Architecture Design

