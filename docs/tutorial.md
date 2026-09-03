# Tutorial: Building a Tabular Fraud-Detection Classifier with AI Lifecycle

A hands-on walk through every stage (0 → 9) using a realistic example: a card-transaction fraud classifier for a payments team. Each stage shows what you invoke, what the agent asks, what artifact lands where, and the review gate that ends it. Interactions are abridged — your sessions will be longer.

Conventions used below: `ai_output_folder` is configured as `docs`, the tracker is MLflow, and the IDE is Claude Code. **Every stage ends with a review gate** — the agent stops, summarizes, and waits for your explicit approval; nothing chains automatically.

---

## Stage 0 — Install, Configure, Scaffold

### Install the module

```bash
npx bmad-method install --directory . --modules bmm \
  --custom-source https://github.com/avielbl/ai-lifecycle --tools claude-code --yes
```

The BMad installer collects the **core** settings (your name, languages, output folder) itself.

### Configure — note the dedup

```
/ai-setup   → configure
```

Because the installer already owns the core keys, `configure` **never re-asks them** — it only prompts for module keys that are still missing:

> **ai-setup:** Fresh install detected. Core settings (user_name: Dana, output_folder: `{project-root}/_bmad-output`) are inherited from the BMad install — I'll show them in the summary where you can still override them. I only need the module settings:
> 1. Where should lifecycle documents be saved? [docs]
> 2. LLM provider for analysis scripts? [anthropic] — and which model name?
> 3. Experiment tracking platform? [none]
> 4. Which internal knowledge sources exist? [none]
>
> *You:* docs / anthropic, claude-sonnet-4-6 / mlflow / jira + confluence

Selecting internal sources triggers **MCP detection (Step 2b)**:

> **ai-setup:** Detected MCP servers: `mcp__atlassian` (Jira+Confluence). Use these for internal-source research? Are there additional or **internal** MCP servers I can't see — e.g. mirrors/gateways on an air-gapped network? Also: which Jira project keys and Confluence spaces are in scope?
>
> *You:* Yes, use atlassian. No internal servers. Jira: PAY, FRAUD. Confluence: RISK.

Because a tracker was chosen, it also asks `ai_tracker_url` (blank = SaaS) and `ai_tracker_offline` (auto). Finally, fresh installs get: *"Import memory from a previous project? (path to its `memory/` folder, or none)"*.

> This tutorial runs the default `standard` prompt flavor; if you use a mid-tier or local model, a `guided` flavor with step-by-step scaffolding exists — switch via `ai_prompt_flavor` in `_bmad/config.user.yaml` (see "Prompt Flavors" in the README).

**What lands:** the `ai` section in `_bmad/config.yaml` (+ `config.user.yaml`), `module-help.csv` rows for `/bmad-help`, the output directory tree, and the seeded memory bank — `docs/memory/index.md` (header row only) and `docs/memory/imports.yaml`.

### Scaffold the project

```
/ai-setup   → new-project
```

The skill collects project name, IDE, Python version, tracker, data location, artifact registry, compute topology, and git remote, then runs:

```bash
uv run .claude/skills/ai-lifecycle/scripts/init_project.py \
  --ide claude-code --tracker mlflow --python-version 3.11 \
  --data-location local --artifact-registry tracker-native \
  --compute same-machine --git-remote git@github.com:acme/fraud-detector.git --yes
```

**What lands:** the directory tree (`data/`, `src/fraud_detector/`, `tests/`, `notebooks/`, `configs/`, `scripts/`, `logs/`, `docs/…`), `pyproject.toml` with **zero dependencies**, an empty `.venv` via `uv venv`, a git repo on `main` with the scaffold committed and `origin` registered (**never pushed** — it prints `git push -u origin main` as a next step), `.claude/CLAUDE.md`, `configs/llm_config.yaml`, `configs/project_infra.yaml` (data/artifacts/compute decisions), `docker/Dockerfile.train` + `docker/README.md` (built at Stage 5+, not now), and the gitignored `imports/` drop-folder tree.

---

## Stage 1 — Domain Research (Alex)

