# Design: Prompt Flavors for Other Harnesses and Models

**Status:** Proposed — pending user decisions (§8)

## 1. Problem

All preliminary testing of this module ran on **Claude Code with SOTA models (Opus 4.8 and better)**. The capability prompts are written for that profile: terse operating instructions, open-ended judgment ("present options with a recommendation"), multi-step files the agent is trusted to sequence itself, and free-form output templates described rather than spelled out.

Two portability axes are untested:

- **Harness** — Cline, Cursor, Antigravity, and future IDEs differ in invocation (no slash commands), tool availability (web search, MCP, shell), and context handling.
- **Model capability** — mid-tier and small models (including local/air-gapped models served via Ollama/vLLM) need more explicit scaffolding: literal output skeletons, enumerated choices instead of open-ended dilemmas, per-step self-checks, and narrower per-session scope.

The user asked: can different prompt flavors coexist, selected by user preference **at BMad installation time**?

## 2. What already exists

| Layer | Mechanism | Status |
|---|---|---|
| Install-time questions | `module.yaml` `variables` are collected by the BMad installer and by `ai-setup configure`, stored in `_bmad/config.yaml` / `config.user.yaml`, re-read as defaults on update | shipped |
| Harness invocation glue | `init_project.py` writes `CLAUDE.md` (claude-code) or `.clinerules` (cline/cursor/antigravity); README documents per-IDE invocation | shipped (v2.1+) |
| Tool-availability fallbacks | MCP-first with export/drop-folder fallback (integrations, v5.0.0); web vs air-gapped modes in research capabilities; script LLM calls are provider-agnostic | shipped (v5.0.0) |
| BMad core precedent | `customize.toml` overlays per agent: scalar overrides + append-only prompt arrays, merged at activation | core feature — validates the overlay pattern |

## 3. Axis 1 — Harness: no prompt flavors needed

Harness differences are **mechanical, not semantic**: how skills are invoked and which tools exist. The prompt content does not need to change per harness — and after v5.0.0's integrations work, tool-availability differences already degrade gracefully (no MCP → export mode; no web → air-gapped mode).

### Harness profiles

| Harness | Invocation | Rules file | MCP | Custom/local models | Glue the module must provide |
|---|---|---|---|---|---|
| Claude Code | `/skill` slash commands | `CLAUDE.md` | yes | Anthropic models | shipped |
| Antigravity | slash commands (auto-discovered) | — | yes | bundled models | shipped |
| Cline / Cursor | paste skill path | `.clinerules` | yes | custom OpenAI-compatible endpoints | shipped |
| **opencode** | native **agent skills** (SKILL.md convention) + custom commands (`.opencode/command/*.md`) | `AGENTS.md` | yes (`opencode.json`) | any provider — ollama, openrouter, azure, **any OpenAI-compatible endpoint** (best on-prem fit) | new `--ide opencode` in `init_project.py`: write `AGENTS.md` with skill paths; copy/link skills where opencode discovers them; optional per-agent custom commands |
| **VS Code Copilot (native agent mode)** | `.prompt.md` files invoked via `/name` in chat; `.chatmode.md` custom personas with tool sets | `.github/copilot-instructions.md` (always-on) + scoped `.instructions.md` | yes (GA since VS Code 1.102) | BYOK — official Ollama extension for local models; **agent mode hides models without tool-calling support**; BYOK availability varies by Copilot plan | new `--ide copilot` in `init_project.py`: write `.github/copilot-instructions.md` with skill paths + `.github/prompts/ai-agent-*.prompt.md` wrappers (restores slash-command UX); optionally one `.chatmode.md` per agent persona |

opencode is the strongest air-gapped/on-prem pairing: it natively consumes the same SKILL.md convention this module already ships, and points at any OpenAI-compatible endpoint (vLLM/NIM). Copilot agent mode is viable but has two caveats to document: local models must support tool calling to appear in agent mode at all, and BYOK is plan-dependent in enterprise setups.

**Adjustments (small, no flavor mechanism):**

1. **Harness compatibility audit** — one pass over all capability files for Claude-Code-specific assumptions (e.g., subagent references, tool names). Replace with neutral phrasing ("search the web" not "use WebSearch").
2. **Compatibility matrix in README** — the table above, user-facing. Extends the existing "Invoking Agents" section.
3. **Degradation note in each SKILL.md On Activation** — one line: "If a required tool (shell, web, MCP) is unavailable in this environment, tell the user what is missing and offer the manual alternative rather than skipping the step."
4. **`init_project.py`**: add `opencode` and `copilot` IDE options with the glue files from the table.

**Recommendation:** do NOT key prompt flavors on harness. One config key fewer; the capability files stay harness-neutral by rule. Harness support = glue files only.

## 4. Axis 2 — Model capability: two flavors

### Flavors

- **`standard`** (default) — the current prompts, written for frontier models (Opus 4.8+, comparable SOTA).
- **`guided`** — for mid-tier / small / local models. Same stages, same artifacts, same gates — more scaffolding.

