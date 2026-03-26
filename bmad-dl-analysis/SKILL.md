\---

name: bmad-dl-analysis

description: Acts as a Data Scientist to analyze experiment results from the tracking tool (W&B/MLflow/ClearML) and local logs, evaluate against the pre-committed TECHSPEC, verify the hypothesis verdict, and produce a structured analysis report with mandatory failure documentation.

\---



\# BMAD Workflow 07: Experiment Analysis



\## 1. Operating Instructions

You are an expert Data Scientist and MLOps Engineer. Your goal is to analyze the results of the latest training runs, evaluate them against the pre-committed TECHSPEC, assess the hypothesis verdict, and surface all failure modes. You work with the Domain Expert to interpret findings in domain terms.

**Key discipline:** Results are evaluated against `docs/techspecs/TECHSPEC_EXP_[ID].md` as it was written before training. You do not reinterpret success criteria after seeing results.



1\. **Run the advisor first:** `/bmad-dl-advise` — surface what past experiments revealed before interpreting these results.



2\. **Read in order:**

   \- `docs/00_Research_Thesis.md` — active hypothesis (Section II), failure costs (Section III), data characterization (Section IV)
   \- `docs/techspecs/TECHSPEC_EXP_[ID].md` — pre-committed success tiers (Section E), known risks (Section F)
   \- `docs/experiments/06_Experiment_Log.md` — run summary and tracking URLs



3\. **Pull experiment data from the tracking tool:**

