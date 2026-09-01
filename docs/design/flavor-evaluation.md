# Design: Automated Flavor Evaluation — Validating the guided/standard Mechanism

**Status:** Redesigned per owner direction (2026-09-01) — **local two-run design**: both arms run on the owner's dev VM; arm A drives Claude Code, arm B drives opencode against Nemotron Super 49B deployed through Vertex AI Model Garden (deploy-from-Hugging-Face). The endpoint is the plan's only provisioned resource. In-network (air-gapped) verification remains a rerun of the same rig against a local vLLM host (§7.4). Companion to [prompt-flavors.md](prompt-flavors.md) §4 (rollout step 2: "evaluate before writing wave 2").

## 1. Objective & hypotheses

Run the [tutorial](../tutorial.md) fraud-detection lifecycle end-to-end, headlessly, once per arm of a harness×model×flavor matrix, entirely from the owner's dev machine. Arm A (Claude Code + frontier Claude, standard flavor) is the baseline profile the prompts were written on; arm B (opencode + Nemotron Super, guided flavor) is the exact target profile the overlays exist for — validating the mechanism directly on the motivating model rather than through a proxy.

Two outputs: (1) **calibration data** — observed contract deviations that wave-2 guided overlays get written against; (2) **a stakeholder demo** — a reproducible, scored side-by-side of the module on a frontier vs a mid-tier model.

| # | Hypothesis | Falsifiable claim |
|---|---|---|
| H1 | Standard flavor + Claude Code baseline completes the lifecycle with high artifact-contract compliance | Arm A passes ≥ 95% of L1 checks and completes all 9 in-scope stages, all 3 seeds |
| H2 | Guided flavor closes most of the Nemotron gap | Arm B recovers ≥ 60% of the L1 gap between arm C (Nemotron+standard) and arm A (absolute floor: ≥ 85% L1, ≥ 7/9 stages) |

## 2. Demo challenge

Reuse the tutorial scenario unchanged: a card-transaction fraud classifier, `ai_output_folder: docs`, tracker MLflow in offline mode (`file:./mlruns` — no tracker service to provision, and the Stage 5 fallback path is itself under test).

**Dataset.** The ULB credit-card fraud CSV (284,807 transactions, 492 frauds, 0.172% positive — the exact profile the tutorial narrates). Fetched once, pinned by SHA-256, staged in GCS; runs never touch the public internet for data. Fallback for air-gapped reruns: a seeded synthetic generator producing the same schema/imbalance (open decision 1).

**Stage scope** — exactly the capabilities whose manifests declare `supports-headless: true`:

| Stage | Capability | Mode |
|---|---|---|
| 1-research, 1.2-literature | domain-research, literature-review | **Pre-seeded fixtures** — `Domain_Knowledge_Base.md`, `Literature_Review.md`, and initial memory entries copied into the workspace before the run. Web results aren't reproducible, and domain-research is `supports-headless: false` by design |
| 1.5 → 7 | ideation, eda, architecture, detailed-design, techspec, infra, experiment, results, analysis | **Run headlessly** (9 stages; all are `supports-headless: true`) |
| 4.6, 7.5, 8, 9 | decisions, hparam, revision-audit, deployment | Out of scope for v1 (interactive by design or optional) |

**Review gates in headless mode.** Per the manifests' headless contract: at each gate the agent writes the gate summary it would have presented, appends a row to `docs/gates/gates-ledger.md` (stage, timestamp, summary path, auto-approved), and proceeds. Ask-don't-guess moments resolve to the agent's own recommendation, recorded the same way. The ledger is an L1-scored artifact — a skipped gate is a contract violation, not a shortcut.

## 3. Arms matrix

