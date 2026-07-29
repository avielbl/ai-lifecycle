# Capability: Decisions & Know-How

## Overview
Captures decisions taken, rejected alternatives, and implementation know-how during experiment planning and execution. Preserves reasoning so future experiments don't repeat investigations.

## Operating Instructions
1. **When to write:** Any time a non-obvious decision is made — dataset selection/rejection, preprocessing choice, architecture quirk, tooling workaround.
2. **Structure each entry:** Context → Finding → Decision (with date and approximate UTC time).
3. **Include rejected alternatives:** Explain why they were rejected — this is as valuable as what was chosen.
4. **Deferred questions:** Maintain a section of open questions punted to the next experiment.
5. **Output:** `{ai_output_folder}/experiments/{ID}/DECISIONS.md`
6. **Review Gate:** Stop after adding entries. Summarize the new entries, ask the user to review and comment, and wait for explicit approval before resuming other work.
7. **Memory Update (mandatory, after approval):** Distill each new DECISIONS.md entry into `{ai_output_folder}/memory/entries/` using the entry template — one `decision` entry per decision (including rejected alternatives, with reasons) — and append one index row each to `{ai_output_folder}/memory/index.md`. Write only facts a future cycle would need; link back to the source document.

## Template Sections
- Numbered decision entries (each with Context, Finding, Decision, Date)
- Execution Decisions table (# | Decision | Why | Date)
- Open Questions Deferred to E-{N+1}
