# Capability: Revision Audit

## Overview
Audits and amends all upstream lifecycle documents at the end of an experiment cycle. Ensures the Research Thesis, PRD, Architecture, and Detailed Design remain consistent with what was actually learned — whether the experiment succeeded, partially succeeded, or failed.

## When to Use
After `ai-agent-researcher analysis` has concluded an experiment cycle. Every completed cycle — successful or not — warrants a Revision Audit before starting the next one.

## Phase 1: Gather Experiment Outcomes
Read:
1. `{output_folder}/experiments/07_Analysis_EXP_[ID].md` — the most recent analysis report
2. `{output_folder}/techspecs/TECHSPEC_EXP_[ID].md` — the contract that governed the cycle
3. `docs/00_Research_Thesis.md` — the current hypothesis

Confirm with the user: "Which experiment cycle are we auditing? Should I cover all upstream docs or specific ones?"

## Phase 2: Audit Each Upstream Document

**Research Thesis (`docs/00_Research_Thesis.md`)**
- Does the Active Hypothesis still hold? Should it be refined or replaced?
- Are Domain Failure Costs still accurate given experiment findings?
- Add the experiment outcome to the **Hypothesis History** section (mandatory).

**PRD (`docs/prd/01_PRD.md`)**
- Do any functional requirements need updating based on what was learned?
- Were any requirements revealed as infeasible at current scale or with available data?

**Architecture (`docs/architecture/03_Architecture.md`)**
- Were architectural/paradigm assumptions validated or invalidated?
- Should the model family (DL, gradient boosting, ensemble, etc.) be revisited?

**Detailed Design (`docs/design/04_Detailed_Design.md`)**
- Should any INF-* or EXP-* tasks be retired, amended, or added for the next cycle?

## Phase 3: Write Amendments
Amend each document in place. Keep amendments minimal and focused — only change what the experiment evidence directly supports. Do not refactor documents; only update what changed.

## Phase 4: Revision Log
Produce `{output_folder}/revisions/08_Revision_Log.md` (or append to it if it exists) containing:
- **Cycle ID:** Which experiment cycle this covers
- **Thesis Status:** hypothesis confirmed / refined / rejected
- **Documents Amended:** list with a one-line summary of each change
- **Next Cycle Hypothesis:** the updated starting hypothesis for the next iteration

## Phase 5: Handoff
Point to the Revision Log. Then based on thesis status:
- **Hypothesis refined** (not rejected): return to **TECHSPEC** (`ai-agent-developer`, capability: `techspec`) for the next experiment cycle with the updated hypothesis.
- **Hypothesis rejected**: return to **Architecture** (`ai-agent-researcher`, capability: `architecture`) to reconsider the paradigm or model family.
- **Hypothesis confirmed** (success criteria met): proceed to **Inference Pipeline** (`ai-agent-developer`, capability: `inference-pipeline`) for production deployment.
