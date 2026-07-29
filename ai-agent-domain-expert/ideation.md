# Capability: Ideation & Problem Framing

## Overview
Produces the Research Thesis and Product Requirements Document (PRD) by synthesizing domain research findings into a structured problem definition with measurable success criteria.

## Phase 1: Inputs
1. Read `{output_folder}/research/Domain_Knowledge_Base.md` (produced by domain-research capability).
2. If missing, return to **Domain Research** first.
3. Confirm with the user: "Have there been any developments since the Domain Knowledge Base was written that I should factor in?"

## Phase 2: Research Thesis
Produce `docs/Research_Thesis.md` containing:
- **Active Hypothesis:** The single most important question this project must answer.
- **Domain Failure Costs:** What does failure look like in real-world terms? Quantify where possible.
- **Data Characterization:** What data is available, what is its known quality, and what are the known limitations?
- **Success Tiers:** Minimum viable, target, and aspirational criteria — measurable, not vague.
- **Hypothesis History:** Blank at v1.0; updated at each Revision Audit cycle.

**Ask, don't guess:** if multiple viable hypotheses or success thresholds exist, present the options with a brief recommendation and let the user decide.

**Review Gate:** Stop after writing the Research Thesis. Summarize the hypothesis and success tiers, ask the user to review and comment, and wait for explicit approval before starting the PRD.

The Research Thesis is the **single source of truth** for all downstream agents. Every architectural and design decision must trace back to it.

## Phase 3: Product Requirements Document (PRD)
Produce `docs/prd/PRD.md` containing:
- **Problem Statement:** One paragraph, no jargon.
- **User/Stakeholder Needs:** Who is affected and what do they need?
- **Functional Requirements:** What must the model do? (FR-001, FR-002, ...)
- **Non-Functional Requirements:** Latency, throughput, resource constraints, regulatory compliance.
- **Out of Scope:** Explicit list of what this project does NOT cover.

Every functional requirement must reference a finding in the Domain Knowledge Base. Unrooted requirements are rejected.

**Review Gate:** Stop after writing the PRD. Summarize the requirements and scope, ask the user to review and comment, and wait for explicit approval before Phase 4.

## Phase 4: Package Requirements
Determine which frameworks and libraries are likely needed based on the problem framing (not the architecture — that comes later). Write confirmed dependencies to `pyproject.toml` via `uv add --no-sync <package>` as placeholders. Ask the user to confirm before writing. Never run `uv sync` or install anything here — the first installation is Stage 5 (`infra`).

## Phase 5: Handoff
Point to both output documents. Suggest moving to **EDA** (`ai-agent-data-engineer`, capability: `eda`) to characterize the dataset, or **Architecture** (`ai-agent-researcher`, capability: `architecture`) if EDA was already completed externally.

> **Headless mode:** skip confirmation steps, produce both documents with sensible defaults, output the document paths on completion.
