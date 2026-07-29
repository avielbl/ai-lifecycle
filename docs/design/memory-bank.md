# Design: Per-Project Memory Bank

> Status: **Proposed** — target Sprint 3. Design only; no skill changes in this document.

Every agent SKILL.md currently carries a "Memory & Learning" paragraph that begins *"If memory is enabled..."* — but no mechanism exists. Agents that need history (notably `advise`, `techspec`, `architecture`) re-read entire lifecycle documents: analysis reports, decision logs, the Domain Knowledge Base. That burns context on prose when the agent needs five facts. This design replaces the placeholder with a concrete, file-based knowledge bank.

## 1. Goals

1. **Small contexts.** An agent session loads only a compact index (one line per knowledge entry). Capabilities retrieve the handful of entries relevant to their stage — never whole upstream documents for background knowledge.
2. **Accumulation.** Knowledge survives across experiment cycles (E1 → E2 → ...) and across projects. Each cycle appends; nothing is lost when documents are amended by `revision-audit`.
3. **Zero new infrastructure.** Works air-gapped, with no dependencies beyond the filesystem, and diffs cleanly in git.

Non-goals: replacing lifecycle documents (they remain the authoritative long-form record), semantic/vector search, and any runtime service.

## 2. Content Taxonomy

Six entry types, each with a fixed id prefix:

| Type | Prefix | What it captures | Example hook |
|------|--------|------------------|--------------|
| `background` | `bg-` | Domain/data facts that constrain modelling | "Sensor dropout >3s means hard-fail in this domain" |
| `finding` | `fnd-` | Literature-review findings (papers, prior art, benchmarks) | "SpecAugment gives +2-4% on low-resource audio (arXiv:1904.08779)" |
| `lesson` | `les-` | Implementation lessons learned (infra bugs, tooling, workarounds) | "DataLoader workers >4 deadlock on the NFS mount — pin to 2" |
| `result` | `res-` | Experiment conclusions and validated parameters | "E2: lr 3e-4 + cosine confirmed stable across all arms" |
| `decision` | `dec-` | Key decisions **and rejected alternatives** with reasons | "Rejected oversampling; class weights won on val AUPRC" |
| `evolution` | `evo-` | Project-evolution rationale — why the thesis/design changed between cycles | "E1 failure shifted thesis from detection to ranking" |

Rules: one entry = one atomic, reusable fact. If it takes more than ~15 lines, it belongs in a lifecycle document and the entry should link to it. Rejected alternatives are first-class `decision` entries — the bank exists precisely so dead ends are not re-explored.

## 3. Storage Options Compared

| Criterion | (a) Markdown + index file | (b) SQLite + query script | (c) JSON knowledge-graph |
|-----------|--------------------------|---------------------------|--------------------------|
| LLM-friendliness (read/write via prompts) | **Excellent** — agents natively read/write markdown | Poor — requires script mediation for every access | Fair — writable but error-prone (strict syntax, escaping) |
| Git-diffability | **Excellent** — line-level diffs, human-reviewable | None (binary) | Poor — noisy diffs, merge conflicts |
| Air-gapped operation | **Yes** | Yes (stdlib) | Yes |
| Extra dependencies | **None** | Python + script maintenance | None, but needs a validator script in practice |
| Retrieval precision at scale | Good to ~500 entries via index scan + typed grep; degrades beyond | **Excellent** (indexed queries) | Good (typed edges) but only via tooling |

**Recommendation: (a) markdown + index for v1**, with graph semantics layered on top via `[[entry-id]]` references in entry bodies — this gives typed links without JSON's fragility. Rationale: agents are the only readers and writers, and they handle markdown with near-zero failure rate; every entry is reviewable in a PR; it works identically in air-gapped corporate environments (an explicit constraint of this module — see `domain-research.md` Mode B).

**Growth path:** the frontmatter schema below is deliberately relational (id, type, stage, exp_id, tags). If a project exceeds ~500 entries and index-scan retrieval degrades, a one-shot script can ingest all entries into SQLite (option b) without changing a single entry file — the markdown remains the source of truth and the DB becomes a derived cache.

## 4. Layout

```
{ai_output_folder}/memory/
├── index.md            # the ONLY file loaded at agent activation
├── entries/
│   ├── bg-001-sensor-dropout.md
│   ├── dec-004-no-oversampling.md
│   └── les-012-nfs-dataloader.md
└── imports.yaml        # optional — paths to other projects' banks (§7)
```

**Entry file** — `entries/{id}-{slug}.md`:

