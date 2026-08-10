# AI Lifecycle

> A structured agentic team for the full AI/ML project lifecycle — a [BMad Method](https://github.com/bmad-code-org/bmad-method) module.

Five specialist agents guide you through the full lifecycle (stages 0–9) — from raw domain research to production deployment. Works across paradigms — deep learning, gradient boosting (XGBoost/LightGBM), transformers, fine-tuning, classical ML, and hybrid approaches.

New here? Follow the [hands-on tutorial](docs/tutorial.md) — a worked fraud-detection example through all stages. Working in a restricted or offline network? See the [air-gapped & corporate guide](docs/air-gapped.md).

---

## Meet the Team

| Agent | Name | Role |
|-------|------|------|
| `ai-agent-domain-expert` | **Alex** | Researches the problem domain, frames the Research Thesis, writes the PRD, and audits upstream docs after each experiment cycle. |
| `ai-agent-data-engineer` | **Sam** | Performs EDA, characterizes data quality and distribution, and establishes a model-agnostic performance baseline. |
| `ai-agent-researcher` | **Maya** | Surveys the literature for similar work, selects the modelling paradigm and architecture, designs the experiment strategy, evaluates results against TECHSPEC tiers, and captures learnings. |
| `ai-agent-mlops-engineer` | **Kai** | Writes TECHSPEC contracts, builds data and training pipelines, adapts trained models for production, and runs the final deployment stage — goal confirmation, requirements, and serving implementation. |
| `ai-agent-experimentation-engineer` | **Jordan** | Executes training and fit runs, logs everything to the experiment tracker, and runs hyperparameter optimization. |

---

## Lifecycle at a Glance

```
[0]   Setup        ai-setup configure / new-project
[1]   Research     Alex   — domain-research     → Domain Knowledge Base
[1.2] Literature   Maya   — literature-review   → Literature Review (optional)
[1.5] Ideation     Alex   — ideation            → Research Thesis + PRD
[2]   EDA          Sam    — eda                 → EDA Report + notebook
[3]   Architecture Maya   — architecture        → Architecture document
[4]   Design       Maya   — detailed-design     → INF-* + EXP-* tasks
[4.5] TECHSPEC     Kai    — techspec            → Pre-experiment contract
[5]   Infra        Kai    — infra               → Pipelines + eval harness
[6]   Experiment   Jordan — experiment          → Experiment Log + configs
[6.5] Results      Jordan — results            → Raw metrics, curves, comparisons
[7]   Analysis     Maya   — analysis            → Interpretation + lessons + next steps
      ├── [7.5]    Jordan — hparam (if needed)  → HPO report → back to [6]
      └── [8]      Alex   — revision-audit      → Revision Log → back to [4.5]
[9]   Deployment   Kai    — deployment          → Requirements + Report (when goal reached)

Anytime:
      Alex   — advise             Surface validated params from past experiments
      Kai    — decisions          Capture know-how and rejected alternatives
      Kai    — inference-pipeline Adapt model for production + V&V
```

---

## Getting Started

### Prerequisites

| Requirement | Notes |
|-------------|-------|
| [BMad Method](https://github.com/bmad-code-org/bmad-method) | **Required** — provides `/bmad-help` routing and `_bmad/` structure |
| AI IDE | Claude Code, Antigravity, or VSCode + Cline / Cursor |
| LLM | Any capable frontier / coding model, selected in your IDE |
| [uv](https://docs.astral.sh/uv/) | Python package manager — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| git | Used by `new-project` to initialise the repo (scaffold still works without it) |
| Docker *(optional)* | Only for building the training/serving images from Stage 5 onward |

### Install the module

Use the BMad installer from your project root. Choose the method that matches your environment:

**From a Git repository or npm registry (default / Artifactory)**

```bash
npx bmad-method install \
  --directory . \
  --modules bmm \
  --custom-source https://github.com/avielbl/ai-lifecycle \
  --tools claude-code \
  --yes
```

If your organisation mirrors npm packages through an internal Artifactory or similar registry, replace the GitHub URL with the package name:

```bash
npx bmad-method install \
  --directory . \
  --modules bmm \
  --custom-source ai-lifecycle \
  --tools claude-code \
  --yes
```

**From a local path (offline / air-gapped environments)**

```bash
npx bmad-method install \
  --directory . \
  --modules bmm \
  --custom-source /path/to/ai-lifecycle \
  --tools claude-code \
  --yes
```

**Interactively**

```bash
npx bmad-method install
# When prompted for a custom source → paste the GitHub URL or local path
```

### Configure (once per project)

Run the setup skill to write config and register capabilities with `/bmad-help`:

```
/ai-setup   → then: configure
```

Or headless with defaults:

```
/ai-setup configure --headless
```

Core settings (user name, languages, output folder) collected by `npx bmad-method install` are never re-asked — `configure` only prompts for module keys that are still missing (they still appear in the confirmation summary, marked "inherited from BMad install", where you can override them). While collecting internal sources, `configure` also auto-detects MCP servers registered in your IDE and asks about internal servers it cannot see (see [Connecting Internal Sources & Trackers](#connecting-internal-sources--trackers)). On a fresh install it additionally offers to import a previous project's memory bank (seeds `memory/imports.yaml`), and it seeds the [Project Memory Bank](#project-memory-bank) files.

#### Why agents run resolve_config on activation

BMad core resolves configuration at **runtime** (every agent activation runs `resolve_config.py` to merge `config.yaml`, `config.user.yaml`, and module defaults) rather than baking values in at install time, because:

- `config.user.yaml` is per-user and gitignored — each collaborator has different values, so nothing user-specific can be frozen into shared files.
- `{project-root}` differs per clone/machine, so absolute paths can only be resolved where the agent actually runs.
- Config can change between sessions (edits, module updates); resolving on activation always picks up the current values.

Agents resolve once at activation and reuse those values for the whole session.

### Scaffold a new project (optional)

For brand-new projects, scaffold the full directory structure, IDE config, and uv project:

```
/ai-setup   → then: new-project
```

This creates `data/` (raw/processed/splits), `src/{package}/`, `tests/`, `notebooks/`, `configs/`, `scripts/` (with copied utility scripts), `logs/`, `docs/` (with lifecycle subfolders), an `imports/` export drop folder (gitignored — see [Connecting Internal Sources & Trackers](#connecting-internal-sources--trackers)), a `pyproject.toml` (no dependencies yet), an empty `.venv` (`uv venv`), a git repo on `main` (plus optional `origin` remote — never auto-pushed), `configs/project_infra.yaml` (data location, artifact registry, compute topology), `docker/` training templates (`Dockerfile.train` + README), and IDE-specific agent config (`CLAUDE.md`, `.clinerules`, `AGENTS.md` for opencode, or `.github/copilot-instructions.md` + prompt files for VS Code Copilot — see the [harness compatibility matrix](#harness-compatibility-matrix)).

> **No packages are installed at scaffold time.** Dependencies are added in Ideation (Stage 1.5) and installed in Infrastructure (Stage 5) via `uv sync`.

### Navigate with BMad Help

```
/bmad-help
```

Reads your project state and tells you exactly which agent and capability to invoke next.

---

## Invoking Agents

### Harness compatibility matrix

The capability prompts are harness-neutral — only the invocation glue differs. `ai-setup new-project --ide <harness>` writes the matching glue files:

| Harness | Invocation | Rules file | MCP | Custom/local models | Caveats |
|---|---|---|---|---|---|
| **Claude Code** | `/ai-agent-<name>` slash commands (skills copied to `.claude/skills/`) | `CLAUDE.md` | yes | Anthropic models | — |
| **Antigravity** | slash commands (auto-discovered globally) | `.clinerules` | yes | bundled models | — |
| **Cline / Cursor** | paste the skill path ("Follow the workflow in: …/SKILL.md") | `.clinerules` | yes | custom OpenAI-compatible endpoints | no slash commands |
| **opencode** | native agent skills — ask for the skill by name; discovered from `.claude/skills/` (Claude-compatible dirs) | `AGENTS.md` | yes (`opencode.json`) | any provider — Ollama, OpenRouter, Azure, **any OpenAI-compatible endpoint** (best on-prem/air-gapped fit) | — |
| **VS Code Copilot (agent mode)** | `/ai-agent-<name>` prompt files in chat (`.github/prompts/*.prompt.md`) | `.github/copilot-instructions.md` (always-on) | yes (GA since VS Code 1.102) | BYOK — official Ollama extension for local models | **agent mode hides models without tool-calling support**; BYOK availability is Copilot-plan-dependent |

### Claude Code

The install step copies agents into `.claude/skills/`, enabling slash commands:

```
/ai-agent-domain-expert   → tell it which capability to activate
/ai-agent-data-engineer
/ai-agent-researcher
/ai-agent-mlops-engineer
/ai-agent-experimentation-engineer
```

### Antigravity

Auto-discovered globally. Use slash commands directly.

### VSCode + Cline / Cursor

No slash commands. Reference the agent by path:

```
Follow the workflow in: .claude/skills/ai-lifecycle/ai-agent-domain-expert/SKILL.md
Activate capability: domain-research
```

The `.clinerules` file generated by `ai-setup new-project` lists all agent paths for quick copy-paste.

### opencode

opencode discovers the agents natively from `.claude/skills/` (it consumes the same SKILL.md convention this module ships) and reads `AGENTS.md` at the project root for the stage order. Ask for a skill by name:

```
Use the ai-agent-domain-expert skill and activate domain-research.
```

Point opencode at any provider or OpenAI-compatible endpoint (vLLM/NIM/Ollama) via `opencode.json` — the strongest pairing for on-prem and air-gapped setups (see [docs/air-gapped.md](docs/air-gapped.md)).

### VS Code Copilot (native agent mode)

`ai-setup new-project --ide copilot` writes `.github/copilot-instructions.md` (always-on rules) plus one prompt file per agent under `.github/prompts/`, restoring slash-command UX in Copilot chat:

```
/ai-agent-domain-expert   → then: activate domain-research
```

Two caveats: agent mode only lists models with tool-calling support (relevant for local/BYOK models), and BYOK availability depends on your Copilot plan.

---

## Stages Reference

### Sequential Lifecycle

| Stage | Agent | Capability | Output |
|-------|-------|------------|--------|
| 1 | Alex (domain-expert) | `domain-research` | Domain Knowledge Base |
| 1.2 *(optional)* | Maya (researcher) | `literature-review` | Literature Review |
| 1.5 | Alex (domain-expert) | `ideation` | Research Thesis + PRD |
| 2 | Sam (data-engineer) | `eda` | EDA Report + notebook |
| 3 | Maya (researcher) | `architecture` | Architecture document |
| 4 | Maya (researcher) | `detailed-design` | Detailed Design (INF-* + EXP-* tasks) |
| 4.5 | Kai (mlops-engineer) | `techspec` | TECHSPEC contract |
| 4.6 *(optional)* | Kai (mlops-engineer) | `decisions` | DECISIONS document (first entries; keep adding anytime) |
| 5 | Kai (mlops-engineer) | `infra` | Pipelines + eval harness + tracker verification |
| 6 | Jordan (experimentation-engineer) | `experiment` | Experiment Log + archived configs |
| 6.5 | Jordan (experimentation-engineer) | `results` | Raw metrics, curves, comparison tables |
| 7 | Maya (researcher) | `analysis` | Interpretation + lessons + next steps |
| 7.5 *(conditional)* | Jordan (experimentation-engineer) | `hparam` | HPO report |
| 8 | Alex (domain-expert) | `revision-audit` | Revision Log + amended upstream docs |
| 9 *(when goal reached)* | Kai (mlops-engineer) | `deployment` | Deployment Requirements + Report |

### Anytime Capabilities

| Agent | Capability | When to Use |
|-------|------------|-------------|
| Alex (domain-expert) | `advise` | Before any experiment — surfaces validated params and dead ends from past work |
| Kai (mlops-engineer) | `decisions` | During any experiment — captures know-how, rejected alternatives, and deferred questions |
| Kai (mlops-engineer) | `inference-pipeline` | After a model is accepted — adapts for production with V&V; also invoked as Phase C of Stage 9 `deployment` |

---

## Task Namespaces

Detailed Design (Stage 4) produces two task categories:

| Prefix | Executed By | Purpose |
|--------|-------------|---------|
| `INF-*` | Kai — `infra` | Infrastructure tasks — built once, reused across experiment cycles |
| `EXP-*` | Jordan — `experiment` | Experiment tasks — executed each cycle against the active TECHSPEC |
| `REV-*` | Next cycle | Generated by `revision-audit` for the following iteration |

---

## Experiment Tracking

| Tool | Best For |
|------|----------|
| [Weights & Biases](https://wandb.ai) | Teams, sweep UI, collaboration |
| [MLflow](https://mlflow.org) | Self-hosted, open-source, model registry |
| [ClearML](https://clear.ml) | Auto-capture, enterprise MLOps, HPO orchestration |

Choose one during `ai-setup configure`; wire it in `infra` (Stage 5). Stage 5 **verifies connectivity** (using `ai_tracker_url` for self-hosted servers) before the smoke test — on failure it warns, switches to the tool's offline store, records it in the Infra Log, and continues. It never hard-fails on a dead tracker; offline runs sync/import later (`wandb sync`, MLflow file store, `Task.import_offline_session`).

---

## Connecting Internal Sources & Trackers

The module wires internal knowledge systems (Jira, Confluence, SharePoint, network shares) and experiment trackers through config set at `ai-setup configure` — with two acquisition modes that produce **identical downstream artifacts**:

- **MCP-first.** `configure` auto-detects MCP servers registered in your IDE, then asks whether additional **internal servers** exist — air-gapped networks often run their own MCP mirrors/gateways, so air-gapped never automatically means "no MCP". You supply the exact server name as registered in your IDE/MCP config plus the source it serves; everything is recorded in `ai_mcp_servers`. Sources with a server are queried live (Jira JQL, Confluence space search, filesystem).
- **Export fallback.** Any source without a server uses the `imports/` drop folder (`jira/` CSV/XML exports, `confluence/` space exports, `sharepoint/` downloaded documents, `docs/` loose PDFs). `imports/` is **gitignored by default** (except its README) — exports often contain sensitive data; the Domain Knowledge Base that cites them (by file path) is the committed artifact. SharePoint is export-only for now unless your org provides an MCP server.
- **Air-gapped background folder.** In air-gapped mode, `domain-research` and `literature-review` also ask for a background folder of PDFs/reference files at **any path you name** — not only `imports/`.
- **Config keys:** `ai_internal_sources` (per-source mode + scope: Jira project keys, Confluence spaces, share paths — confirmed once per research run), `ai_mcp_servers`, `ai_tracker_url`, `ai_tracker_offline` — all under the `ai` section of `_bmad/config.yaml`. Credentials stay in env vars, never in config.
- **Tracker offline behavior:** `ai_tracker_offline: true` (or a failed Stage 5 ping) routes runs to offline stores; Stage 6/6.5 read local stores transparently and record `offline:<run-dir>` task IDs.

Full design: [docs/design/integrations.md](docs/design/integrations.md). For the consolidated offline workflow (install, internal MCP, exports, offline trackers, local LLMs), see the [air-gapped & corporate guide](docs/air-gapped.md).

---

## LLM Configuration

### Agent model

Set in your IDE — not here. Any model supported by your IDE works.

### Script-level LLM calls

Some utility scripts call an LLM directly via `scripts/llm_client.py`, configured by `configs/llm_config.yaml` (written by `ai-setup new-project`):

Two provider options are supported — pick whichever fits your setup (exactly one block active):

```yaml
# Option A — Anthropic API
provider: anthropic
model: <your-model-name>         # e.g. claude-sonnet-4-6
base_url: ~
api_key_env: ANTHROPIC_API_KEY

# Option B — OpenAI-compatible API (OpenAI, Ollama, vLLM, Azure, ...)
# provider: openai-compatible
# model: <your-model-name>       # e.g. gpt-4o, llama3.3
# base_url: http://localhost:11434/v1
# api_key_env: OPENAI_API_KEY
```

The API key lives in the env var — never in the config file.

Running a local model such as **Nemotron Super 49B** on vLLM/NIM? See ["Serving a local model" in the air-gapped guide](docs/air-gapped.md#serving-a-local-model-example-nemotron-super-49b) — launch flags, tool-parser setup, reasoning toggle, and harness pairing; `scripts/llm_config.yaml.template` ships a ready-made Nemotron block.

---

## Prompt Flavors

The capability prompts ship in two flavors, selected by the `ai_prompt_flavor` config key:

- **`standard`** (default) — the canonical prompts, written for frontier models (Claude Opus-class, GPT-5-class and better).
- **`guided`** — for mid-tier, small, or local models (e.g. served via Ollama/vLLM). Same stages, same artifacts, same review gates — with more explicit scaffolding: numbered micro-steps, literal copy-this output skeletons, enumerated closed choices, and pre-gate self-check checklists.

The flavor is a **per-user setting**: it lives in `_bmad/config.user.yaml` (gitignored), so teammates sharing one repo can each run the flavor matching their model. Mechanically, the canonical capability files never change — `guided` mode additionally loads an overlay from `<agent>/guided/<capability>.md` when one exists (currently: `ideation`, `architecture`, `techspec`, `experiment`), and falls back to the canonical file alone otherwise. Artifact names, paths, review gates, and the memory protocol are identical in both flavors.

To switch: edit `ai_prompt_flavor` in `_bmad/config.user.yaml`, or re-run `ai-setup configure` and change it there. No reinstall needed.

---

## Key Principles

- **Configure first.** Run `ai-setup configure` before invoking any agent.
- **Review gates are hard stops.** After writing or editing any document, an agent stops, summarizes what changed, and waits for your explicit approval before the next step — no automatic stage chaining.
- **Agents ask, they don't guess.** On any dilemma with meaningful alternatives (paradigm, threshold, data assumption, scope), agents present the options with a brief recommendation and let you decide.
- **Scaffold, then install.** No package installation before Ideation; Ideation only records placeholders (`uv add --no-sync`). The first real install is `uv sync` when Kai runs `infra` (Stage 5).
- **TECHSPECs are contracts.** Lock them before training starts; amend them with a new revision.
- **HPO only after baseline confirmation.** HPO on a broken architecture wastes compute.
- **Run advise before every experiment.** Alex mines the memory bank — local and imported — so you don't repeat mistakes.
- **Memory outlives documents.** Every writing stage ends with a Memory Update that distills atomic facts into the project memory bank; agents start from its compact index instead of re-reading whole documents.
- **Document decisions as you go.** Kai captures rejected alternatives and know-how in DECISIONS.md — don't lose this context.
- **Fresh context window per agent.** Each agent is specialized — mixing stages in one session degrades quality.
- **Failed attempts are mandatory.** Infra Log and Analysis documents with no failures documented are incomplete.

---

## Project Memory Bank

Each project accumulates a file-based knowledge bank, created by `ai-setup configure` and shared by all five agents:

```
{ai_output_folder}/memory/
├── index.md            # one table row per entry — the ONLY bank file loaded at agent activation
├── entries/            # one markdown file per atomic fact (bg-*, fnd-*, les-*, res-*, dec-*, evo-*)
└── imports.yaml        # optional read-only references to other projects' banks
```

Six entry types: `background`, `finding`, `lesson`, `result`, `decision`, `evolution`. How it works:

- **Read.** On activation an agent loads only `index.md`. Capabilities retrieve the few relevant entries by type/tag (each < 20 lines) and follow `[[entry-id]]` links — never whole upstream documents for background knowledge.
- **Write.** Each writing capability ends with a mandatory **Memory Update** step that distills new atomic facts into `entries/` and appends one index row each. Capabilities write only their own types (e.g. `analysis` → `lesson` + `result`; `decisions` → `decision`; `revision-audit` → `evolution`).
- **Append-only.** Entries are never edited or deleted. Only `revision-audit` marks entries superseded (`superseded_by`) and, past ~200 index rows, compacts stale rows into `index-archive.md` — the cross-cycle evolution chain is preserved.
- **Cross-project reuse.** `imports.yaml` points at previous projects' banks (read-only). `advise` searches local + imported indexes; imported facts that become load-bearing are copied into the local bank (copy-on-use).

Lifecycle documents remain the authoritative long-form record — the bank holds the distilled, reusable facts. Full design: [docs/design/memory-bank.md](docs/design/memory-bank.md).

---

## CI/CD

Two GitHub Actions workflows are included:

- **`validate_skills.yml`** — PR gate: checks SKILL.md frontmatter, manifest structure, and semver format
- **`update_marketplace.yml`** — auto-generates `marketplace.json` from all manifests on push to `main`

---

## Updating the Module

Re-run the installer with the same `--custom-source` you used during installation. BMad re-fetches from the original source and applies updates in place.

```bash
npx bmad-method install \
  --directory . \
  --modules bmm \
  --custom-source https://github.com/avielbl/ai-lifecycle \
  --tools claude-code \
  --yes
```

For offline environments, use the local path instead of the GitHub URL — see [Updating the module offline](docs/air-gapped.md#updating-the-module-offline).

---

## Versioning

- `v5.0.0` — Full-lifecycle release (stages 0–9). **Stage 9 Deployment**: joint goal-attainment gate → requirements elicitation → serving implementation with V&V. **Project Memory Bank**: shared per-project knowledge bank (`memory/index.md` + six typed atomic entry kinds with `[[entry-id]]` links), mandatory Memory Update steps across writing capabilities, `advise` rewritten as an index-first query, append-only entries with supersede/compaction owned by `revision-audit`, cross-project imports via `imports.yaml`. **Stage 1.2 Literature Review** (Maya) with cross-article comparison matrix and handoff back to the Domain KB. **EDA executed notebook**: `notebooks/eda_report.ipynb` built programmatically and executed headlessly alongside the markdown report. **Scaffold env + cloud**: `uv venv`, `git init` + optional remote (never auto-pushed), `configs/project_infra.yaml`, `docker/Dockerfile.train` templates (Vertex AI / ClearML / generic). **Integrations**: MCP-first internal sources with export/drop-folder fallback and internal air-gapped MCP support; tracker verification in Stage 5 with offline fallback. **Conventions**: hard review gates and ask-don't-guess across all agents; model-agnostic defaults (no preset model names); installer-owned setup keys never re-asked by `configure`. New docs: hands-on tutorial and air-gapped guide.
- `v4.1.0` — Renamed MLOps Developer and Experimentation Engineer personas for role clarity. Restructured experiment output into per-experiment folders with dedicated `results` and `decisions` capabilities; merged retrospective into analysis and dropped numeric prefixes. Added `package.json` for npm/registry distribution with environment-specific install examples (GitHub, Artifactory, local path). Repaired broken file references across skills. Updated docs to use BMad installer instead of git submodules.
- `v4.0.0` — Renamed from `bmad-dl-lifecycle` to `ai-lifecycle`. Module code `ai`. Broadened from deep learning to all AI/ML paradigms. Agents renamed to `ai-agent-*` with assigned personas (Alex, Sam, Maya, Kai, Jordan). `ai-setup` skill absorbs scaffold and module configuration.
- `v3.0.0` — Agent-based architecture. Five domain specialists replace per-skill approach. Memory added to Domain Expert, Researcher, Developer.
- `v2.1.0` — Scaffold (Stage 0): automated project scaffolding with uv.
- `v2.0.0` — Split infra + experiment. HPO (Stage 7.5). W&B/MLflow/ClearML integration.
- `v1.2.0` — Knowledge flywheel: advise, techspec.
- `v1.0.0` — Initial release.

---

## License

MIT
