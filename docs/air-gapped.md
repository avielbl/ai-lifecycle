# Air-Gapped & Corporate Environments

The module treats offline and restricted-network operation as a first-class mode, not a degraded one: every stage produces identical artifacts whether sources are queried live or read from exports, and whether trackers are online or offline. This guide consolidates everything you need. Full design rationale: [design/integrations.md](design/integrations.md).

## Installing without internet

**From a local path.** Copy the module (git bundle, zip, USB, network share) into the isolated network, then point the BMad installer at the directory:

```bash
npx bmad-method install \
  --directory . \
  --modules bmm \
  --custom-source /path/to/ai-lifecycle \
  --tools claude-code \
  --yes
```

**From an internal registry (Artifactory or similar).** If your organisation mirrors npm packages, publish/mirror `ai-lifecycle` and install by package name:

```bash
npx bmad-method install --directory . --modules bmm \
  --custom-source ai-lifecycle --tools claude-code --yes
```

Point npm at the mirror as usual (`npm config set registry https://artifactory.example.com/api/npm/npm-virtual/` or a project `.npmrc`). `uv` can likewise use an internal PyPI mirror via `UV_INDEX_URL` — needed at Stage 5 when `uv sync` runs.

## Internal MCP servers — air-gapped ≠ no MCP

Air-gapped networks often run their **own** MCP servers: an internal Atlassian gateway, an arXiv mirror, a filesystem server over a document share. The module never assumes offline means export-only.

At `ai-setup configure`, after auto-detecting whatever MCP servers your IDE already has, the skill **always asks**: *"Are there additional or internal MCP servers I can't see?"* For each one, give:

- the **exact server name as registered in your IDE/MCP config** (e.g. `mcp__internal-arxiv-mirror`) — never a guessed or normalized name, and
- **which source it serves** (jira / confluence / docs / arxiv / …).

These are recorded in `ai_mcp_servers`; each covered source gets `mode: mcp` in `ai_internal_sources` and is queried live during `domain-research`, `literature-review`, and `advise`. Sources without a server fall back to export mode below.

## Export drop-folder + background folders

Any source with no MCP server uses `{project-root}/imports/` — produced on the connected corporate network and carried across by whatever transfer mechanism you have:

```
imports/
  jira/          # CSV/XML exports (Issue Navigator → Export), one file per JQL query
  confluence/    # space exports (HTML/XML zip, unzipped) or individual page PDFs
  sharepoint/    # downloaded documents (PDF/DOCX/XLSX), keeping library structure
  docs/          # loose PDFs, specs, datasheets from network shares
  MANIFEST.md    # optional: what each export contains and when it was pulled
```

`imports/` is **gitignored by default** (except its README) — exports often contain sensitive data; the Domain Knowledge Base that cites them (by file path, e.g. `imports/jira/postmortems-2025.csv`) is the committed artifact. Research agents inventory the folder first and **pause with export instructions** if it is empty and no MCP source is configured — they never silently continue web-only.

**Background folders:** in air-gapped mode, `domain-research` and `literature-review` additionally ask for a folder of PDFs/reference files at **any path you name** — a mounted share works fine; you are not restricted to `imports/`.

## Offline experiment trackers

Set `ai_tracker_offline: true` at configure time (or leave `auto` — a failed connectivity ping at Stage 5 has the same effect). Stage 5 **warns, switches to the tool's offline store, records it in the Infra Log, and continues** — it never hard-fails on an unreachable tracker:

| Tracker | Offline mode | Sync later |
|---------|-------------|------------|
| W&B | `WANDB_MODE=offline` | `wandb sync <run-dir>` |
| MLflow | `tracking_uri: file:./mlruns` | point the client at the server |
| ClearML | `Task.set_offline(True)` | `Task.import_offline_session(...)` |

Stages 6/6.5 read the local stores transparently and record `offline:<run-dir>` task IDs — the RUN and RESULTS documents are identical to online mode. Self-hosted servers inside the network are supported via `ai_tracker_url`; credentials always live in env vars (`WANDB_API_KEY`, `MLFLOW_TRACKING_TOKEN`, `CLEARML_API_*`), never in config files.

## Local LLMs for analysis scripts

The agents themselves run on whatever model your IDE provides. Utility scripts that call an LLM programmatically (`scripts/llm_client.py`) are configured in `configs/llm_config.yaml`, which supports any **OpenAI-compatible** endpoint — including fully local ones:

```yaml
# Ollama
provider: openai-compatible
model: llama3.1:70b
base_url: http://localhost:11434/v1
api_key_env: OLLAMA_API_KEY   # any non-empty string; Ollama ignores it

# vLLM (self-hosted)
# provider: openai-compatible
# model: meta-llama/Llama-3.1-70B-Instruct
# base_url: http://localhost:8000/v1
# api_key_env: VLLM_API_KEY
```

Pick `openai-compatible` as `ai_llm_provider` at configure time; the template (`scripts/llm_config.yaml.template`) ships ready-made blocks for Ollama, vLLM, Azure, and others.

## Memory bank and scaffold — nothing to do

The per-project memory bank is plain markdown on the filesystem — zero dependencies, fully offline. `imports.yaml` cross-project references work over local mounts and shared network folders. Scaffolding (`new-project`) degrades gracefully too: `git init` and `uv venv` run locally, no packages are installed, and the git remote is optional and never pushed.

## Updating the module offline

Carry the new module version across, then re-run the installer with the same local-path (or internal-registry) `--custom-source` you installed from:

```bash
npx bmad-method install --directory . --modules bmm \
  --custom-source /path/to/ai-lifecycle --tools claude-code --yes
```

BMad re-fetches from that source and applies the update in place. Afterwards run `/ai-setup configure` once — it skips every key that already has a value, so an update typically asks nothing and only registers new capabilities with `/bmad-help`.