```markdown
---
id: dec-004
type: decision
stage: 4.6-decisions
exp_id: E1
tags: [imbalance, sampling, tabular]
date: 2026-07-29
status: active            # active | superseded
superseded_by: null       # entry id, when status: superseded
---
**Fact:** Class weights chosen over oversampling for the fraud dataset.

**Why:** Oversampling duplicated near-identical fraud rows → val AUPRC
dropped 0.03 from leakage-like memorization. Weights matched baseline
compute with no leakage risk.

**Links:** [[bg-001]], [[res-007]] · Source: experiments/E1/DECISIONS.md #3
```

**Index file** — `index.md`, exactly one table row per entry, hook ≤ 100 chars:

```markdown
| id | type | stage | exp | tags | hook |
|----|------|-------|-----|------|------|
| bg-001 | background | 1-research | - | sensors,latency | Sensor dropout >3s is a hard operational failure |
| dec-004 | decision | 4.6-decisions | E1 | imbalance,sampling | Class weights over oversampling — duplication leaked |
| les-012 | lesson | 5-infra | E2 | dataloader,nfs | DataLoader workers >4 deadlock on NFS — pin to 2 |
```

Superseded entries stay in the index with `~~struck-through~~` hooks so agents see that the topic was revisited (and can follow `superseded_by`).

## 5. Write Protocol

Every writing capability gets a short, mandatory **"Memory Update"** step appended after its final output step: *"Distill new atomic facts into `{ai_output_folder}/memory/entries/` using the entry template, and append one index row each. Write only facts a future cycle would need; link back to the source document."*

| Capability (stage) | Writes entry types |
|--------------------|--------------------|
| `domain-research` (1) | `background` + `finding` (literature portion of the Domain KB) |
| `ideation` (1.5) | `evolution` (initial thesis rationale — the root of the chain) |
| `eda` (2) | `background` (data-quality facts, baseline number) |
| `architecture` (3) | `decision` (paradigm choice + rejected paradigms), `finding` |
| `techspec` (4.5) | — (contracts are per-experiment; no bank writes) |
| `decisions` (4.6, anytime) | `decision` (each DECISIONS.md entry distilled to one bank entry) |
| `infra` (5) | `lesson` (infra bugs, fixes, generalizable rules) |
| `experiment` / `results` (6/6.5) | — (raw data stays in the experiment folder) |
| `analysis` (7) | `lesson` (What Went Wrong rules) + `result` (verdict, validated params) |
| `hparam` (7.5) | `result` (confirmed ranges) |
| `revision-audit` (8) | `evolution` (why upstream docs changed — the cross-cycle reasoning chain); marks superseded entries |
| `inference-pipeline` (anytime) | `lesson` (deployment/V&V learnings) |
| `advise` (anytime) | — (read-only consumer) |

Ownership rule: a capability only writes its listed types. `revision-audit` is additionally the only capability that flips `status: superseded` — keeping contradiction handling in one place.

## 6. Read Protocol

1. **Activation:** each SKILL.md instructs the agent to read `{ai_output_folder}/memory/index.md` (and nothing else from the bank) when activated. Missing index = fresh project, proceed normally.
2. **Retrieval:** each capability file names the types/tags relevant to its stage, e.g. `techspec`: *"Retrieve `result` and `decision` entries whose tags intersect the current experiment's topic before locking parameters."* The agent scans the in-context index and Reads only the matching `entries/*.md` files (typically 3–10 files, each <20 lines). `[[entry-id]]` links may be followed one hop when an entry references its justification.
3. **`advise` becomes a bank query.** Phase 2 of `advise.md` is rewritten: instead of globbing `experiments/*/ANALYSIS_*.md` and reading full reports, Alex filters the index by the user's intent (type ∈ {result, decision, lesson} + tag match), reads the matching entries, follows links, and only opens a full lifecycle document when an entry's `Source:` pointer needs verbatim detail. Imported banks (§7) are searched the same way.

## 7. Cross-Project Reuse

`memory/imports.yaml` lists read-only external banks:

```yaml
imports:
  - name: fraud-v1
    path: /path/to/fraud-v1/docs/memory   # absolute or relative; local mount is fine air-gapped
    note: same data source, prior paradigm was XGBoost
```

- `ai-setup configure` gains an optional prompt: "Import memory from a previous project? (path)".
- Readers treat imported banks exactly like the local one, prefixing ids in citations (`fraud-v1:res-007`). **Imports are never written to.**
- `advise` is the primary consumer: its index scan covers local + imported indexes, so "what worked last project" costs one small file per import.
- If a fact from an imported bank becomes load-bearing, the consuming capability copies it into the local bank as a new entry with a `Source: fraud-v1:res-007` line — the local bank stays self-contained if the import path later disappears.

