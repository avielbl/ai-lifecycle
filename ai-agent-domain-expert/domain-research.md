# Capability: Domain Research

## Overview
This capability allows the agent to gather all information required to become a domain expert in a specific given domain. It leverages both external (web) and internal (local docs/KB) sources.

## Phase 1: Environment & Intent Discovery
1. **Identify constraints:** Ask the user:
   - "Are we in an air-gapped environment or do I have internet access?"
   - "What specific domain are we researching?"
   - "What internal sources (Jira, Confluence, Network Folders, PDF docs) should I prioritize?"

2. **Establish the "Why":** Ask what specific problem we are trying to solve in this domain to focus the research.

## Phase 2: Knowledge Gathering

### Mode A: Web Research (Open Environment)
- Use `google_web_search` to find:
  - Industry standards and whitepapers.
  - Scientific literature (arXiv, PubMed, etc.).
  - Competitor approaches or similar use cases.
- Use `web_fetch` to extract deep details from promising URLs.

### Mode B: Internal Discovery (Air-Gapped or Corporate)
- **Local Documents:** Use `ls -R` and `find` to explore provided directories.
- **Content Analysis:** Use `grep_search` and `read_file` to index and read background materials.
- **System Integration:** If provided with exported data or access to internal tools:
  - **Jira:** Look for issue summaries, failure post-mortems, and technical debt logs.
  - **Confluence:** Look for design docs, project charters, and domain glossaries.
  - **Network Folders:** Scan for datasets, legacy code, and technical specifications.

## Phase 3: Synthesize & Clarify
1. **Identify Gaps:** After reviewing sources, list what is still unclear or contradictory.
2. **Ask Clarifying Questions:** Present the user with a focused list of 4-6 questions to complete your understanding.
   - *Example:* "Internal doc X says the threshold is 0.5, but recent industry standards suggest 0.7. Which one applies to our specific context?"

## Phase 4: Domain Synthesis Report
Produce a structured summary at `{output_folder}/research/Domain_Knowledge_Base.md` containing:
- **Domain Fundamentals:** Key concepts, entities, and relationships.
- **Success/Failure Definitions:** What matters in this domain?
- **Prior Art:** What has been tried and what were the outcomes?
- **Constraints identified:** Technical, regulatory, or operational.

## Phase 5: Handoff
Once the Domain Knowledge Base is satisfied, suggest moving to **Ideation & Problem Framing** (`ideation.md`).
