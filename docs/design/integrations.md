# Design: Internal Data Sources and MLOps Tool Integration

> Status: **Draft — pending user decisions (§7)**
> Scope: design only. Implementation lands in Sprint 3 per the change list in §6.

---

## 1. Problem Statement

The module *names* integrations but never *wires* them:

- **Internal sources.** `domain-research.md` (Phase 1/2) and `ai-agent-domain-expert/SKILL.md` tell Alex to consult Jira, Confluence, network folders, and PDF docs — but define no connection mechanism. There is no config recording which sources exist, no instruction on *how* to query them (API? export? MCP?), and no convention for where exported material lives. In practice the agent falls back to asking the user to paste content.
- **MLOps trackers.** `ai_experiment_tracker` is a config-only variable (`module.yaml`). Stage 5 (`infra.md`) says "implement logging" with no verification step; Stage 6/6.5 (`experiment.md`, `results.md`) assume the tracker is reachable and name it ad hoc ("ClearML/WandB/MLflow"). Nothing checks connectivity, handles self-hosted URLs, or defines an offline path for air-gapped environments.

This design closes both gaps with two integration modes that produce **identical downstream artifacts**, so the lifecycle stages never need to know which mode is active.

---

## 2. Two Integration Modes

### 2.1 Mode 1: MCP-Based (Connected Environments)

MCP servers give agents live, queryable access to internal systems. The module does not bundle MCP servers — it **detects** what the user's IDE has configured, **records** it in config, and **instructs** capabilities to use it.

**Recommended servers per source:**

| Source | MCP server | Notes |
|--------|-----------|-------|
| Jira + Confluence | Atlassian Remote MCP Server (`https://mcp.atlassian.com/v1/sse`) or `sooperset/mcp-atlassian` (self-hosted, supports Server/Data Center) | Self-hosted variant is the realistic option for corporate DC installs |
| SharePoint | Microsoft 365 MCP (e.g. `softeria/ms-365-mcp-server`) via Microsoft Graph, or the Graph API directly via Bash + `az`/PAT | No single canonical server yet — record whichever the org provides |
| Network folders / PDF shares | Filesystem MCP (`@modelcontextprotocol/server-filesystem`) rooted at the mounted share, **or no MCP at all** — if the share is mounted (SMB/NFS), native `Read`/`Glob`/`Grep` suffice | Prefer native tools when a mount path exists; MCP only for unmounted/remote shares |

**Detection and recording (ai-setup configure, new Step 2b):**

1. Enumerate configured MCP servers: check `.mcp.json` (project), `~/.claude.json` / IDE equivalent, and — in Claude Code — the live tool list (`mcp__<server>__*` tools visible in session).
2. Match server names/tools against known patterns (`atlassian`, `jira`, `confluence`, `sharepoint`, `ms-365`, `filesystem`).
3. Present findings: "Detected MCP servers: atlassian (Jira+Confluence), filesystem. Use these for internal-source research? [Y/n]"
4. Record results in `ai_mcp_servers` and set `ai_internal_sources` mode per source (see §3). Detection is best-effort — the user can always override.

**How capabilities use it:** `domain-research.md` Phase 2 Mode B gains explicit per-source instructions, e.g.:

> If `ai_internal_sources.jira.mode: mcp` — use the recorded server's search tool (JQL) to pull issues matching the domain keywords; prioritize post-mortems, bugs with `resolution=Won't Fix`, and epics in the relevant project keys listed in `ai_internal_sources.jira.scope`.

`advise.md` gains a parallel Phase 2 step: when Jira is available, search for tickets referencing past experiment IDs or model names before concluding "no prior work exists."

### 2.2 Mode 2: File-Export Fallback (Air-Gapped / Corporate)

When no MCP server is available (or per-source mode is `export`), the user drops exports into a conventional folder. **This is not a degraded mode** — the research workflow, prompts, and output artifacts are identical; only Phase 2 acquisition differs.

**Drop-folder convention — `{project-root}/imports/`:**

```
imports/
  jira/          # CSV or XML exports (Issue Navigator → Export); one file per JQL query
  confluence/    # Space exports (HTML or XML zip, unzipped) or individual page PDFs
  sharepoint/    # Downloaded documents (PDF/DOCX/XLSX), preserving library folder structure
  docs/          # Loose PDFs, specs, datasheets from network shares
  MANIFEST.md    # Optional: user-written notes on what each export contains and when it was pulled
