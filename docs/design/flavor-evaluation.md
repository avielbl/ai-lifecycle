# Design: Automated Flavor Evaluation on GCP — Claude (standard) vs Nemotron Super (guided)

**Status:** Proposed — pending user decisions (§8). Companion to [prompt-flavors.md](prompt-flavors.md) §4 (rollout step 2: "evaluate before writing wave 2") and §4b (Nemotron case study).

## 1. Objective & hypotheses

Run the [tutorial](../tutorial.md) fraud-detection lifecycle end-to-end, headlessly, on dedicated GCP resources, once per arm of a model×flavor matrix. Two outputs: (1) **calibration data** — the observed contract deviations that wave-2 guided overlays get written against, per prompt-flavors.md §Rollout; (2) **a stakeholder demo** — a reproducible, scored side-by-side of the module on a frontier model vs a self-hostable 49B model.

| # | Hypothesis | Falsifiable claim |
|---|---|---|
| H1 | Standard flavor + frontier model completes the lifecycle with high artifact-contract compliance | Claude+standard passes ≥ 95% of L1 checks and completes all 9 in-scope stages, all 3 seeds |
| H2 | Guided flavor closes most of the Nemotron gap | Nemotron+guided recovers ≥ 60% of the L1 gap between Nemotron+standard and Claude+standard (absolute floor: ≥ 85% L1, ≥ 7/9 stages) |
| H3 | Guided overlays don't degrade frontier output (sanity, optional arm) | Claude+guided L1/L2 within noise (±1 L1 check, ±0.3 L2 points) of Claude+standard |

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

| Arm | Model | `ai_prompt_flavor` | Purpose | Priority |
|---|---|---|---|---|
| A | Claude Opus 4.8 (Vertex) | standard | H1 baseline — the profile the prompts were written for | required |
| B | Nemotron Super 49B v1.5 (self-hosted) | guided | H2 — the arm the overlays exist for | required |
| C | Nemotron Super 49B v1.5 | standard | Ablation — proves the overlays cause the improvement, not the model | recommended |
| D | Claude Opus 4.8 | guided | H3 sanity — overlays don't hurt frontier output | optional |

N = 3 seeded runs per arm (fresh workspace each; seed varies the harness RNG and dataset split seed passed at ideation). 3 is enough to separate systematic contract failures from one-off flakes without tripling GPU cost; report per-seed and median.

## 4. GCP architecture

One dedicated project (e.g. `ai-lifecycle-eval`), fully torn down after each campaign.

```
ai-lifecycle-eval (GCP project)
├── Vertex AI: Anthropic publisher models (serverless, arms A/D + judge)
├── GCE: nemotron-vllm — a2-ultragpu-2g Spot (2×A100-80GB), vLLM 0.9.2+, arms B/C
├── GCE: orchestrator — e2-standard-8, runs the harness, one arm at a time
└── GCS: gs://ai-lifecycle-eval/{dataset,fixtures,runs/<arm>/<seed>/{workspace,transcripts},reports}
```