| Arm | Harness | Model | `ai_prompt_flavor` | Purpose | Priority |
|---|---|---|---|---|---|
| A | Claude Code (`claude -p`) | Claude (this machine's existing Claude Code auth) | standard | H1 baseline — the harness+model the prompts were written on | required |
| B | opencode (`opencode run`) | Nemotron Super 49B v1.5 — Model Garden HF-deploy → Vertex endpoint | guided | H2 — the arm the overlays exist for, on the model that motivates them | required |
| C | opencode | same Nemotron endpoint | standard | Ablation — proves the overlays cause the improvement, not the model | recommended (one more local run against the already-deployed endpoint — nearly free) |

**Known confound, accepted:** arms A and B differ in harness as well as model+flavor. For this campaign's purpose (mechanism validation + demo) that is acceptable; if attribution ever matters, the cheap de-confound is re-running arm A under opencode pointed at Claude on Vertex (one provider block).

N = 3 seeded runs per arm (fresh workspace each; seed varies the harness RNG and the dataset split seed passed at ideation). 3 is enough to separate systematic contract failures from one-off flakes; report per-seed and median.

## 4. Architecture — one machine, two runs

Everything runs on the existing dev VM (verified: GCE `e2-standard-4`, project `internal-project-470910`, service-account ADC active, Claude Code 2.1.237 and gcloud installed). No orchestrator VM, no central GCS staging — workspaces are local project dirs, optionally synced to GCS at campaign end.

```
this VM (GCE e2-standard-4)
├── ~/eval/arm-a-<seed>/   fresh scaffold, driven by claude -p          (arm A)
├── ~/eval/arm-b-<seed>/   fresh scaffold, driven by opencode run      (arms B/C)
└── Vertex AI endpoint: Nemotron Super 49B v1.5
    deployed via Model Garden deploy-from-Hugging-Face (prebuilt vLLM container,
    2×A100-80GB or 1×H200 class), OpenAI-compatible chat/completions route
```

**Arm A model access** — Claude Code's own auth on this machine; no extra setup. (`claude -p` can alternatively target Vertex Anthropic models via `CLAUDE_CODE_USE_VERTEX=1` if token accounting should stay inside GCP.)

**Arms B/C model access** — deploy once per campaign window: `gcloud ai model-garden models deploy` from the HF model id, then call the endpoint's **OpenAI-compatible `chat/completions` route** with a bearer token. On this VM the token comes from the service account (`gcloud auth print-access-token`, 60-min TTL) — the runner exports a fresh token into opencode's provider env at each stage launch, which suffices because every stage is a fresh session. **Undeploy the endpoint at campaign end** — it bills per GPU-hour while deployed.

**Preconditions** (the only two): `npm i -g opencode-ai` on this VM; GPU quota for Vertex online prediction in the chosen region (`custom_model_serving_nvidia_a100_80gb_gpus` ≥ 2 or an H200 equivalent) in `internal-project-470910`.

**Indicative cost per full campaign** (3 arms × 3 seeds; verify pricing before running):

| Item | Basis | Estimate |
|---|---|---|
| Nemotron endpoint | ~2×A100-80GB managed, on-demand, deployed only for the B/C window (~12–24 h) | $120–300 |
| Claude usage (arm A + judge) | existing Claude Code plan/API | plan-dependent |
| VM + storage | already running | ~$0 marginal |
| **Total incremental** | | **~$120–300 + Claude tokens** |

## 5. Automation harness

**Two drivers, both verified:** (a) **Claude Code headless** — `claude -p "<stage prompt>"` per stage in the arm-A workspace (installed on this VM; [headless docs](https://code.claude.com/docs/en/google-vertex-ai) cover the optional Vertex backend); (b) **opencode** — non-interactive `opencode run` for arms B/C, natively consumes the SKILL.md convention this module ships and takes any OpenAI-compatible endpoint ([CLI docs](https://opencode.ai/docs/cli/)). A single bash runner iterates the manifest for both arms; arms can run in parallel (both are API-bound; stage 6's local training is small enough for the 4-vCPU VM, but stagger the two arms' stage-6 windows if contention shows).

**Per-arm configuration** (all existing mechanisms, nothing new to build):

- `ai_prompt_flavor` in each workspace's `config.user.yaml`: `standard` (A/C) or `guided` (B) — the prompt-flavors loading rule does the rest.
- Arm A: Claude Code as configured on this machine.
- Arms B/C: opencode provider block — OpenAI-compatible, `base_url` = the Vertex endpoint's chat/completions URL, api key injected per stage from `gcloud auth print-access-token`. For the in-network air-gapped rerun (§7.4), only the `base_url` changes to the local vLLM host.
- `configs/llm_config.yaml` (script calls): matching provider block per backend, `temperature: 0.0`.

**Run manifest** — one YAML per run, executed stage-by-stage:

```yaml
arm: nemotron-guided         # A|B|C name
seed: 1
stages:                      # order = ai-lifecycle.csv phase order
  - {capability: ideation,        agent: ai-agent-domain-expert,            timeout_min: 30}
  - {capability: eda,             agent: ai-agent-data-engineer,            timeout_min: 45}
  - {capability: architecture,    agent: ai-agent-researcher,               timeout_min: 30}
  - {capability: detailed-design, agent: ai-agent-researcher,               timeout_min: 20}
  - {capability: techspec,        agent: ai-agent-mlops-engineer,           timeout_min: 30}
  - {capability: infra,           agent: ai-agent-mlops-engineer,           timeout_min: 60}
  - {capability: experiment,      agent: ai-agent-experimentation-engineer, timeout_min: 90}
  - {capability: results,         agent: ai-agent-experimentation-engineer, timeout_min: 20}
  - {capability: analysis,        agent: ai-agent-researcher,               timeout_min: 30}
```

Each stage = one fresh harness session (`opencode run "<headless stage prompt>"`), matching the module's one-capability-per-session rule; full transcript captured to GCS. The stage prompt states: headless mode, auto-approve gates per §2, resolve choices to your own recommendation and record them.

**Failure handling.** A stage that exceeds its timeout, exits nonzero, or fails a blocking L1 precondition (its contracted artifact absent) marks the stage `failed` and the run `degraded`; the runner still attempts downstream stages (they surface how failures cascade — itself calibration signal) but never blocks the other seeds/arms. One retry per stage for infrastructure-class failures only (endpoint 5xx); model-behavior failures are never retried — they are the data.

## 6. Scoring

Three layers, scored per run, aggregated per arm.

**L1 — artifact-contract compliance (scripted, objective).** A checker script walks the workspace against the contract:
- Files exist at the CSV/manifest-contracted paths (`docs/Research_Thesis.md`, `docs/prd/PRD.md`, `docs/eda/EDA_Report.md` + executed `notebooks/eda_report.ipynb`, `docs/architecture/Architecture.md`, `docs/design/Detailed_Design.md`, `docs/experiments/E1/{TECHSPEC,RUN_*,RESULTS_*,ANALYSIS_*}.md` + `configs/`, `docs/implementation/Infra_Log.md`).
- Required sections present (thesis: hypothesis/failure costs/data characterization/success tiers; PRD: FR-/NFR- IDs; TECHSPEC: numeric tier thresholds; Detailed Design: INF-*/EXP-* IDs; Analysis: What Went Wrong).
- Memory protocol: `docs/memory/index.md` rows appended per stage's mandatory update; entry files parse (frontmatter schema, <20 lines).
- Gates ledger: one row per completed stage.
- Naming consistent with `ai-lifecycle.csv` output-locations.

Score = checks passed / checks applicable (~40–50 checks). **This is the layer wave-2 overlays are written from** — every failed check is tagged with capability + failure mode.

**L2 — artifact quality (LLM judge, rubric).** Fixed frontier judge scores each major artifact 1–5 against a per-artifact rubric: thesis→PRD traceability, TECHSPEC completeness/lockdown, EDA baseline defensibility, analysis root-causing depth. Judge is **blind to arm**: artifacts are stripped of model/flavor identifiers, presented in randomized order, one artifact per call, temperature 0. Judge model: open decision 3.

**L3 — operational.** Per stage and per run: input/output tokens, wall-clock, cost, retry count, timeout/failure count. No pass threshold — context for the demo and for overlay sizing (guided overlays cost tokens; measure how many).

**Pass thresholds:** H1 and H2 as defined in §1 (L1-based, with L2 median ≥ 4.0 required for H1). H2's gap-closure form requires arm C; if C is cut, the absolute floor applies.

## 7. Deliverables & follow-up

1. **Evaluation report** (`docs/design/flavor-evaluation-results.md`): arms × seeds L1/L2/L3 table, per-hypothesis verdict, per-capability failure catalog (check failed → transcript excerpt → diagnosis).
2. **Wave-2 overlay mapping** — the calibration output: each recurring mid-tier failure mode maps to overlay content in a named file (`<agent>/guided/<capability>.md`), per the prompt-flavors.md rule that overlays are written against observed failures, not guesses. Also: prune wave-1 overlay sections that arm C shows were unnecessary.
3. **Stakeholder demo package**: one polished A-arm and one B-arm workspace (the artifact trees are self-explanatory), the scoring dashboard, and a 1-page summary — "same module, same challenge, frontier vs mid-tier model, with and without guided scaffolding."
4. **Air-gapped rerun handoff** — the reusable rig (run manifests, checker script, fixtures, stage prompts) packaged so the module owner can rerun arms B/C against any in-network OpenAI-compatible endpoint (e.g. Nemotron on vLLM) by swapping one provider block. Model-specific serving guidance lives in [docs/air-gapped.md](../air-gapped.md), not in this plan. The rig doubles as the recurring flavor regression check that prompt-flavors.md §Rollout step 3 calls for.

## 8. Open decisions

1. **Dataset** — ULB credit-card CSV (real, recognizable, matches the tutorial's numbers) vs synthetic generator (fully hermetic). **Recommend ULB pinned in GCS** for the demo's credibility; ship the synthetic generator as the documented air-gapped fallback.
2. **Arm count** — 2 vs 3. **Recommend 3 (A, B, C)**: without the C ablation, H2 can't attribute improvement to the overlays, and C reuses the already-deployed endpoint.
3. **Judge model** — Claude Opus-class (strongest rubric-following; already provisioned) vs a third-family judge (no self-preference toward arm A). **Recommend Claude Opus 4.8 with strict blinding** (identifiers stripped, order randomized), plus a Gemini-family cross-check on a 10% artifact sample; escalate to full dual-judging only if the two disagree by >0.5 on that sample.
4. **Harness de-confound arm** — add an opencode+Claude-on-Vertex run to separate harness effects from model+flavor effects, or accept the confound for v1. **Recommend accept for v1** (this campaign is mechanism validation + demo); add the de-confound arm only if arm A vs B differences look harness-shaped (e.g., tool-call formatting failures rather than content failures).
