# Capability: Literature Review

## Overview
Surveys potential similar work and research directions for the problem framed by the Domain Expert (Alex) in Stage 1. Collects papers, preprints, blog posts, benchmark results, and open-source implementations addressing the same problem class, summarizes each in a structured form, and builds an extensive comparison across all of them. The synthesis feeds back into Alex's Domain Knowledge Base and Ideation — this capability is invoked as a handoff from `domain-research`, not standalone.

## Operating Instructions
1. **Inputs:** Read the initial Domain Knowledge Base notes at `{ai_output_folder}/research/Domain_Knowledge_Base.md` (may be in progress). If it does not exist yet, ask the user for the raw problem statement and any framing Alex has produced so far.
2. **Identify environment:** Ask whether we have internet access or are air-gapped.

### Mode A: Web Search (Open Environment)
- Search for scientific literature (arXiv, conference proceedings), preprints, technical blog posts, benchmark/leaderboard results, and open-source implementations on the problem class.
- Fetch and read the most promising sources in depth; prefer primary sources over summaries.

### Mode B: Internal Sources (Air-Gapped or Corporate)
- **MCP first:** read `ai_mcp_servers` from the resolved config. Air-gapped networks may run their **own internal MCP servers** (e.g. an internal arXiv mirror or paper-search gateway) — never assume air-gapped means no MCP. If a relevant server is recorded, query it for papers and prior work before asking for files.
- **Background folder:** ask the user for the location of a background folder containing PDFs, exported papers, or saved articles — **any path the user names** (the conventional `imports/docs/` is only a default suggestion).
- Enumerate and read every provided document; ask the user to fill obvious coverage gaps if key topics are missing.
- Cite MCP results by their returned identifier/URL and file-based sources by file path.

3. **Per-article summary:** For each source, capture in a fixed structure:
   - Citation (authors, title, venue/URL, year)
   - Problem addressed
   - Approach / architecture
   - Data used (type, scale, availability)
   - Metrics and headline results
   - Strengths
   - Limitations
   - Relevance to our problem
4. **Comparison matrix:** Build an extensive cross-article comparison table: approach vs. data regime vs. metric/results vs. compute requirements vs. maturity (paper-only / code available / production-proven) vs. applicability to our constraints. Discuss the notable contrasts below the table — do not leave the matrix uninterpreted.
5. **Synthesis:** Derive candidate research directions, ranked. Identify gaps in prior work our project could exploit. State your recommended direction(s) with justification.
6. **Ask, don't guess:** Present the ranked directions and your recommendation to the user — the user decides which direction(s) carry forward. Never silently commit to a direction.
7. **Output:** Write `{ai_output_folder}/research/Literature_Review.md`.
8. **Review Gate:** Stop after writing the document. Summarize the findings and recommendation, then wait for explicit user approval before handing back to Alex (domain-expert) to complete the Domain Knowledge Base and proceed to `ideation`.
9. **Memory Update (mandatory, after approval):** Distill new atomic facts from the Literature Review into `{ai_output_folder}/memory/entries/` using the entry template — `finding` entries (papers, prior art, benchmark results with their citation) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.

## Output Template
- Scope and Search Strategy (mode used, queries or drop folder contents)
- Article Summaries (one structured entry per source)
- Comparison Matrix (approach × data regime × metrics × compute × maturity × applicability)
- Gaps in Prior Work
- Candidate Research Directions (ranked, with recommendation)
- Handoff Notes for Domain Expert