**Claude arm (A/D)** — Vertex AI Anthropic partner models, serverless (no deploy step). Verified: model is in the endpoint URL (`…/locations/global/publishers/anthropic/models/claude-opus-4-8:rawPredict`), `anthropic_version: "vertex-2023-10-16"` in the body; the official SDKs support this via `AnthropicVertex` (`pip install "anthropic[vertex]"`); current IDs include `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5@20251001`. Use the **global endpoint** (max availability, no 10% regional premium). Fallback: direct Anthropic API — the harness config differs by provider block only. ([Claude on Vertex AI docs](https://platform.claude.com/docs/en/api/claude-on-vertex-ai))

**Nemotron arm (B/C)** — two verified paths:

| | Model Garden deploy | Self-managed vLLM on GCE (recommended) |
|---|---|---|
| Path | Not a first-party Model Garden card (verified: AWS Bedrock/JumpStart listings exist; no Vertex listing). Deployable via Model Garden's **deploy-from-Hugging-Face** flow (`gcloud ai model-garden models deploy`, prebuilt vLLM containers, e.g. `a3-highgpu-2g`) | `a2-ultragpu-2g` (2×A100-80GB) **Spot** + startup script: vLLM ≥ 0.9.2, `--tensor-parallel-size 2 --max-model-len 131072 --enable-auto-tool-choice --tool-parser-plugin <repo parser>` |
| GPU fit | HF card: 2×H100-80GB or 2×A100-80GB (bf16); 1×H200 also fits | same requirement; A100 pair is the cheapest verified-supported config |
| API | Vertex endpoint; OpenAI-compatible route exists but adds Vertex auth/token plumbing to the harness | native `http://<host>:8000/v1` — exactly what the harness and `llm_config.yaml` (`provider: openai-compatible`) already expect |
| Cost | managed-endpoint pricing, no Spot | Spot ≈ 60–70% off on-demand; instance lives only for the arm's runs |

**Recommendation: self-managed vLLM on GCE Spot.** The eval is bursty (hours, not weeks), the OpenAI-compatible surface is the module's already-shipped integration path (prompt-flavors.md §4b), and Spot pricing dominates. Model Garden HF-deploy is the documented fallback if Spot capacity or ops effort becomes the constraint. Region: pick one with A100-80GB Spot availability (e.g. `us-central1`); the Claude global endpoint is region-independent. ([HF model card](https://huggingface.co/nvidia/Llama-3_3-Nemotron-Super-49B-v1_5), [Model Garden vLLM/HF deploy docs](https://cloud.google.com/vertex-ai/generative-ai/docs/open-models/vllm/use-vllm))

**Orchestrator** — a plain GCE VM running the harness sequentially per arm (open decision 5 weighs Cloud Build/Batch). Per run: pull fixtures from GCS → scaffold workspace (`init_project.py`) → execute the run manifest (§5) → sync workspace + transcripts to GCS → next seed. **Teardown**: one script deletes the vLLM instance after arms B/C and the orchestrator at campaign end; the project itself is deletable because nothing durable lives outside GCS.

**Indicative cost per full campaign** (4 arms × 3 seeds; verify against current pricing before running):

| Item | Basis | Estimate |
|---|---|---|
| Nemotron serving | ~4 h/run × 6 runs on 2×A100 Spot (~$3–5/h) | $70–120 |
| Claude tokens (arms A/D + judge) | ~6 runs × Opus-class agentic session + L2 judging | $150–400 |
| Orchestrator + GCS | e2-standard-8 ~30 h + <10 GB | ~$15 |
| **Total** | | **~$250–550** (Spot; roughly 2× if on-demand GPUs) |

## 5. Automation harness

**Verified harness options:** (a) **opencode** — non-interactive `opencode run` for CI/scripting, natively consumes the SKILL.md convention this module ships, and supports both Vertex/Anthropic providers and any OpenAI-compatible endpoint ([CLI docs](https://opencode.ai/docs/cli/)); (b) **Claude Code headless** — `claude -p` with the Vertex backend via `CLAUDE_CODE_USE_VERTEX=1`, `ANTHROPIC_VERTEX_PROJECT_ID`, `CLOUD_ML_REGION` ([Claude Code on Vertex docs](https://code.claude.com/docs/en/google-vertex-ai)).

**Recommendation: opencode for all arms.** One harness for both backends removes harness capability as a confound — the matrix then varies exactly two things: model and flavor. `claude -p` stays as the fallback Claude driver if opencode's Vertex-Anthropic path proves flaky in the pilot (open decision 5 caveat: if it's used, note the harness asymmetry in the report).

**Per-arm configuration** (all existing mechanisms, nothing new to build):

- `ai_prompt_flavor` in `config.user.yaml`: `standard` (A/C) or `guided` (B/D) — the §4 loading rule does the rest.
- Harness model: `opencode.json` provider block — Vertex Anthropic (`claude-opus-4-8`) for A/D; OpenAI-compatible `base_url: http://<vllm-host>:8000/v1` for B/C. Nemotron reasoning toggle stays ON (default) — the guided overlays already carry the per-capability toggle note (prompt-flavors.md §4b).
- `configs/llm_config.yaml` (script calls): matching provider block per backend, `temperature: 0.0`.

**Run manifest** — one YAML per run, executed stage-by-stage:

```yaml
arm: nemotron-guided        # A|B|C|D name
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

**Failure handling.** A stage that exceeds its timeout, exits nonzero, or fails a blocking L1 precondition (its contracted artifact absent) marks the stage `failed` and the run `degraded`; the runner still attempts downstream stages (they surface how failures cascade — itself calibration signal) but never blocks the other seeds/arms. One retry per stage for infrastructure-class failures only (endpoint 5xx, Spot preemption); model-behavior failures are never retried — they are the data.

## 6. Scoring

Three layers, scored per run, aggregated per arm.

**L1 — artifact-contract compliance (scripted, objective).** A checker script walks the workspace against the contract:
- Files exist at the CSV/manifest-contracted paths (`docs/Research_Thesis.md`, `docs/prd/PRD.md`, `docs/eda/EDA_Report.md` + executed `notebooks/eda_report.ipynb`, `docs/architecture/Architecture.md`, `docs/design/Detailed_Design.md`, `docs/experiments/E1/{TECHSPEC,RUN_*,RESULTS_*,ANALYSIS_*}.md` + `configs/`, `docs/implementation/Infra_Log.md`).
- Required sections present (thesis: hypothesis/failure costs/data characterization/success tiers; PRD: FR-/NFR- IDs; TECHSPEC: numeric tier thresholds; Detailed Design: INF-*/EXP-* IDs; Analysis: What Went Wrong).
- Memory protocol: `docs/memory/index.md` rows appended per stage's mandatory update; entry files parse (frontmatter schema, <20 lines).
- Gates ledger: one row per completed stage.
- Naming consistent with `ai-lifecycle.csv` output-locations.

Score = checks passed / checks applicable (~40–50 checks). **This is the layer wave-2 overlays are written from** — every failed check is tagged with capability + failure mode.

**L2 — artifact quality (LLM judge, rubric).** Fixed frontier judge scores each major artifact 1–5 against a per-artifact rubric: thesis→PRD traceability, TECHSPEC completeness/lockdown, EDA baseline defensibility, analysis root-causing depth. Judge is **blind to arm**: artifacts are stripped of model/flavor identifiers, presented in randomized order, one artifact per call, temperature 0. Judge model: open decision 4.

**L3 — operational.** Per stage and per run: input/output tokens, wall-clock, cost, retry count, timeout/failure count. No pass threshold — context for the demo and for overlay sizing (guided overlays cost tokens; measure how many).

**Pass thresholds:** H1 and H2 as defined in §1 (L1-based, with L2 median ≥ 4.0 required for H1). H2's gap-closure form requires arm C; if C is cut, the absolute floor applies.

## 7. Deliverables & follow-up

1. **Evaluation report** (`docs/design/flavor-evaluation-results.md`): arms × seeds L1/L2/L3 table, per-hypothesis verdict, per-capability failure catalog (check failed → transcript excerpt → diagnosis).
2. **Wave-2 overlay mapping** — the calibration output: each recurring Nemotron failure mode maps to overlay content in a named file (`<agent>/guided/<capability>.md`), per the prompt-flavors.md rule that overlays are written against observed failures, not guesses. Also: prune wave-1 overlay sections that arm C shows were unnecessary.
3. **Stakeholder demo package**: one polished A-arm and one B-arm workspace (the artifact trees are self-explanatory), the scoring dashboard, and a 1-page summary — "same module, same challenge, frontier vs self-hostable model" — framed around the on-prem/air-gapped story that motivates Nemotron.
4. **Reusable rig**: run manifests, checker script, and teardown scripts stay in the eval project's repo as the flavor regression check that prompt-flavors.md §Rollout step 3 calls for.

## 8. Open decisions

1. **Dataset** — ULB credit-card CSV (real, recognizable, matches the tutorial's numbers) vs synthetic generator (fully hermetic). **Recommend ULB pinned in GCS** for the demo's credibility; ship the synthetic generator as the documented air-gapped fallback.
2. **Nemotron serving** — Model Garden HF-deploy (managed) vs self-managed vLLM on GCE Spot. **Recommend self-managed vLLM on `a2-ultragpu-2g` Spot** (§4): native OpenAI-compatible API, Spot economics, and it exercises the module's shipped on-prem path.
3. **Arm count** — 2 required vs 3 vs 4. **Recommend 3 (A, B, C)**: without the C ablation, H2 can't attribute improvement to the overlays. D is cheap to add later if H3 becomes contested.
4. **Judge model** — Claude Opus-class (strongest rubric-following; already provisioned) vs a third-family judge (no self-preference toward arm A). **Recommend Claude Opus 4.8 with strict blinding** (identifiers stripped, order randomized), plus a Gemini-family cross-check on a 10% artifact sample; escalate to full dual-judging only if the two disagree by >0.5 on that sample.
5. **Orchestrator** — GCE VM (simple, inspectable mid-run, SSH debugging) vs Cloud Build/Batch (serverless, but agentic sessions are long-lived and interactive-ish to debug). **Recommend the GCE VM for v1**; revisit Batch when the rig becomes the recurring regression check (deliverable 4).