## 8. Skill-File Change List (Sprint 3)

| File | Edit |
|------|------|
| `ai-agent-domain-expert/SKILL.md`, `ai-agent-data-engineer/SKILL.md`, `ai-agent-researcher/SKILL.md`, `ai-agent-mlops-engineer/SKILL.md`, `ai-agent-experimentation-engineer/SKILL.md` | Replace the "Memory & Learning — if memory is enabled..." paragraph with: read `{ai_output_folder}/memory/index.md` on activation; retrieve entries per capability instructions; write entries per the Memory Update steps. (~5 lines, identical wording across agents.) |
| `ai-agent-domain-expert/domain-research.md` | Append Memory Update step (writes `background`, `finding`) |
| `ai-agent-domain-expert/ideation.md` | Append Memory Update step (writes `evolution`); add retrieval of `background`/`finding` |
| `ai-agent-domain-expert/advise.md` | Rewrite Phase 2 as index query over local + imported banks (§6.3); keep document fallback via `Source:` pointers |
| `ai-agent-domain-expert/revision-audit.md` | Append Memory Update step (writes `evolution`; supersedes contradicted entries) |
| `ai-agent-data-engineer/eda.md` | Append Memory Update step (writes `background`); retrieval of `background` |
| `ai-agent-researcher/architecture.md` | Retrieval (`finding`, `result`, `decision`); Memory Update (writes `decision`, `finding`) |
| `ai-agent-researcher/detailed-design.md` | Retrieval only (`decision`, `lesson`) |
| `ai-agent-researcher/analysis.md` | Append Memory Update step (writes `lesson`, `result`) |
| `ai-agent-mlops-engineer/techspec.md` | Retrieval only (`result`, `decision`) — validated params inform the contract |
| `ai-agent-mlops-engineer/decisions.md` | Append Memory Update step (each decision distilled to a `dec-*` entry) |
| `ai-agent-mlops-engineer/infra.md` | Retrieval (`lesson`); Memory Update (writes `lesson`) |
| `ai-agent-mlops-engineer/inference-pipeline.md` | Memory Update (writes `lesson`) |
| `ai-agent-experimentation-engineer/experiment.md` | Retrieval only (`lesson` tagged with the tracker/tooling) |
| `ai-agent-experimentation-engineer/hparam.md` | Retrieval (`result`); Memory Update (writes `result`) |
| `ai-setup/assets/module.yaml` | Add `{ai_output_folder}/memory` and `{ai_output_folder}/memory/entries` to `directories` |
| `ai-setup/SKILL.md` | `configure` seeds an empty `index.md` (header row) and offers the imports prompt (§7) |
| `README.md` | Add a "Memory Bank" section under Key Principles; note it in the version log |

No scripts and no CSV changes required for v1 (the bank is not a lifecycle stage; it is a side effect of existing stages).

## 9. Open Decisions

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Storage backend | (a) markdown + index · (b) SQLite + script · (c) JSON graph | **(a)** — LLM-native, diffable, air-gapped, zero deps; SQLite as a derived cache only if a project passes ~500 entries (§3) |
| 2 | Per-agent vs shared bank | one bank per agent · one shared bank | **Shared bank with type ownership** (§5 table) — agents consume each other's knowledge (Kai's lessons feed Jordan; Maya's results feed Kai's TECHSPECs); per-agent banks would force cross-reads anyway |
| 3 | Index size cap | no cap · hard cap with archive file · shard per type | **Cap at ~200 rows**; when exceeded, `revision-audit` compacts — merges superseded/stale rows into `index-archive.md` (still searchable on demand, never auto-loaded). Shard per type only if a single type dominates |
| 4 | Entry mutability | edit in place · append-only + supersedes | **Append-only with `superseded_by`** — preserves the evolution chain and keeps git history honest; only `revision-audit` flips status |
| 5 | Cross-project import | path reference (read-only) · physical copy · curated export | **Path reference** (§7), with copy-on-use for load-bearing facts — cheapest, and works on shared network folders in air-gapped setups |
| 6 | Index maintenance | writer appends row inline · CI/validation script | **Writer appends inline** for v1; add a ~30-line `scripts/validate_memory.py` (ids unique, every entry indexed, links resolve) to `validate_skills.yml` in a later sprint if drift appears |