```
/ai-agent-domain-expert   → domain-research
```

> **Alex:** Are we air-gapped or do I have internet access? What domain are we researching, and what problem are we solving? Config says internal sources: Jira (PAY, FRAUD via `mcp__atlassian`) and Confluence (RISK) — still correct for this run?

Alex researches the web (chargeback economics, PSD2/SCA rules, class-imbalance norms in fraud) and queries Jira via MCP — pulling post-mortems and `Won't Fix` bugs from PAY/FRAUD — then asks 4–6 clarifying questions ("Is the cost of a false positive a blocked legitimate transaction, or a manual review? What is the review team's daily capacity?").

At Phase 3.5 Alex hands off: *"Invoke Maya's `literature-review` now and come back with `docs/research/Literature_Review.md`."*

**Artifact:** `docs/research/Domain_Knowledge_Base.md` (fundamentals, success/failure definitions, prior art, constraints), every internal claim cited by Jira issue key or Confluence page. **Gate:** Alex stops and waits for approval, then (mandatory Memory Update) distills `background`/`finding` entries into `docs/memory/entries/` with one index row each.

## Stage 1.2 — Literature Review (Maya, optional)

```
/ai-agent-researcher   → literature-review
```

Maya reads the in-progress Domain Knowledge Base, asks whether you have internet access, surveys papers/benchmarks/OSS implementations (or, air-gapped, queries an internal MCP mirror and asks for a background folder of PDFs at **any path you name**), writes a per-article structured summary and a cross-article **comparison matrix** (approach × data regime × metrics × compute × maturity × applicability), then presents ranked candidate directions:

