# bmad-dl-lifecycle

> Agentic workflows for the Deep Learning development lifecycle — a custom [BMAD Method](https://github.com/bmad-code-org) module.

This package provides thirteen structured AI workflow skills covering the full lifecycle of a machine learning project: research framing, data exploration, architecture design, infrastructure engineering, experiment execution, hyperparameter optimization, analysis, and iterative revision. Each skill adopts a specific expert role and produces traceable, structured documents.

---

## Getting Started

### Step 1 — Install the package

```bash
# From your project root — add as a git submodule (keeps skills updatable)
git submodule add https://github.com/avielbl/bmad-dl-lifecycle _bmad/bmad-dl-lifecycle
git submodule update --init
```

### Step 2 — Scaffold (shell command — run once, no AI involved)

Scaffolding always starts with a plain shell command regardless of IDE. It creates all
folders, writes the IDE config file, and sets up the `uv` project:

```bash
python3 _bmad/bmad-dl-lifecycle/bmad-dl-scaffold/scripts/init_project.py \
  --project-name my_project \
  --project-dir . \
  --ide cline \           # cline | claude-code | antigravity | cursor
  --tracking-tool wandb   # wandb | mlflow | clearml | undecided
```

| `--ide` | Config file written | Skill files copied to |
|---------|--------------------|-----------------------|
| `cline` / `cursor` | `.clinerules` | — (referenced by path) |
| `claude-code` | `.claude/CLAUDE.md` | `.claude/skills/` ← enables slash commands |
| `antigravity` | `.clinerules` | — (auto-discovered globally) |

**No packages are installed.** `pyproject.toml` is written with an empty `dependencies = []`.

### Step 3 — Let BMAD route you

After scaffolding, run `/bmad-help` in your IDE. It reads `_bmad/_config/bmad-help.csv`
(updated by `init_project.py`) and tells you exactly what to do next.

### Step 4 — Invoke skills (IDE-specific)

How you trigger each lifecycle stage depends on your IDE:

#### Antigravity
Skills are auto-discovered globally. Use slash commands directly:
```
/bmad-dl-ideation
/bmad-dl-eda
...
```

#### Claude Code
The scaffold step copies skills into `.claude/skills/`, enabling slash commands:
```
/bmad-dl-ideation
/bmad-dl-eda
...
```

#### VSCode + Cline / Cursor
No slash commands. Tell the AI to follow a skill by referencing its path — either paste
this into chat or add it to your system prompt:

```
Follow the workflow in: _bmad/bmad-dl-lifecycle/bmad-dl-ideation/SKILL.md
```

The `.clinerules` file lists all skill paths for quick copy-paste.

---

### Package lifecycle

| Stage | Action | Who |
|-------|--------|-----|
| Stage 1 — `bmad-dl-ideation` | Domain Expert determines required packages, writes them via `uv add --no-sync` | AI agent |
| Stage 5 — `bmad-dl-infra` | **First `uv sync`** — installs everything | AI agent |
| Any stage | `uv add <pkg>` — adds a package and updates `pyproject.toml` | AI agent or user |

> **Never use `pip install`.** All package management goes through `uv`. Never run `uv sync` before Stage 5.

---

## Skills Overview

### Sequential Lifecycle Skills

| # | Skill | Role | Output |
|---|-------|------|--------|
| 0 | `bmad-dl-scaffold` | Scaffolding | Folder structure, `.clinerules`, `pyproject.toml` (no deps) |
| 1 | `bmad-dl-ideation` | Domain Expert | `docs/00_Research_Thesis.md` + `docs/prd/01_PRD.md` + `pyproject.toml` deps |
| 2 | `bmad-dl-eda` | Data Scientist | `docs/eda/02_EDA_Report.md` |
| 3 | `bmad-dl-architecture` | AI Architect | `docs/architecture/03_Architecture.md` |
| 4 | `bmad-dl-detailed-design` | AI Tech Lead | `docs/design/04_Detailed_Design.md` (INF-* + EXP-* tasks) |
| 4.5 | `bmad-dl-techspec` | Domain Expert + Tech Lead | `docs/techspecs/TECHSPEC_EXP_[ID].md` |
| 5 | `bmad-dl-infra` | AI Developer + MLOps | `docs/implementation/05_Infra_Log.md` |
| 6 | `bmad-dl-experiment` | AI Developer + Data Scientist | `docs/experiments/06_Experiment_Log.md` |
| 7 | `bmad-dl-analysis` | Data Scientist | `docs/experiments/07_Analysis_EXP_[ID].md` |
| 7.5 | `bmad-dl-hparam` *(conditional)* | Data Scientist + MLOps | `docs/techspecs/HPARAM_EXP_[ID].md` |
| 8 | `bmad-dl-revision` | Domain Expert + Tech Lead | `docs/revisions/08_Revision_Log.md` + amends all upstream docs |

### Universal Tools (run anytime)

| Skill | Purpose | When to Use |
|-------|---------|------------|
| `bmad-dl-advise` | Surface past findings, failure warnings, validated params | Before starting any new experiment or task |
| `bmad-dl-retrospective` | Capture session learnings into team knowledge base | End of any implementation or analysis session |

### Deprecated

| Skill | Status |
|-------|--------|
| `bmad-dl-implementation` | Replaced by `bmad-dl-infra` + `bmad-dl-experiment` in v2.0.0 |

---

## Task Namespaces

Detailed Design produces two categories of tasks with distinct prefixes:

| Prefix | Executed By | Meaning |
|--------|------------|---------|
| `INF-001`, `INF-002`, ... | `bmad-dl-infra` | Infrastructure tasks — built once, reused across all experiment cycles |
| `EXP-001`, `EXP-002`, ... | `bmad-dl-experiment` | Experiment tasks — executed in each cycle against the active TECHSPEC |
| `REV-001`, `REV-002`, ... | Next cycle | Generated by `bmad-dl-revision` for the following cycle |

---

## Experiment Tracking Integration

The module provides native integration patterns for three tracking tools. Choose one at project start; wire it in `bmad-dl-infra` (Stage 5); use it consistently through experiment, HPO, and analysis.

| Tool | Best For | W&B | MLflow | ClearML |
|------|---------|-----|--------|---------|
| [Weights & Biases](https://wandb.ai) | Teams, sweep UI, collaboration | ✓ | | |
| [MLflow](https://mlflow.org) | Self-hosted, open-source, model registry | | ✓ | |
| [ClearML](https://clear.ml) | Auto-capture, enterprise MLOps, HPO orchestration | | | ✓ |

All three are supported in `bmad-dl-infra` (setup), `bmad-dl-experiment` (logging), `bmad-dl-hparam` (sweep), and `bmad-dl-analysis` (querying results).

---

## Hyperparameter Optimization

HPO is a **conditional stage** (7.5) that runs only after `bmad-dl-analysis` confirms the baseline architecture meets at least the TECHSPEC's "Worst case (alive)" tier. Running HPO on a broken architecture wastes compute.

Supported HPO frameworks:

| Framework | Method | Integration |
|-----------|--------|------------|
| **Optuna** | TPE/Bayesian, MedianPruner | `optuna.create_study()` → `study.optimize()` |
| **W&B Sweeps** | Bayesian/random/grid, Hyperband early stopping | YAML config → `wandb sweep` → `wandb agent` |
| **Ray Tune** | ASHA scheduler, distributed multi-GPU | `tune.run()` with resource allocation |
| **ClearML HPO** | Optuna backend, concurrent tasks, auto-clone | `HyperParameterOptimizer` on a base Task ID |

---

## Central Documents

### `docs/00_Research_Thesis.md`
The **single source of truth** read by every agent. Updated at Stage 1 (initial framing), Stage 2 (EDA findings), and Stage 8 (each revision cycle). Contains: active hypothesis, domain failure costs, data characterization, full hypothesis history.

### `docs/techspecs/TECHSPEC_EXP_[ID].md`
Pre-experiment contract written before training starts. Locks parameter search space, compute budget, and tiered success criteria with Domain Expert sign-off. **Never modified after training begins.**

### `docs/knowledge/RETRO_EXP_[ID].md`
Team knowledge base — accumulated via `/bmad-dl-retrospective`. Each entry contains a mandatory Failed Attempts table. Searched by `/bmad-dl-advise` before new work begins.

---

## Lifecycle Flow

```
[0] Init (once — automated scaffolding)
    ↓  folder structure  +  .clinerules  +  pyproject.toml (no deps)
[1] Ideation (Domain Expert)
    ↓  docs/00_Research_Thesis.md  +  docs/prd/01_PRD.md  +  pyproject.toml deps
[2] EDA (Data Scientist + Domain Expert interpretation)
    ↓  docs/eda/02_EDA_Report.md  +  Thesis §IV updated
[3] Architecture (reads Thesis + EDA)
    ↓  docs/architecture/03_Architecture.md
[4] Detailed Design (INF-* + EXP-* task namespaces)
    ↓  docs/design/04_Detailed_Design.md
[4.5] TECHSPEC (pre-experiment contract, Domain Expert sign-off)
    ↓  docs/techspecs/TECHSPEC_EXP_[ID].md
[5] Infra Build (INF-* tasks, smoke-test gate)
    ↓  uv sync  ← FIRST package installation in the project
    ↓  docs/implementation/05_Infra_Log.md
    ↓  data pipeline · training loop · W&B/MLflow/ClearML · eval harness · inference API
[6] Experiment (EXP-* tasks, tracking-tool logged)   ← /advise before, /retro after
    ↓  docs/experiments/06_Experiment_Log.md
[7] Analysis (vs TECHSPEC tiers, tracking-tool query)  ← /advise before, /retro after
    ↓  docs/experiments/07_Analysis_EXP_[ID].md
    ↓
    ├── [7.5] HPO (conditional — only if baseline works)
    │       ↓  docs/techspecs/HPARAM_EXP_[ID].md
    │       └──→ back to [6] with tuned params
    │
    └── [8] Revision (amends ALL upstream docs)
            ↓  docs/revisions/08_Revision_Log.md
            ↓  Thesis · PRD · Architecture · Detailed Design all audited + amended
            └──→ back to [4.5] with new hypothesis
```

---

## Prerequisites

- [BMAD Method](https://github.com/bmad-code-org/bmad-method) installed (`_bmad/` folder present)
- An AI IDE: Claude Code, Antigravity, or VSCode + Cline
- Recommended model: Claude Sonnet 4.5+ or equivalent
- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

---

## Installation

### Option A — Git Submodule (recommended for teams)

```bash
git submodule add https://github.com/avielbl/bmad-dl-lifecycle _bmad/bmad-dl-lifecycle
git submodule update --init
```

Register in `_bmad/_config/manifest.yaml`:

```yaml
modules:
  - name: bmad-dl-lifecycle
    version: 2.0.0
    source: external
    repoUrl: https://github.com/avielbl/bmad-dl-lifecycle
```

Pull updates:

```bash
git submodule update --remote _bmad/bmad-dl-lifecycle
```

### Option B — Manual Copy

```bash
git clone https://github.com/avielbl/bmad-dl-lifecycle
cp -r bmad-dl-lifecycle/bmad-dl-* your-project/_bmad/bmad-dl-lifecycle/
```

---

## IDE Setup

### Claude Code

```bash
for skill in _bmad/bmad-dl-lifecycle/bmad-dl-*; do
  name=$(basename $skill)
  mkdir -p .claude/skills/$name
  cp $skill/SKILL.md .claude/skills/$name/SKILL.md
  cp $skill/bmad-manifest.json .claude/skills/$name/bmad-manifest.json 2>/dev/null || true
done
```

### Antigravity

Auto-discovered from `_bmad/` — no setup needed.

### VSCode + Cline — `.clinerules`

```markdown
# BMAD DL Lifecycle Skills

- Frame research question / PRD: `_bmad/bmad-dl-lifecycle/bmad-dl-ideation/SKILL.md`
- Exploratory data analysis: `_bmad/bmad-dl-lifecycle/bmad-dl-eda/SKILL.md`
- Architecture design: `_bmad/bmad-dl-lifecycle/bmad-dl-architecture/SKILL.md`
- Task breakdown (INF-* + EXP-*): `_bmad/bmad-dl-lifecycle/bmad-dl-detailed-design/SKILL.md`
- Pre-experiment contract: `_bmad/bmad-dl-lifecycle/bmad-dl-techspec/SKILL.md`
- Infrastructure build: `_bmad/bmad-dl-lifecycle/bmad-dl-infra/SKILL.md`
- Training experiment: `_bmad/bmad-dl-lifecycle/bmad-dl-experiment/SKILL.md`
- Experiment analysis: `_bmad/bmad-dl-lifecycle/bmad-dl-analysis/SKILL.md`
- Hyperparameter optimization: `_bmad/bmad-dl-lifecycle/bmad-dl-hparam/SKILL.md`
- Revision + document amendments: `_bmad/bmad-dl-lifecycle/bmad-dl-revision/SKILL.md`
- Search past experiments: `_bmad/bmad-dl-lifecycle/bmad-dl-advise/SKILL.md`
- Capture session learnings: `_bmad/bmad-dl-lifecycle/bmad-dl-retrospective/SKILL.md`
```

---

## Key Principles

- **Scaffold first, install last.** `bmad-dl-scaffold` creates the folder structure without installing packages. The first `uv sync` runs in `bmad-dl-infra` (Stage 5). Never `pip install` or `uv sync` before that.
- **Package decisions in Ideation.** The Domain Expert (Stage 1) determines the framework stack and writes packages to `pyproject.toml` via `uv add --no-sync`. Architecture or domain constraints drive these choices.
- **Use `uv` everywhere.** No `pip install`, no `python -m venv`. Commands: `uv add <pkg>`, `uv sync`, `uv run pytest`.
- **Infra before experiments.** `bmad-dl-infra` builds the runway; `bmad-dl-experiment` flies the plane. Never mix them.
- **HPO only after baseline confirmation.** HPO on a broken architecture wastes compute. Wait for Analysis to clear the minimum viable tier.
- **Run `/bmad-dl-advise` before every experiment.** Skip the days of rediscovery.
- **Run `/bmad-dl-retrospective` after every session.** Claude does the writing; you review.
- **TECHSPECs are contracts.** Never modify after training starts.
- **Failed Attempts sections are mandatory** in Integration Log and Analysis. A log with no failures documented is incomplete.
- **Revision amends all upstream docs.** PRD, Architecture, and Detailed Design must be audited every cycle — not just the Thesis.
- **Fresh context window per skill.** Each skill is long; mixing steps in one session degrades quality.

---

## Output Directory Layout

```
docs/
├── 00_Research_Thesis.md          ← read first, every stage; updated every revision
├── prd/
│   └── 01_PRD.md
├── eda/
│   ├── 02_EDA_Report.md
│   └── 02_class_weights.md
├── architecture/
│   └── 03_Architecture.md
├── design/
│   └── 04_Detailed_Design.md      ← INF-* and EXP-* task tables
├── techspecs/
│   ├── TECHSPEC_EXP_001.md        ← pre-experiment contract, never modified
│   ├── HPARAM_EXP_001.md          ← HPO results, best config
│   └── TECHSPEC_EXP_002.md
├── implementation/
│   └── 05_Infra_Log.md            ← INF-* task log with smoke test results
├── experiments/
│   ├── 06_Experiment_Log.md       ← EXP-* run log with tracking URLs
│   ├── 07_Analysis_EXP_001.md
│   └── 07_Analysis_EXP_002.md
├── revisions/
│   └── 08_Revision_Log.md         ← amendment log for all upstream docs
└── knowledge/                     ← growing team knowledge base
    ├── RETRO_EXP_001_dataloader.md
    └── RETRO_EXP_002_focal_loss.md
```

---

## LLM Engine Configuration

### Agent model (IDE-level)

The model that **executes the SKILL.md prompts** is set inside your IDE — not here:

| IDE | Where to configure |
|-----|--------------------|
| **Cline** | VS Code settings → Cline → Model |
| **Antigravity** | Antigravity settings → Model selector |
| **Claude Code** | `/model` command or `--model` flag |
| **Cursor** | Cursor settings → Model |

Any OpenAI-compatible endpoint supported by your IDE works. Switch models between stages freely — the skills are model-agnostic.

### Programmatic LLM calls (script-level)

Some utility scripts call an LLM directly (e.g., auto-summarization, log interpretation). These use `scripts/llm_client.py`, configured via `configs/llm_config.yaml`.

`bmad-dl-scaffold` copies both files into your project. Edit `configs/llm_config.yaml` to point at the right provider:

```yaml
# Anthropic / Claude (default)
provider: anthropic
model: claude-sonnet-4-6
base_url: ~
api_key_env: ANTHROPIC_API_KEY

# OpenAI-compatible (any endpoint)
# provider: openai-compatible
# model: gpt-4o                       # or: llama3.1:70b, mistral-large-latest, etc.
# base_url: http://localhost:11434/v1  # Ollama, vLLM, Together, Groq, Mistral, Azure…
# api_key_env: OPENAI_API_KEY
```

Usage in a script:

```python
from scripts.llm_client import LLMClient

client = LLMClient()  # reads configs/llm_config.yaml
summary = client.chat("Summarise these training logs: ...", system="You are a data scientist.")
```

The API key is **never stored in the config file** — it lives in the env var named by `api_key_env`.

---

## CI/CD

Two GitHub Actions workflows are included:

- **`validate_skills.yml`** — PR gate: checks SKILL.md frontmatter, manifest structure, semver format, and presence of Failed Attempts sections
- **`update_marketplace.yml`** — auto-generates `marketplace.json` from all manifests on push to `main`

---

## Versioning & Changelog

| Change | Version Bump |
|--------|------|
| New skill added | Minor |
| Prompt/template fix | Patch |
| Breaking output format change | Major |

**Changelog:**
- `v2.1.0` — Added `bmad-dl-scaffold` (Stage 0): automated project scaffolding with `uv`. Creates folder structure, `.clinerules`/`CLAUDE.md`, and an empty `pyproject.toml`. Package requirements are now determined in Stage 1 (`bmad-dl-ideation`) and the first `uv sync` runs in Stage 5 (`bmad-dl-infra`). All skills updated to use `uv run` instead of `python3` directly. README includes full Getting Started guide.
- `v2.0.0` — Split `bmad-dl-implementation` into `bmad-dl-infra` (INF-* tasks, infrastructure + tracking setup) and `bmad-dl-experiment` (EXP-* tasks, training runs). Added `bmad-dl-hparam` (conditional HPO with Optuna/W&B Sweeps/Ray Tune/ClearML HPO). Native W&B, MLflow, and ClearML integration in infra/experiment/analysis skills. Revised task namespace (INF-*/EXP-*/REV-*). `bmad-dl-revision` now explicitly audits and amends all upstream documents. `bmad-dl-analysis` queries tracking tools directly. Stage numbers updated.
- `v1.2.0` — Knowledge flywheel: `bmad-dl-advise`, `bmad-dl-retrospective`, `bmad-dl-techspec`. Mandatory Failed Attempts sections. GitHub Actions CI.
- `v1.1.0` — Dedicated EDA stage. Domain Expert role. Research Thesis document.
- `v1.0.0` — Initial release.

---

## License

MIT
