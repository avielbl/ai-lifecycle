---
name: "ai-setup"
description: "Sets up the AI Lifecycle module in a project (configure), or scaffolds a new AI/ML project structure (new-project)."
---

# AI Lifecycle Setup

## Overview

Two capabilities:

- **`configure`** — Installs and configures the AI Lifecycle module. Writes module config to `_bmad/config.yaml` and registers capabilities in `module-help.csv`. Run this first in any project where AI Lifecycle hasn't been installed yet.
- **`new-project`** — Scaffolds a new AI/ML project from scratch: creates directory structure, IDE config, `uv` project, experiment tracker config, and LLM config. Run this when starting a brand-new project.

Config is written to:
- **`{project-root}/_bmad/config.yaml`** — shared project config (module settings, output paths, LLM config, tracker)
- **`{project-root}/_bmad/config.user.yaml`** — personal settings (gitignored: user name, communication language)
- **`{project-root}/_bmad/module-help.csv`** — capability registry for `/bmad-help`

## On Activation

Check which capability was requested:

- If the user passed `new-project` → skip to **[New Project](#new-project)**
- If the user passed `configure`, `setup`, or `install` → continue below
- If no argument: ask — "Configure the AI Lifecycle module in this project, or scaffold a new project?"

---

## Configure (Module Setup)

### Step 1: Read Module Definition

Read `./assets/module.yaml` for module metadata and variable definitions (the `code` field is the module identifier).

Check if `{project-root}/_bmad/config.yaml` exists:
- If a section matching `ai` is already present → inform the user this is an **update**
- If not → this is a **fresh install**

Check for legacy per-module configuration at `{project-root}/_bmad/ai/config.yaml` and `{project-root}/_bmad/core/config.yaml`. If either exists:
- If `{project-root}/_bmad/config.yaml` does **not** yet have an `ai` section: inform the user installer config was detected and will be consolidated.
- If it **already** has an `ai` section: inform the user legacy config was found and will be used as fallback defaults.
- In both cases, legacy files will be cleaned up after setup.

If the user provides arguments (e.g., `accept all defaults`, `--headless`, or inline values like `output folder is reports`), map them to config keys, use defaults for the rest, and skip interactive prompting. Still display the full confirmation summary at the end.

### Step 2: Collect Configuration

**Before asking anything**, read `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (if they exist). Build the question list by **skipping every question whose config key already has a value** — never re-ask a key that is already set.

Then ask the user only for the remaining values. Show defaults in brackets. Present all values together so the user can respond once with only the values they want to change. Never tell the user to "press enter" or "leave blank".

**Default priority** (highest wins): existing config values > legacy config values > `./assets/module.yaml` defaults.

**Core config** — installer-owned; never re-ask keys that have values. The BMad installer (`npx bmad-method install`) collects `user_name`, `communication_language`, `document_output_language`, and `output_folder` before this skill ever runs. If a core key already has a value, do not ask for it — display it in the Step 6 confirmation summary marked "inherited from BMad install", where the user can still override it by replying. Ask only for core keys that are missing entirely (e.g., the installer never ran): `user_name` (default: BMad), `communication_language` and `document_output_language` (default: English — ask as a single question), `output_folder` (default: `{project-root}/_bmad-output`). `user_name` and `communication_language` go to `config.user.yaml`; the rest to `config.yaml`.

**Module config** — from `./assets/module.yaml` variables:
- `ai_output_folder` — where to save lifecycle documents (default: `docs` → `{project-root}/docs`)
- `ai_llm_provider` — LLM provider for analysis scripts (anthropic / openai-compatible, default: anthropic)
- `ai_llm_model` — model name for the chosen provider (no preset default — ask the user; e.g. claude-sonnet-4-6, gpt-4o, llama3.3)
- `ai_experiment_tracker` — tracking platform (wandb / mlflow / clearml / none, default: none)
- `ai_internal_sources` — internal knowledge sources (multi-select: jira / confluence / sharepoint / network_share / none, default: none). For each selected source also collect its **scope** (Jira project keys, Confluence space keys, share mount path, SharePoint library) — stored in the map so research runs only need a per-run confirmation. Mode (`mcp` / `export`) comes from Step 2b, not from a question.
- `ai_mcp_servers` — filled by Step 2b (detection + user-supplied internal servers); never typed blind.
- `ai_tracker_url` / `ai_tracker_offline` — ask **only when `ai_experiment_tracker` is not `none`**: self-hosted server URL (blank = SaaS default) and offline forcing (auto / true / false, default: auto).

On a **fresh install**, ask all applicable module questions. On an **update**, apply the same skip-if-present logic: only ask module keys missing from the existing `ai` section; keys that already have values are skipped and shown in the confirmation summary.

### Step 2b: MCP Detection (internal sources only)

Run when `ai_internal_sources` is being collected (skip entirely when it is already set or the user selected `none`):

1. **Auto-detect** configured MCP servers, best-effort: check `{project-root}/.mcp.json`, the IDE's user-level MCP config (`~/.claude.json` or equivalent) if accessible, and — in Claude Code — the live tool list (`mcp__<server>__*` tools visible this session). Match names/tools against known patterns: `atlassian`, `jira`, `confluence`, `sharepoint`, `ms-365`, `filesystem`.
2. **Confirm findings:** "Detected MCP servers: atlassian (Jira+Confluence), filesystem. Use these for internal-source research? [Y/n]"
3. **Ask about internal servers (always, even when nothing was detected):** "Are there additional or internal MCP servers I can't see — e.g. internal mirrors/gateways on an air-gapped network?" Air-gapped ≠ no MCP. For each one the user names, record the **exact server name as registered in the IDE/MCP config** and **which source it serves** — never guess or normalize the name.
4. **Record:** write the source→server map to `ai_mcp_servers`; for each source with a server set `mode: mcp` (+ `server:`) in `ai_internal_sources`, otherwise `mode: export`. SharePoint defaults to `export` unless the org supplied a server. For a mounted network share, prefer `mode: export` with the mount path as scope — native file tools beat MCP there.
5. **Headless:** accept detection as-is; undetected sources default to `export`; no internal-server question.

**Memory import (optional, fresh install only):** also ask — "Import memory from a previous project? (path to its `memory/` folder, or none)" [default: none]. This is not a config key; the answer seeds `imports.yaml` in Step 4. In headless mode, default to none.

**Net effect:** a project that just ran the BMad installer answers at most the 4 module questions plus the optional memory-import prompt — no core questions are repeated.

**Post-configure note:** If `ai_experiment_tracker` is not `none`, remind the user that the tracker SDK is installed in Stage 5 (infra) via `uv sync` — no action needed now. If any internal source ended up in export mode, print a short export summary: the `imports/` layout (`jira/` CSV/XML Issue-Navigator exports, `confluence/` space exports or page PDFs, `sharepoint/` downloaded documents, `docs/` loose PDFs), a note that `imports/` is gitignored, and that an optional `imports/MANIFEST.md` can describe what each export contains.

### Step 3: Write Files

Write a temp JSON file with collected answers as `{"core": {...}, "module": {...}}` (omit `core` if already exists). Run both scripts in parallel:

```bash
uv run ./scripts/merge-config.py --config-path "{project-root}/_bmad/config.yaml" --user-config-path "{project-root}/_bmad/config.user.yaml" --module-yaml ./assets/module.yaml --answers {temp-file} --legacy-dir "{project-root}/_bmad"
uv run ./scripts/merge-help-csv.py --target "{project-root}/_bmad/module-help.csv" --source ./assets/module-help.csv --legacy-dir "{project-root}/_bmad" --module-code ai
```

Both scripts output JSON to stdout. If either exits non-zero, surface the error and stop. Check `legacy_configs_deleted` and `legacy_csvs_deleted` in the output.

### Step 4: Create Output Directories

After writing config, resolve `{project-root}` to the actual project root and create each path-type config value that does not yet exist (including `ai_output_folder` and its subfolders from `./assets/module.yaml` `directories`). Use `mkdir -p`. Paths in config files keep the literal `{project-root}` token.

**Exception — `imports/` entries:** create `{project-root}/imports/` and only the per-source subfolders whose `ai_internal_sources` mode is `export` (skip all of them when no source is in export mode). When creating `imports/`, ensure the project `.gitignore` ignores it (append `imports/*` + `!imports/README.md` if missing) — exports often contain sensitive internal data.

**Seed the memory bank** (never overwrite an existing file):

- `{ai_output_folder}/memory/index.md` — header row only:

  ```markdown
  | id | type | stage | exp | tags | hook |
  |----|------|-------|-----|------|------|
  ```

- `{ai_output_folder}/memory/imports.yaml` — template listing read-only external banks. If the user gave a path at the Step 2 memory-import prompt, add it as the first entry (ask for a short `name` and `note`); otherwise leave the list empty:

  ```yaml
  # Read-only references to other projects' memory banks (never written to).
  # imports:
  #   - name: fraud-v1
  #     path: /path/to/fraud-v1/docs/memory   # absolute or relative; local mount is fine air-gapped
  #     note: same data source, prior paradigm was XGBoost
  imports: []
  ```

### Step 5: Cleanup Legacy Directories

```bash
uv run ./scripts/cleanup-legacy.py --bmad-dir "{project-root}/_bmad" --module-code ai --also-remove _config --skills-dir "{project-root}/.claude/skills"
```

The script verifies every skill exists at `.claude/skills/` before removing. Missing directories are not errors. Check `directories_removed` and `files_removed_count`.

### Step 6: Confirm

Display what was written: config values, user settings, help entries added, memory bank files seeded (or skipped, if present), fresh install vs update, any legacy cleanup. Core values that were skipped in Step 2 must appear here marked "inherited from BMad install" — if the user replies with a change, update the config accordingly. Then show the `module_greeting` from `./assets/module.yaml`.

Once `user_name` and `communication_language` are known, use them for the rest of the session.

> **Note:** BMad core runs `resolve_config.py` on every agent activation to merge these config layers at runtime (see "Why agents run resolve_config on activation" in the README). Agents inherit that resolved config — capabilities should NOT re-read the `_bmad` config files if the agent already resolved them this session.

---

## New Project

Scaffolds a complete AI/ML project directory structure. Run from or targeting an empty directory.

### Step 1: Collect Project Details

Ask the user (present all at once):

- **Project name** — used as the Python package name (underscores, no spaces). Default: current directory name.
- **Project directory** — where to create the project. Default: current working directory.
- **IDE** — `claude-code` (slash commands), `cline`, `cursor`, or `antigravity`. Default: `claude-code`.
- **Python version** — Default: `3.11`.
- **Experiment tracker** — `wandb`, `mlflow`, `clearml`, or `undecided` (can change at Architecture stage). Default: `undecided`.
- **Data location** — `local`, `s3`, `gcs`, `azure-blob`, or `nfs`, plus an optional URI/path. Default: `local`.
- **Artifact registry** — `tracker-native`, `s3`, `gcs`, or `local`, plus an optional URI. Default: `tracker-native` if a tracker was chosen, else `local`.
- **Compute topology** — `same-machine`, `remote-gpu`, or `cloud-managed`. Default: `same-machine`. If `cloud-managed`, also ask the service: `vertex-ai`, `clearml`, or `generic`.
- **Git remote** — remote URL for `origin`, or `none`. Default: `none`. Never pushed automatically.

If the user passed arguments inline (e.g., `new-project my-fraud-detector --ide claude-code`), map them and skip the questions.

### Step 2: Create Directory and Run Scaffold

Locate `init_project.py` — it lives at `{skill-install-path}/scripts/init_project.py` (the `scripts/` folder inside the ai-lifecycle module install directory, e.g. `.claude/skills/ai-lifecycle/scripts/init_project.py` or the source repo path).

```bash
mkdir -p "{project_dir}"
cd "{project_dir}" && uv run "{init_project_path}" --ide {ide} --tracker {tracker} --python-version {python_version} --data-location {data_location} --artifact-registry {artifact_registry} --compute {compute} --git-remote {git_remote_url_or_none} --yes 2>&1
```

Append `--compute-service {vertex-ai|clearml|generic}` when compute is `cloud-managed`, and `--data-uri` / `--artifact-uri` when the user gave URIs. (`--yes` defaults any omitted flag; the script also still supports the legacy interactive stdin flow.)

The script creates:
- Full directory structure (`data/`, `src/`, `notebooks/`, `configs/`, `docs/`, `models/`, `outputs/`)
- `.clinerules` or `CLAUDE.md` with agent skill paths (based on IDE)
- `pyproject.toml` and `.python-version` (uv project)
- An empty `.venv` via `uv venv` — no packages installed
- A git repository on `main` (`git init -b main`) with the scaffold committed; `origin` registered if a remote URL was given (never pushed — the push command is printed as a next step)
- `.gitignore`
- `configs/llm_config.yaml` (from template using configured LLM provider/model)
- `configs/project_infra.yaml` — data location, artifact registry, compute topology (read by TECHSPEC Stage 4.5 and infra Stage 5)
- `docker/Dockerfile.train` + `docker/README.md` — dockerized training templates (image built at Stage 5+, not now)
- Copies skills to `.claude/skills/` if `ide=claude-code`

**No premature installs:** the scaffold installs **no packages** — `pyproject.toml` starts with no dependencies. Do not run `uv sync`, `uv add`, `pip install`, or equivalent here. Dependencies are recorded as placeholders in Ideation (Stage 1.5, `uv add --no-sync`) and first installed in Stage 5 (`infra`) via `uv sync`.

### Step 3: Confirm and Hand Off

Report what was created — including the venv, git init and remote status (with the `git push -u origin main` command if a remote was set), `configs/project_infra.yaml`, and the `docker/` templates. Then:

> "Your project is scaffolded at `{project_dir}`. Next: run `/ai-agent-domain-expert` and activate `domain-research` to start Stage 1."

If the module hasn't been configured yet (`{project-root}/_bmad/config.yaml` has no `ai` section), offer to run **configure** now:

> "I notice AI Lifecycle hasn't been configured in this project yet. Run `configure` now to set up the output folder, LLM provider, and experiment tracker before starting Stage 1?"