> **Maya:** Ranked directions: (1) gradient boosting on engineered features — best cost/performance for tabular fraud; (2) TabNet; (3) anomaly-detection hybrid. I recommend (1). Which carry forward? *(Ask, don't guess — you decide.)*

**Artifact:** `docs/research/Literature_Review.md`. **Gate:** approval, then `finding` memory entries; hand back to Alex to fold into the Domain KB.

## Stage 1.5 — Ideation (Alex)

```
/ai-agent-domain-expert   → ideation
```

Alex retrieves matching `background`/`finding` memory entries, then writes the **Research Thesis** (`docs/Research_Thesis.md`: active hypothesis, failure costs, data characterization, success tiers) — gate — then the **PRD** (`docs/prd/PRD.md`: FR-/NFR- requirements, each traceable to the Domain KB) — gate. Then Phase 4:

> **Alex:** Likely dependencies: pandas, scikit-learn, xgboost, mlflow. Confirm and I'll record them as **placeholders** via `uv add --no-sync` — nothing is installed until Stage 5.

**Memory Update:** one `evolution` entry — the root of the project-evolution chain.

## Stage 2 — EDA (Sam)

```
/ai-agent-data-engineer   → eda
```

Sam reads the Research Thesis and `background` memory entries, asks for the data path, and runs the EDA suite through **ephemeral** environments (`uv run --with … / uvx` — never installing into the project): `eda_analyzer.py`, `baseline_classifier.py`, `class_weights_calculator.py`, optionally `clustering_explorer.py`. Judgment calls are surfaced, not guessed:

> **Sam:** 0.17% fraud rate. Options for imbalance: (a) class weights — my recommendation, no leakage risk; (b) oversampling; (c) focal loss later. Split strategy: transactions are time-ordered — I recommend a temporal split over random. Your call on both.

**Artifacts (two, both gated together):**
- `docs/eda/EDA_Report.md` — distributions, quality, leakage checks, the **baseline performance floor**, recommended class weights, implications for architecture.
- `notebooks/eda_report.ipynb` — built programmatically (`scripts/build_notebook.py` + nbformat) and **executed headlessly** via `jupyter nbconvert --execute`, so committed cells contain rendered histograms, correlation heatmap, class-balance chart, and baseline tables.

After approval Sam updates Thesis Section IV and writes `background` memory entries (data facts + baseline floor).

## Stage 3 — Architecture (Maya)

```
/ai-agent-researcher   → architecture
```

Maya reads Thesis + EDA report and retrieves `finding`/`result`/`decision` entries. Ask-don't-guess moment:

> **Maya:** Paradigm candidates: (a) XGBoost — strong tabular baseline, fast iteration (recommended); (b) LightGBM; (c) TabNet. Tracker: config says MLflow — I'll keep it unless you want to revisit (any change is written back via `ai-setup configure`).

**Artifact:** `docs/architecture/Architecture.md`. **Gate**, then memory: `decision` entries for the chosen paradigm **and each rejected one, with reasons**.

## Stage 4 — Detailed Design (Maya)

```
/ai-agent-researcher   → detailed-design
```

Maya breaks the architecture into task tables: `INF-01` data loader with temporal split, `INF-02` feature pipeline, `INF-03` eval harness + MLflow logging; `EXP-01` weighted XGBoost vs baseline, `EXP-02` feature-set ablation. **Artifact:** `docs/design/Detailed_Design.md`. **Gate.**

## Stage 4.5 — TECHSPEC (Kai)

```
/ai-agent-mlops-engineer   → techspec
```

Kai retrieves `result`/`decision` entries, creates the experiment folder, reads `configs/project_infra.yaml` for the compute section, and locks the contract — hypothesis, preprocessing, params table, arms, **acceptance gates** (Tier 1 mandatory: beat baseline AUPRC by ≥20%; Tier 2/3), execution plan, risks. Tier thresholds are presented as options, not guessed. **Artifact:** `docs/experiments/E1/TECHSPEC.md`. **Gate** — nothing trains until you approve. (Optionally record early trade-offs now with `decisions` → `docs/experiments/E1/DECISIONS.md`, Stage 4.6.)

## Stage 5 — Infrastructure (Kai)

```
/ai-agent-mlops-engineer   → infra
```

Kai retrieves `lesson` entries, implements the INF-* tasks, then runs **the first and only package installation** of the lifecycle: `uv sync`. Next, **tracker verification**: `mlflow.MlflowClient(tracking_uri=…).search_experiments(max_results=1)` using `ai_tracker_url`. On success the resolved URL is recorded in the Infra Log; on failure (or `ai_tracker_offline: true`) Kai **warns, switches to the offline store (`file:./mlruns`), records it, and continues** — a dead tracker never hard-fails Stage 5. A smoke test on dummy data closes the stage. **Artifact:** `docs/implementation/Infra_Log.md` (including failed attempts — mandatory). **Gate**, then `lesson` memory entries.

## Stage 6 — Experiment (Jordan)

```
/ai-agent-experimentation-engineer   → experiment
```

Before this (and any cycle), run **advise** — see below. Jordan reads the TECHSPEC and the tracker mode from the Infra Log (offline runs get task IDs like `offline:./mlruns/<run_id>`), retrieves tooling `lesson` entries, smoke-tests, then executes the arms exactly as contracted — deviations are asked, never improvised. **Artifacts:** `docs/experiments/E1/RUN_2026-07-29_10-00-00.md` (per-arm tables, UTC timeline, issues) + archived configs in `docs/experiments/E1/configs/`. **Gate.**

## Stage 6.5 — Results (Jordan)

```
/ai-agent-experimentation-engineer   → results
```

Raw outputs only, no interpretation: metrics pulled from MLflow's API (or the local store when offline — identical document either way), tier comparison tables, param counts, convergence data, learning curves, exact reproduction commands. **Artifact:** `docs/experiments/E1/RESULTS_….md`. **Gate.**

## Stage 7 — Analysis (Maya)

```
/ai-agent-researcher   → analysis
```

Maya interprets against the TECHSPEC gates: verdict per tier at top, root causes, **What Went Wrong** (mandatory — an analysis with no failures documented is incomplete), validated parameters, next steps traceable to findings. **Artifact:** `docs/experiments/E1/ANALYSIS_….md`. **Gate**, then memory: `lesson` + `result` entries. If the baseline is stable and tiers are near-missed, Stage 7.5 `hparam` runs an HPO sweep (search-space doc gated before the sweep; `result` entries after) and loops back to Stage 6.

## Anytime — Advise & the Memory Bank in Action

```
/ai-agent-domain-expert   → advise
```

> **Alex:** What are you about to build? — *"E2: tuned XGBoost with the v2 feature set."*

Alex queries **index-first**: filters `docs/memory/index.md` rows by type/tags, reads only the matching entries (each <20 lines), follows `[[entry-id]]` links one hop, searches any imported banks from `imports.yaml` (read-only; load-bearing imported facts are copied in), and only opens a full document when an entry's `Source:` pointer needs verbatim detail. A typical entry and its index row:

```markdown
---
id: dec-004
type: decision
stage: 4.6-decisions
exp_id: E1
tags: [imbalance, sampling, tabular]
date: 2026-07-29
status: active
superseded_by: null
---
**Fact:** Class weights chosen over oversampling for the fraud dataset.
**Why:** Oversampling duplicated near-identical fraud rows → val AUPRC dropped 0.03.
**Links:** [[bg-001]] · Source: experiments/E1/DECISIONS.md #3
```

```markdown
| dec-004 | decision | 4.6-decisions | E1 | imbalance,sampling | Class weights over oversampling — duplication leaked |
```

**Artifact:** `docs/advisory/Advisory_xgboost-hpo_2026-07-29.md` (validated findings, dead ends, recommended starting point). **Gate.**

## Stage 8 — Revision Audit (Alex)

```
/ai-agent-domain-expert   → revision-audit
```

Alex reads the E1 Analysis + TECHSPEC, asks which cycle/docs to cover, and amends the Thesis (Hypothesis History is mandatory), PRD, Architecture, and Detailed Design — minimally, only what the evidence supports. **Artifact:** `docs/revisions/Revision_Log.md`. **Gate**, then `evolution` memory entries; revision-audit is also the **only** capability allowed to mark bank entries superseded and to compact the index past ~200 rows. Routing: hypothesis refined → back to TECHSPEC (E2); rejected → back to Architecture; confirmed → toward deployment.

## Stage 9 — Deployment (Kai)

```
/ai-agent-mlops-engineer   → deployment
```

**Phase A — goal gate (hard stop):** Kai tabulates Thesis tiers vs best achieved results from the Analysis and Revision Log:

> **Kai:** Tier 1 (AUPRC ≥ 0.42): achieved 0.47 — pass. Tier 2: pass. Tier 3: miss. Decide: **deploy as-is** / one more cycle / descope. I recommend deploy as-is.

No deployment work happens until you declare the goal reached. **Phase B — requirements:** serving mode, latency/throughput targets, target environment (confirmed against `configs/project_infra.yaml`), packaging, monitoring, rollback, security, ownership — each elicited with options + recommendation → `docs/deployment/Deployment_Requirements.md`. **Gate.** **Phase C — implementation:** invokes `inference-pipeline` (model adaptation + V&V on the test set), builds the serving image from the `docker/Dockerfile.train` base, writes deploy/health-check/rollback scripts, wires monitoring, smoke-tests end-to-end → `docs/deployment/Deployment_Report.md` (failed attempts mandatory). **Final gate**, then `lesson` memory entries — and the lifecycle is complete.

---

## Where Everything Landed

```
docs/
├── Research_Thesis.md            prd/PRD.md
├── research/    Domain_Knowledge_Base.md · Literature_Review.md
├── eda/EDA_Report.md             (+ notebooks/eda_report.ipynb, executed)
├── architecture/Architecture.md  design/Detailed_Design.md
├── experiments/E1/  TECHSPEC.md · DECISIONS.md · RUN_*.md · RESULTS_*.md · ANALYSIS_*.md · configs/
├── implementation/  Infra_Log.md · Inference_Report.md
├── advisory/  revisions/Revision_Log.md  deployment/{Deployment_Requirements,Deployment_Report}.md
└── memory/  index.md · entries/*.md · imports.yaml
```

Run `/bmad-help` at any point — it reads project state and tells you the next agent and capability.