```

- Added to `module.yaml` `directories` so `ai-setup configure` creates it; `new-project` adds `imports/` to `.gitignore` (exports often contain sensitive data).
- **Consumption (`domain-research.md` Phase 2 Mode B, rewritten):** inventory `imports/` first (`find`, file counts, date stamps); parse Jira CSVs with `grep`/Python for status, resolution, and description columns; treat unzipped Confluence HTML exports as a local wiki (grep titles, then read pages); read PDFs directly (agents read PDFs natively). If `imports/` is empty and no MCP source is configured, print the export instructions above and pause — do not silently proceed with web-only research.
- Every Domain Knowledge Base claim sourced from an export cites the file path (`imports/jira/postmortems-2025.csv`, row/issue key), keeping traceability parity with MCP mode (which cites issue URLs/IDs).

**Air-gapped note:** exports are produced on the connected corporate network and carried across; the drop folder is deliberately dumb (plain files, no index, no daemon) so any transfer mechanism works.

---

## 3. Config Surface

New variables in `ai-setup/assets/module.yaml`:

```yaml
  - key: ai_internal_sources
    prompt: Which internal knowledge sources exist for this project? (multi-select)
    type: multi-select
    options: [jira, confluence, sharepoint, network_share, none]
    default: none
    user_setting: false
    # Written as a map; per selected source, configure adds:
    #   mode: mcp | export        (auto-detected, user-confirmable)
    #   scope: free text           (e.g. Jira project keys, Confluence space keys, share mount path)

  - key: ai_mcp_servers
    prompt: (auto-detected — confirm) MCP servers available for internal sources?
    default: auto
    user_setting: false
    # Stored as a map: {atlassian: mcp__atlassian, filesystem: mcp__filesystem, ...}
    # Value "none" means all sources fall back to export mode.

  - key: ai_tracker_url
    prompt: Tracker server URL? (self-hosted MLflow/ClearML/W&B; blank = SaaS default)
    default: ""
    user_setting: false

  - key: ai_tracker_offline
    prompt: Force tracker offline mode? (air-gapped or no server yet)
    type: single-select
    options: [auto, "true", "false"]
    default: auto
    user_setting: false