What `guided` adds (overlay content guidelines):

| Standard behavior | Guided overlay behavior |
|---|---|
| "Present options with a brief recommendation" | Enumerated closed lists: "Choose exactly one of: (a)…, (b)…, (c)…. If unsure, pick (a)." |
| Output template described in prose | Literal copy-this markdown skeleton with every section header and placeholder pre-written |
| Agent sequences multi-step file itself | Numbered micro-steps with "do not continue until step N output exists" |
| Review gate = stop and summarize | Gate preceded by an explicit self-check checklist ("[ ] every PRD requirement has an ID; [ ] every tier has a numeric threshold; …") |
| One session may span related work | Hard rule: one capability per session; write the memory index row, then stop |
| Trusted to infer file paths from config | Full literal paths repeated at point of use |

What must **never** differ between flavors (contract invariants):
- Artifact names, locations, and section structure (downstream stages read them).
- Review gates, ask-don't-guess, no-premature-install rules.
- Memory bank protocol (entry types, index format, write ownership).
- CSV/manifest registration — flavors are invisible to `/bmad-help`.

### Mechanism options

| | A. Duplicate prompt sets (`prompts/standard/`, `prompts/guided/`) | B. Shared core + guided overlay (recommended) | C. One file with conditional sections |
|---|---|---|---|
| Source of truth | 2 copies of every file — drift risk across 17 capabilities | Core file stays canonical; overlay is additive | single file |
| Context cost | none extra | small (overlay loads only in guided mode) | every model reads both flavors' text |
| Weak-model suitability | good | good (overlay is explicit by construction) | poor — small models follow the wrong branch |
| Maintenance | every change made twice | change core once; overlay only when scaffolding needs it | conditionals metastasize |
| Missing-flavor fallback | must exist for all files | absent overlay ⇒ standard silently | n/a |

**Recommendation: B.** Each capability keeps its canonical file; guided scaffolding lives in `<agent>/guided/<capability>.md`. An absent overlay means the standard prompt is used as-is — so overlays can be rolled out incrementally, highest-leverage capabilities first.

### Loading mechanism

