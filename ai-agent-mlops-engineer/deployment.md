# Capability: Deployment

## Overview
The final lifecycle stage (Stage 9). Jointly confirms with the user that the project goal is reached, elicits deployment requirements, and implements what is needed to serve the accepted model. Deployment is a decision the user makes with the agents — never a step the agent takes on its own.

## Operating Instructions

### Phase A — Goal-Attainment Review (joint decision, hard gate)
1. **Input:** Read the Research Thesis tiers (`docs/Research_Thesis.md`), the latest Analysis document (`{ai_output_folder}/experiments/{ID}/ANALYSIS_*.md`), and the Revision Log (`{ai_output_folder}/revisions/Revision_Log.md`).
2. **Compare:** Present a structured goal-vs-achieved comparison — for each acceptance tier (Tier 1/2/3), show the target, the best achieved result, and pass/miss status, plus any open risks or caveats from the Analysis and Revision Log.
3. **Decide jointly:** Explicitly ask the user to decide: **deploy as-is** / **one more experiment cycle** / **descope** (deploy against a reduced goal). **Ask, don't guess** — present the options with a brief recommendation, and let the user decide.
4. **Gate:** This is a hard stop. Do **no** deployment work until the user declares the goal reached (as-is or descoped). If the user chooses another experiment cycle, hand off to `techspec` and end this capability.

### Phase B — Deployment Requirements Elicitation
Elicit each of the following from the user. **Ask, don't guess** — for every item, present sensible options with a brief recommendation and let the user decide:
1. **Serving mode:** batch / online API / streaming / edge.
2. **Latency & throughput targets:** p50/p99 latency, requests or records per second, batch window.
3. **Target environment:** read `configs/project_infra.yaml` for the data location, artifact registry, and compute topology set at scaffold time; confirm with the user where serving will run.
4. **Packaging:** docker image (reuse the scaffold's `docker/Dockerfile.train` as the base reference for a serving image), plain process, or platform-native artifact.
5. **Monitoring & alerting:** metrics to watch (latency, error rate, drift), where they go, alert thresholds.
6. **Rollback strategy:** how to revert to the previous model/version, and what triggers a rollback.
7. **Security / compliance constraints:** data handling, network boundaries, secrets, audit requirements.
8. **Ownership / handover:** who operates the deployment after handover, and what they need documented.

Write `{ai_output_folder}/deployment/Deployment_Requirements.md` covering all of the above.

**Review Gate:** Stop. Summarize the requirements, ask the user to review and comment, and wait for explicit approval before any implementation work.

### Phase C — Implementation
1. **Model adaptation + V&V:** Invoke the existing `inference-pipeline` capability to adapt the accepted model (optimization, inference class/API, post-adaptation V&V on the test set).
2. **Serving packaging:** Build the serving image/artifact per the approved requirements (e.g., a serving Dockerfile derived from `docker/Dockerfile.train`).
3. **Deployment scripts/manifests:** Write the scripts or manifests needed for the target environment (deploy, health check, rollback).
4. **Monitoring hooks:** Wire the monitoring and alerting agreed in Phase B.
5. **Smoke test:** Deploy to the target (or a staging equivalent), run an end-to-end smoke test, and record the result.
6. **Output:** Write `{ai_output_folder}/deployment/Deployment_Report.md` — what was deployed, where, how to roll back, and V&V results. **Failed attempts are mandatory:** document every deployment attempt that failed and how it was resolved; a report with no failures documented is incomplete unless everything genuinely worked first try.
7. **Review Gate:** Stop. Summarize what was deployed, the smoke-test and V&V results, and the rollback path. Ask the user to review and comment, and wait for explicit approval before declaring the lifecycle complete.

## Output Template

### Deployment_Requirements.md
- Goal-Attainment Decision (deploy as-is / descoped — with the user's stated rationale)
- Serving Mode
- Latency & Throughput Targets
- Target Environment (from `configs/project_infra.yaml` + user confirmation)
- Packaging
- Monitoring & Alerting
- Rollback Strategy
- Security / Compliance Constraints
- Ownership & Handover

### Deployment_Report.md
- What Was Deployed (model version, artifact, image tag)
- Where (environment, endpoint/location)
- How to Roll Back (exact steps)
- V&V Results (from `inference-pipeline` + post-deployment smoke test)
- Monitoring In Place
- Failed Attempts & Resolutions
- Handover Notes
