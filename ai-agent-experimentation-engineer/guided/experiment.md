# Guided Scaffolding for Experiment Execution

Follow `experiment.md` (canonical). This overlay adds explicit scaffolding — same artifacts, same paths, same gate. Where it conflicts with the canonical file, this file wins.

If your model has a reasoning toggle (e.g. Nemotron's `/no_think`), reasoning OFF is recommended for the mechanical run-execution steps (3-6) — it cuts latency and tokens; keep it ON only if you hit an ambiguity that needs judgment.

## Micro-Steps (do not reorder)

1. Read `{ai_output_folder}/experiments/{ID}/TECHSPEC.md`. Do not continue until you have listed each arm and its acceptance gates back to the user. If any TECHSPEC entry is ambiguous, stop and ask — never improvise parameters.
2. Read the tracker mode from the Infra Log (online with resolved URL, or offline). In offline mode, use the local run directory as the tracker task ID (`offline:./mlruns/<run_id>`). Scan `{ai_output_folder}/memory/index.md` for `lesson` rows whose tags match the tracker or tooling; Read only those entry files. Do not continue until step 2's output exists (tracker mode + lessons read, or "none matched").
3. Run the smoke test (see closed choice below). Do not continue until the smoke test has completed and logged successfully.
4. Execute the training scripts exactly per the TECHSPEC execution plan, one phase at a time. Do not continue to phase N+1 until phase N's logged run exists in the tracker (or offline store).
5. Fill in the RUN log skeleton below and write it to `{ai_output_folder}/experiments/{ID}/RUN_{YYYY-MM-DD_HH-MM-SS}.md`. Do not continue until the file exists with every `<placeholder>` replaced.
6. Copy every config file used into `{ai_output_folder}/experiments/{ID}/configs/`. Do not continue until the copies exist.
7. **Review Gate (hard stop):** complete the self-check below, summarize run outcomes and issues, wait for explicit user approval before handing off to Results. Then stop.

## Closed Choices (ask, don't guess — present these to the user)

- **Smoke-test scale** — choose exactly one: (a) tiny subset (~1% of data or a handful of iterations/rounds), (b) a single batch/round forward+backward only, (c) one full epoch/round on the full data. If unsure, pick (a).
- **On mid-run failure** — choose exactly one: (a) stop, log the failure in the RUN log, and ask the user, (b) retry once with the identical config, then (a) if it fails again, (c) skip the arm and continue the remaining arms, flagging it. If unsure, pick (a). Never change parameters to "fix" a run.

## Copy-This Skeleton — `{ai_output_folder}/experiments/{ID}/RUN_{YYYY-MM-DD_HH-MM-SS}.md`

```markdown
# RUN Log — <ID> — <YYYY-MM-DD_HH-MM-SS>

## Per-Arm Results
| arm | script command | tracker task ID | model summary | total params (pretrained/random) | best metric | convergence | wall-clock |
|-----|----------------|-----------------|---------------|----------------------------------|-------------|-------------|------------|
| <arm> | `<command>` | <id or offline:./mlruns/<run_id>> | <summary> | <n> (<p>/<r>) | <metric>=<value> | <converged/diverged/plateau> | <h:mm> |

## Execution Timeline
- <YYYY-MM-DD ~HH:MM UTC> — <event>

## Issues & Notes
- <issue encountered, or "none">

## Archived Configs
- configs/<file> (copied to experiments/<ID>/configs/)
```

## Pre-Gate Self-Check (complete before the Review Gate)

- [ ] Every arm from the TECHSPEC has a row in the Per-Arm Results table; no `<placeholder>` remains
- [ ] Every row has a tracker task ID (or `offline:<run-dir>` in offline mode) — an unlogged run is not valid
- [ ] Timeline uses `YYYY-MM-DD ~HH:MM UTC`; the filename uses `YYYY-MM-DD_HH-MM-SS`
- [ ] All config files used are copied into `experiments/{ID}/configs/`
- [ ] No parameter deviated from the TECHSPEC without explicit user instruction (deviations noted in Issues)
- [ ] Nothing was installed — missing dependencies were flagged to the user instead

## Memory — read-only for this capability

This capability writes NO memory entries (raw run data stays in the experiment folder). You already read `lesson` entries in step 2 — do not write to `{ai_output_folder}/memory/` at all.

## Hard Rule

One capability per session: finish the RUN log and its Review Gate, then stop (no memory rows to write here). Do not start Results, HPO, or any other capability in this session.