- New `module.yaml` variable:
  ```yaml
  - key: ai_prompt_flavor
    prompt: Prompt flavor for the agent team?
    type: single-select
    options:
      - value: standard
        label: Standard — frontier models (Claude Opus-class, GPT-5-class and better)
      - value: guided
        label: Guided — mid-tier, small, or local models (more explicit step-by-step scaffolding)
    default: standard
    user_setting: true   # see §8 decision 3
  ```
  Because it is a `module.yaml` variable, **the BMad installer asks it during installation** (the user's requirement) and `ai-setup configure` asks/skips it with the existing dedup logic. Changing it later = edit config; no reinstall.
- Each SKILL.md "On Activation / Capabilities" section gains one rule:
  > When loading a capability file, check `ai_prompt_flavor` (already resolved at activation). If `guided`, also load `guided/<capability>.md` from this skill folder and follow its scaffolding **in addition to** the capability file; where they conflict, the guided file wins. If no guided file exists, proceed with the capability file alone.
- Both flavors ship in every install (the installer copies whole skill folders); selection is runtime, per the flavor key. This also lets **mixed teams** work in one repo — flavor as a user setting means each collaborator's model tier gets matching prompts.

### Rollout & validation

1. **Wave 1 overlays (4 files):** `ideation`, `architecture`, `techspec`, `experiment` — the capabilities where unguided judgment does the most damage.
2. **Evaluate before writing wave 2:** run the `docs/tutorial.md` fraud-detection scenario end-to-end on a target mid-tier model (e.g., a Sonnet-class or strong local model) in guided mode; log where the model deviates from the artifact contract; write wave-2 overlays (`eda`, `detailed-design`, `analysis`, `deployment`, remaining) against observed failures, not guesses.
3. BMad Builder ships evaluation utilities — worth adopting for a repeatable flavor regression check once waves stabilize.

### How flavors are implemented — concrete walkthrough

A "flavor" is **not** a separate copy of the module. It is one config value plus optional overlay files:

1. **One config key.** `ai_prompt_flavor: standard | guided` — asked once during BMad installation (module.yaml variable), stored in config, changeable any time by editing config or re-running `ai-setup configure`.
2. **One overlay folder per non-standard flavor.** The canonical capability files never move or fork. A flavor adds a subfolder: `ai-agent-researcher/guided/architecture.md`, `ai-agent-domain-expert/guided/ideation.md`, … Overlays contain ONLY the extra scaffolding (output skeletons, enumerated choices, checklists) — not a rewrite.
3. **One loading rule** in each SKILL.md: *"Load `<capability>.md`. If `ai_prompt_flavor` is `guided` and `guided/<capability>.md` exists, load it too; where they conflict, the guided file wins."*
4. **Everything ships together.** The installer always copies the whole skill folder, so every install contains all flavors; the config value decides which text the agent actually reads at runtime. Two users on the same repo can run different flavors (per-user key).

Example: a user on Nemotron Super sets `ai_prompt_flavor: guided`. When Maya runs `architecture`, she loads `architecture.md` (canonical, ~30 lines) **plus** `guided/architecture.md` (~40 lines: a literal Architecture.md skeleton to fill in, a closed paradigm-choice list, a pre-gate checklist). A teammate on Opus in the same repo, with `standard` in their own `config.user.yaml`, loads only the canonical file.

**"Flavor count" decision restated:** the recommendation is to ship exactly these two named profiles. A third (`minimal`, for very small models ≤ ~14B) would just be a second overlay folder (`minimal/`) with even tighter scaffolding — mechanically trivial to add later, but every flavor multiplies prompt-maintenance and testing surface. So: don't create it speculatively; create it only if guided-mode evaluation on small models shows they still break the artifact contract.

## 4b. Case study: Nemotron Super 49B (v1.5)

Target profile for on-prem/air-gapped use. What's known: derivative of Llama-3.3-70B, post-trained specifically for reasoning, tool calling, RAG, and instruction following; 128K context; single-GPU-class serving; **reasoning toggle** — reasoning ON by default, disabled via `/no_think` (or "detailed thinking off") in the system prompt; vLLM ≥ 0.9.2 with the model repo's tool parser for function calling; also served via NIM (OpenAI-compatible either way).

Required modifications to run this module on it:

| Area | Modification | Where |
|---|---|---|
| Prompt flavor | `ai_prompt_flavor: guided` as the recommended starting point. Nemotron's agentic post-training may let mechanical stages run fine on `standard` — the wave-1 evaluation (§rollout) should run on exactly this model and prune overlays that prove unnecessary | config |
| Serving | vLLM ≥ 0.9.2 + the repo's tool parser (function calling), or NIM. Document the launch flags | `docs/air-gapped.md` |
| Script LLM calls | already works: `provider: openai-compatible`, `base_url: http://<vllm-host>/v1` — add a Nemotron example block | `scripts/llm_config.yaml.template`, README |
| Reasoning toggle | guidance doc: reasoning ON (default) for judgment-heavy capabilities (ideation, architecture, techspec, analysis, deployment Phase A); `/no_think` for mechanical ones (results collection, memory updates, scaffolding) to cut latency/tokens. The system prompt is harness-controlled, so this lands in docs + a one-line note in guided overlays ("if your model has a reasoning toggle, enable it for this capability") | docs + overlays |
| Harness pairing | recommend opencode (native SKILL.md + any OpenAI-compatible endpoint) or Cline/Cursor with custom base URL; Copilot agent mode only if the served model's tool calling is exposed through the BYOK provider | README matrix |
| Context budget | 128K is sufficient given index-first memory retrieval and guided mode's one-capability-per-session rule — no changes needed; noted as a validated assumption to re-check in evaluation | — |

## 5. Skill-file change list

| File | Change |
|---|---|
| `ai-setup/assets/module.yaml` | add `ai_prompt_flavor` variable |
| `scripts/init_project.py` | add `opencode` and `copilot` IDE options (AGENTS.md / copilot-instructions.md + prompt-file wrappers) |
| `scripts/llm_config.yaml.template` | Nemotron-on-vLLM example block |
| `docs/air-gapped.md` | Nemotron/vLLM serving section (tool parser, reasoning toggle) |
| `ai-setup/SKILL.md` | Step 2 module keys += flavor (dedup logic applies); confirmation summary shows it |
| all 5 agent `SKILL.md` | flavor-resolution rule in capability-loading section; harness degradation line (§3.3) |
| `<agent>/guided/*.md` | wave-1 overlays: ideation, architecture, techspec, experiment |
| all capability files | harness-neutrality audit pass (§3.1) |
| `README.md` | flavor section + harness compatibility matrix; version log |
| `docs/tutorial.md` | one note: guided flavor exists, where to switch |
| `.github/workflows/validate_skills.yml` | accept `guided/` subfolders (verify globs don't misfire) |

## 6. Open decisions

1. **Flavor set** — two (`standard`/`guided`) vs three (+`minimal` for very small models). **Recommend two**; a third tier only if guided-mode evaluation shows a cliff.
2. **Wave-1 overlay scope** — the 4 proposed vs all 17 upfront. **Recommend 4 + evaluate**: overlays written against observed failures beat speculative ones, and absent overlays fall back safely.
3. **Where the flavor key lives** — `config.user.yaml` (per-user, gitignored — mixed teams supported) vs shared `config.yaml` (uniform behavior, reproducible runs). **Recommend per-user** (`user_setting: true`); a team that wants uniformity can still commit a team default in shared config.
4. **Guided-mode memory bank** — full protocol vs reduced (read index, write via fill-in template only). **Recommend full protocol but overlay provides a literal entry template** — the protocol is already file-based and mechanical.
