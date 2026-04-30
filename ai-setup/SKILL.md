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

Ask the user for values. Show defaults in brackets. Present all values together so the user can respond once with only the values they want to change. Never tell the user to "press enter" or "leave blank".

**Default priority** (highest wins): existing config values > legacy config values > `./assets/module.yaml` defaults.

**Core config** (only if no core keys exist yet): `user_name` (default: BMad), `communication_language` and `document_output_language` (default: English — ask as a single question), `output_folder` (default: `{project-root}/_bmad-output`). `user_name` and `communication_language` go to `config.user.yaml`; the rest to `config.yaml`.

**Module config** — from `./assets/module.yaml` variables:
- `ai_output_folder` — where to save lifecycle documents (default: `docs` → `{project-root}/docs`)
- `ai_llm_provider` — LLM provider for analysis scripts (anthropic / openai-compatible, default: anthropic)
- `ai_llm_model` — default model name (default: claude-sonnet-4-6)
- `ai_experiment_tracker` — tracking platform (wandb / mlflow / clearml / none, default: none)

**Post-configure note:** If `ai_experiment_tracker` is not `none`, remind the user that the tracker SDK is installed in Stage 5 (infra) via `uv sync` — no action needed now.

### Step 3: Write Files

Write a temp JSON file with collected answers as `{"core": {...}, "module": {...}}` (omit `core` if already exists). Run both scripts in parallel:

```bash
python3 ./scripts/merge-config.py --config-path "{project-root}/_bmad/config.yaml" --user-config-path "{project-root}/_bmad/config.user.yaml" --module-yaml ./assets/module.yaml --answers {temp-file} --legacy-dir "{project-root}/_bmad"
python3 ./scripts/merge-help-csv.py --target "{project-root}/_bmad/module-help.csv" --source ./assets/module-help.csv --legacy-dir "{project-root}/_bmad" --module-code ai
```

Both scripts output JSON to stdout. If either exits non-zero, surface the error and stop. Check `legacy_configs_deleted` and `legacy_csvs_deleted` in the output.

### Step 4: Create Output Directories

After writing config, resolve `{project-root}` to the actual project root and create each path-type config value that does not yet exist (including `ai_output_folder` and its subfolders from `./assets/module.yaml` `directories`). Use `mkdir -p`. Paths in config files keep the literal `{project-root}` token.

### Step 5: Cleanup Legacy Directories

```bash
python3 ./scripts/cleanup-legacy.py --bmad-dir "{project-root}/_bmad" --module-code ai --also-remove _config --skills-dir "{project-root}/.claude/skills"
```

The script verifies every skill exists at `.claude/skills/` before removing. Missing directories are not errors. Check `directories_removed` and `files_removed_count`.

### Step 6: Confirm

Display what was written: config values, user settings, help entries added, fresh install vs update, any legacy cleanup. Then show the `module_greeting` from `./assets/module.yaml`.

Once `user_name` and `communication_language` are known, use them for the rest of the session.

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

If the user passed arguments inline (e.g., `new-project my-fraud-detector --ide claude-code`), map them and skip the questions.

### Step 2: Create Directory and Run Scaffold

Locate `init_project.py` — it lives at `{skill-install-path}/scripts/init_project.py` (the `scripts/` folder inside the ai-lifecycle module install directory, e.g. `.claude/skills/ai-lifecycle/scripts/init_project.py` or the source repo path).

```bash
mkdir -p "{project_dir}"
cd "{project_dir}" && printf "{ide}\n{tracking_tool}\n{python_version}\nyes\n" | python3 "{init_project_path}" 2>&1
```

The script creates:
- Full directory structure (`data/`, `src/`, `notebooks/`, `configs/`, `docs/`, `models/`, `outputs/`)
- `.clinerules` or `CLAUDE.md` with agent skill paths (based on IDE)
- `pyproject.toml` and `.python-version` (uv project)
- `.gitignore`
- `configs/llm_config.yaml` (from template using configured LLM provider/model)
- Copies skills to `.claude/skills/` if `ide=claude-code`

### Step 3: Confirm and Hand Off

Report what was created. Then:

> "Your project is scaffolded at `{project_dir}`. Next: run `/ai-agent-domain-expert` and activate `domain-research` to start Stage 1."

If the module hasn't been configured yet (`{project-root}/_bmad/config.yaml` has no `ai` section), offer to run **configure** now:

> "I notice AI Lifecycle hasn't been configured in this project yet. Run `configure` now to set up the output folder, LLM provider, and experiment tracker before starting Stage 1?"