```

**Configure-flow changes (`ai-setup/SKILL.md`):**

- **Step 2** adds the four variables above to the interactive prompt batch. Ask `ai_tracker_url`/`ai_tracker_offline` only when `ai_experiment_tracker != none`; ask per-source `mode`/`scope` only for selected sources.
- **New Step 2b (MCP detection):** run the detection procedure from §2.1 before prompting, so prompts show detected values as defaults. In `--headless` mode, detection result is accepted as-is; undetected sources default to `export`.
- **Step 4** creates `{project-root}/imports/` and subfolders for every source whose mode is `export`.
- **Post-configure note** extends: if any source is in export mode, print the export instructions summary and the `imports/` layout.

---

## 4. MLOps Tracker Verification

### 4.1 Stage 5 (`infra.md`) — new "Tracker Verification" step

Insert between **Provision** and **Validation**:

1. Read `ai_experiment_tracker`, `ai_tracker_url`, `ai_tracker_offline` from `_bmad/config.yaml`. If tracker is `none`, log "tracking: local files only" in the Infra Log and skip.
2. **Connectivity ping** (one-liner per tool, run via `uv run python -c ...`):
   - **W&B:** `wandb.login(timeout=10)` then `wandb.Api().viewer` — verifies `WANDB_API_KEY` and host (`WANDB_BASE_URL` for self-hosted).
   - **MLflow:** `mlflow.MlflowClient(tracking_uri=...).search_experiments(max_results=1)` — verifies URI and auth.
   - **ClearML:** `Task.get_projects()` after `clearml.conf`/env check — verifies api/web/files server triplet.
3. **On success:** record tracker, resolved URL, and project/workspace name in the Infra Log; create the project/experiment container if missing.
4. **On failure or `ai_tracker_offline: true`:** fall back to **offline mode** and record it prominently in the Infra Log:
   - W&B → `WANDB_MODE=offline` (sync later with `wandb sync`)
   - MLflow → `tracking_uri: file:./mlruns` (local store; point at server later)
   - ClearML → `Task.set_offline(True)` (import later with `Task.import_offline_session`)
   Never let a dead tracker block Stage 5 — offline artifacts are always recoverable.
5. Credentials live in env vars (`WANDB_API_KEY`, `MLFLOW_TRACKING_TOKEN`, `CLEARML_API_*`) — never in config files, matching the existing `llm_config.yaml` rule.

### 4.2 Downstream references

- **`experiment.md` Step 2** changes from "ensure tracking tools are initialized" to: read tracker mode from the Infra Log; in offline mode, record the local run directory *as* the tracker task ID (`offline:./mlruns/<run_id>`), preserving the per-arm table schema.
- **`results.md` Step 1** changes from "pull metrics from tracking tool (ClearML/WandB/MLflow)" to: pull from the configured tracker via its API **or**, in offline mode, from the local run store — the RESULTS document format is identical either way.
- **`architecture.md` Step 3** ("Choose and configure wandb/mlflow/clearml") adds: if `ai_experiment_tracker` is already set in config, treat it as the default and only revisit with user consent; write back any change via `ai-setup configure`.

---

## 5. Skill-File Change List (Sprint 3 implementation spec)

| # | File | Change |
|---|------|--------|
| 1 | `ai-setup/assets/module.yaml` | Add `ai_internal_sources`, `ai_mcp_servers`, `ai_tracker_url`, `ai_tracker_offline` variables (§3); add `imports/` + per-source subfolders to `directories` |
| 2 | `ai-setup/SKILL.md` | Step 2: new prompts (conditional); new Step 2b MCP detection; Step 4: create `imports/` tree; extend post-configure note with export instructions |
| 3 | `ai-setup/scripts/merge-config.py` | Support map-valued module variables (`ai_internal_sources`, `ai_mcp_servers`) |
| 4 | `ai-agent-domain-expert/domain-research.md` | Phase 1: replace open-ended source question with config read + confirmation; Phase 2 Mode B: split into "B1: MCP query" (per-source instructions, §2.1) and "B2: imports/ consumption" (inventory, parse, cite, pause-if-empty, §2.2) |
| 5 | `ai-agent-domain-expert/SKILL.md` | Research Mission §2: reference config-driven source modes instead of bare "Jira, Confluence, etc." |
| 6 | `ai-agent-domain-expert/advise.md` | Phase 2: add source 5 — query Jira via MCP (when configured) for tickets referencing past experiments/models |
| 7 | `ai-agent-mlops-engineer/infra.md` | New "Tracker Verification" step: ping, offline fallback, Infra Log recording (§4.1) |
| 8 | `ai-agent-experimentation-engineer/experiment.md` | Step 2: read tracker mode from Infra Log; offline task-ID convention (§4.2) |
| 9 | `ai-agent-experimentation-engineer/results.md` | Step 1: tracker API or local-store metric pull per recorded mode (§4.2) |
| 10 | `ai-agent-researcher/architecture.md` | Step 3: respect configured tracker; write back changes via configure (§4.2) |
| 11 | `README.md` | New "Internal Data Sources" section (two modes, `imports/` convention); extend "Experiment Tracking" with verification/offline behavior |
| 12 | `ai-setup/scripts/init_project.py` | `new-project`: create `imports/` tree, append `imports/` to generated `.gitignore` |

No new scripts are required; MCP detection and tracker pings are agent-executed instructions, not shipped code.

---

## 6. Open Decisions for the User

1. **Default posture: MCP-first vs export-first.**
   - (a) Assume MCP available, export as exception. (b) Default to file-export, MCP opt-in. (c) **Auto-detect MCP at `ai-setup configure`; fall back to export per source when nothing is detected.**
   - **Recommendation: (c).** Zero-config where MCP exists; air-gapped users get an identical workflow through `imports/` without ever seeing MCP prompts. Detection is confirmable, so a wrong guess costs one keystroke.
2. **SharePoint integration depth.**
   - (a) Full Graph-API MCP guidance. (b) **Export-only for now** (documents land in `imports/sharepoint/`), with `ai_mcp_servers` able to record a SharePoint server if the org has one.
   - **Recommendation: (b).** No canonical SharePoint MCP server exists yet, and Graph auth setup (app registration, admin consent) is out of scope for a skill module. Revisit when the ecosystem settles.
3. **Should `imports/` be gitignored by default?**
   - (a) **Yes** — exports frequently contain sensitive internal data; the Domain Knowledge Base (which cites them) is the committed artifact. (b) No — commit for team sharing.
   - **Recommendation: (a).** Teams that want shared exports can remove the ignore line consciously.
4. **Tracker verification failure behavior in Stage 5.**
   - (a) Hard-fail and stop. (b) **Warn, switch to offline mode, record in Infra Log, continue.**
   - **Recommendation: (b).** Air-gapped and not-yet-provisioned servers are normal; offline runs are fully syncable later in all three tools. A hard fail would block the exact users this design targets.
5. **Where per-source scope lives (Jira project keys, Confluence spaces, share paths).**
   - (a) **In `_bmad/config.yaml` under `ai_internal_sources`**, set at configure time. (b) Asked interactively each `domain-research` run.
   - **Recommendation: (a)** with a per-run confirmation ("Researching against Jira projects FOO, BAR — still correct?"), so repeat cycles and `--headless` advisory runs need no re-entry.

---

## 7. Air-Gapped Summary

- Install already supports local-path `--custom-source`; this design adds nothing network-dependent to setup.
- Internal sources: export mode (§2.2) is a first-class peer — same phases, same Domain Knowledge Base format, file-path citations instead of URLs.
- Trackers: `ai_tracker_offline` forces offline stores (W&B offline, MLflow file store, ClearML offline session); Stage 6/6.5 read local stores transparently; sync/import happens if and when a server appears.
- MCP detection in `--headless` configure degrades safely: nothing detected → everything defaults to export mode.