\`\`\`python

\# ── W&B ──────────────────────────────────────────────────────────────────────
import wandb
api = wandb.Api()
runs = api.runs(f"{ENTITY}/{PROJECT_NAME}", filters={"tags": {"$in": [f"EXP-{exp_id}"]}})
for run in runs:
    print(run.name, run.summary.get("val/f1"), run.summary.get("val/loss"))
    history = run.history(keys=["val/f1", "val/loss", "train/loss"])

\# ── MLflow ───────────────────────────────────────────────────────────────────
import mlflow
client = mlflow.MlflowClient(tracking_uri="./mlruns")
experiment = client.get_experiment_by_name(PROJECT_NAME)
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    filter_string=f"tags.exp_id = 'EXP-{exp_id}'"
)
for run in runs:
    print(run.info.run_name, run.data.metrics)

\# ── ClearML ──────────────────────────────────────────────────────────────────
from clearml import Task
tasks = Task.get_tasks(
    project_name=PROJECT_NAME,
    task_filter={"tags": [f"EXP-{exp_id}"]},
)
for task in tasks:
    scalars = task.get_reported_scalars()
    print(task.name, scalars.get("val", {}).get("f1", {}).get("y", [])[-1])

\`\`\`

   Also run local log parsers as fallback:

\`\`\`bash

python3 _bmad/bmad-dl-lifecycle/bmad-dl-analysis/scripts/parse_training_logs.py logs/[experiment]/version_0/metrics.csv docs/prd/01_PRD.md
python3 _bmad/bmad-dl-lifecycle/bmad-dl-analysis/scripts/plot_training_curves.py logs/[experiment]/version_0/metrics.csv --output docs/experiments/training_curves.png
python3 _bmad/bmad-dl-lifecycle/bmad-dl-analysis/scripts/plot_confusion_matrix.py predictions.csv --output-dir docs/experiments/

\`\`\`



4\. **Evaluate against TECHSPEC tiers** (Section E). State explicitly which tier was reached: Best case / Realistic / Worst case alive / Failure. This is not a judgment call — it is a comparison against pre-committed thresholds.



5\. **CRITICAL:** Do not generate the final file yet. Present preliminary findings. Ask **3–4 domain interpretation questions:**

   \- Hypothesis verdict: "The active hypothesis appears [supported/falsified/inconclusive] because [evidence]. The TECHSPEC tier reached is [tier]. Do you agree?"
   \- Domain failure cost: "The model confused Class A with Class B in N% of cases. Given the failure costs in the Thesis (Section III), what is the real-world impact of this error rate?"
   \- Unexpected behaviors: [anything not predicted by EDA or the hypothesis]
   \- Next direction: "Based on these results, what is your domain intuition for the next hypothesis?"

   Halt and wait.



6\. Once answered, write the final document to `docs/experiments/07_Analysis_EXP_[ID].md`.

\`\`\`bash

git add docs/experiments/07_Analysis_EXP_[ID].md
git commit -m "docs(analysis): experiment analysis EXP-[ID] -- hypothesis [SUPPORTED/FALSIFIED/INCONCLUSIVE]"

\`\`\`



7\. **Run `/bmad-dl-retrospective`** at the end of this session.



\## 2. Expected Output Template

\`\`\`markdown

\### A. Experiment Overview

\* \*\*Experiment ID:\*\* EXP-[ID]
\* \*\*Run Type:\*\* [Baseline / Tuned / Ablation]
\* \*\*Tracking Tool:\*\* [W&B / MLflow / ClearML] — [link to experiment/project]
\* \*\*Active Hypothesis:\*\* "[Exact quote from docs/00_Research_Thesis.md Section II]"
\* \*\*TECHSPEC:\*\* `docs/techspecs/TECHSPEC_EXP_[ID].md`



\### B. TECHSPEC Evaluation (pre-committed criteria)

| TECHSPEC Tier | Threshold | Achieved | Verdict |
| :--- | :--- | :--- | :--- |
| Best case | F1 ≥ 0.95 | [actual] | [REACHED / NOT REACHED] |
| Realistic | F1 ≥ 0.92 | [actual] | [REACHED / NOT REACHED] |
| Worst case (alive) | F1 0.85–0.92 | [actual] | [REACHED / NOT REACHED] |
| **Failure** | F1 < 0.85 | [actual] | [REACHED / NOT REACHED] |

\* \*\*Tier reached:\*\* [Tier name]
\* \*\*Goalpost integrity:\*\* [Were criteria evaluated as committed? Any post-hoc reinterpretation? Document honestly.]
\* \*\*HPO eligible:\*\* [Yes — baseline works, proceed to bmad-dl-hparam / No — revise architecture first]



\### C. Hypothesis Verdict

\* \*\*Status:\*\* [SUPPORTED / FALSIFIED / INCONCLUSIVE]
\* \*\*Evidence:\*\* [Specific metrics and behaviors that confirm or deny the hypothesis]
\* \*\*Domain Expert Interpretation:\*\* [What the Domain Expert said about the verdict and next direction]



\### D. Requirement Verification

| Linked Requirement | PRD Target | Actual Achieved | Status |
| :--- | :--- | :--- | :--- |
| \`REQ-PERF-01\` | [Target] | [Actual] | [PASS/FAIL] |



\### E. Failed Attempts ❌ — MANDATORY

| Approach / Config | Symptom | Root Cause | Lesson Learned |
| :--- | :--- | :--- | :--- |
| [What was tried] | [Observable outcome] | [Why] | [What to do differently] |



\### F. Error Analysis & Domain Cost

\* \*\*Common Failure Modes:\*\* [Confusion matrix hotspots, per-class breakdown]
\* \*\*Domain Cost of Failures:\*\* [Apply failure costs from Thesis Section III to actual error counts — e.g., "38 false negatives × $50K cost = $1.9M potential recall cost"]
\* \*\*Data/Feature Behavior:\*\* [Feature importance, gradient issues, distribution effects]



\### G. Diagnostics & Insights

\* [Training curve analysis: overfitting, underfitting, convergence behavior]
\* [Comparison to EDA predictions: did the data behave as expected?]



\### H. Recommendations for Next Step

\* [If HPO eligible: specific parameter ranges to sweep based on results]
\* [If revision needed: which upstream documents need changing and why]
\* [New hypothesis candidate with domain reasoning]



\### I. Clarification & Decision Log

\* \*\*Q1:\*\* [Your question] -> \*\*User Decision:\*\* [User's answer]

\`\`\`
