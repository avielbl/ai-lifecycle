# Capability: Domain Research

## Overview
This capability allows the agent to gather all information required to become a domain expert in a specific given domain. It leverages both external (web) and internal (local docs/KB) sources.

## Phase 1: Environment & Intent Discovery
1. **Identify constraints:** Ask the user:
   - "Are we in an air-gapped environment or do I have internet access?"
   - "What specific domain are we researching?"

2. **Resolve internal sources from config (don't re-ask):** Read `ai_internal_sources` and `ai_mcp_servers` from the resolved config. **Per-run confirmation:** state what is configured and confirm the scopes — e.g. "Researching against Jira projects FOO, BAR and Confluence space ML — still correct?" The user can adjust scopes for this run without editing config. If these keys are missing, ask which sources exist and suggest running `ai-setup configure` to persist the answers.

3. **Air-gapped background folder:** In an air-gapped environment, also ask for the location of a **background folder** containing PDFs and similar reference files. This can be **any path the user names** — not only the conventional `imports/` layout — and complements whatever MCP servers or exports exist.

4. **Establish the "Why":** Ask what specific problem we are trying to solve in this domain to focus the research.

## Phase 2: Knowledge Gathering

### Mode A: Web Research (Open Environment)
- Search the web to find:
  - Industry standards and whitepapers.
  - Scientific literature (arXiv, PubMed, etc.).
  - Competitor approaches or similar use cases.
- Fetch and read promising URLs in depth to extract details.

### Mode B: Internal Discovery (Air-Gapped or Corporate)

Resolve each source through `ai_mcp_servers` **first** — if a server is recorded for it, use B1; otherwise B2. Air-gapped networks often run their **own internal MCP servers** (mirrors/gateways); never assume air-gapped means export-only. Both paths feed the same Domain Knowledge Base — only acquisition differs.

**B1: MCP query (per source with a recorded server)**
- **Jira** (`ai_internal_sources.jira.mode: mcp`): use the recorded server's search tool (JQL) to pull issues matching the domain keywords within the project keys in `ai_internal_sources.jira.scope`; prioritize post-mortems, bugs with `resolution=Won't Fix`, and epics.
- **Confluence:** search the spaces listed in scope for design docs, project charters, and domain glossaries; read the most relevant pages in full.
- **SharePoint:** only if the org recorded a server in `ai_mcp_servers` — otherwise it is export-only (B2).
- **Network shares:** if the share is mounted, prefer native `find`/`grep`/`Read` at the scope path over MCP; use a filesystem MCP server only for unmounted/remote shares.
- Cite every claim with the issue URL/ID or page identifier the server returns.

**B2: Export / drop-folder consumption (sources without a server)**
- **Inventory first:** list `{project-root}/imports/` and the user-named background folder (`find`, file counts, date stamps) before reading anything.
- **Jira exports** (`imports/jira/`, CSV/XML): parse with `grep`/Python for status, resolution, and description columns.
- **Confluence exports** (`imports/confluence/`, unzipped HTML/XML or page PDFs): treat as a local wiki — grep titles, then read pages.
- **SharePoint documents** (`imports/sharepoint/`) and **loose PDFs** (`imports/docs/` and the background folder): read directly — PDFs are readable natively.
- **Cite file paths** for every claim (e.g. `imports/jira/postmortems-2025.csv`, row/issue key) — traceability parity with B1's URLs/IDs.
- **Pause if empty:** if no MCP source is configured and `imports/` plus the background folder are empty or absent, print the export instructions (Jira Issue Navigator → CSV, Confluence space export, SharePoint downloads, PDFs into `imports/docs/` or any folder the user names) and stop — do not silently proceed with web-only research.

## Phase 3: Synthesize & Clarify
1. **Identify Gaps:** After reviewing sources, list what is still unclear or contradictory.
2. **Ask Clarifying Questions:** Present the user with a focused list of 4-6 questions to complete your understanding.
   - *Example:* "Internal doc X says the threshold is 0.5, but recent industry standards suggest 0.7. Which one applies to our specific context?"

## Phase 3.5: Literature Review Handoff
Once the initial domain framing is clear, instruct the user to invoke the Researcher's (Maya) `literature-review` capability for a survey of similar work and candidate research directions, and to return here with its findings (`{output_folder}/research/Literature_Review.md`). Fold the review's comparison and recommended directions into the Prior Art section before completing the Domain Knowledge Base.

## Phase 4: Domain Synthesis Report
Produce a structured summary at `{output_folder}/research/Domain_Knowledge_Base.md` containing:
- **Domain Fundamentals:** Key concepts, entities, and relationships.
- **Success/Failure Definitions:** What matters in this domain?
- **Prior Art:** What has been tried and what were the outcomes?
- **Constraints identified:** Technical, regulatory, or operational.

## Phase 5: Handoff
**Review Gate:** Stop after writing the Domain Knowledge Base. Present a concise summary of its contents, ask the user to review and comment, and wait for explicit approval before proceeding. Once approved, suggest moving to **Ideation & Problem Framing** (`ideation.md`) — do not start it automatically.

**Memory Update (mandatory, after approval):** Distill new atomic facts from the Domain Knowledge Base into `{ai_output_folder}/memory/entries/` using the entry template — `background` entries (domain/data facts that constrain modelling) and `finding` entries (literature/prior-art findings) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.
