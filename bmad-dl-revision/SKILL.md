\---

name: bmad-dl-revision

description: Acts as a Domain Expert and AI Tech Lead to formulate the next hypothesis, explicitly amend all upstream documents (Thesis, PRD, Architecture, Detailed Design) that need updating, and generate the task set for the next experiment cycle.

\---



\# BMAD Workflow 08: Iterative Revision Cycle



\## 1. Operating Instructions

You are the Domain Expert and AI Tech Lead. The Domain Expert drives *why* (what domain insight leads to the next hypothesis), while the Tech Lead drives *what* (which documents change and how).

A revision is not just a hypothesis update. It is a **document audit**: every upstream document that no longer accurately reflects what was learned must be explicitly amended. The next experiment cycle starts from corrected documents, not from documents that have drifted from reality.



1\. **Summarize experiment history:**

\`\`\`bash

python3 _bmad/bmad-dl-lifecycle/bmad-dl-revision/scripts/summarize_experiment_history.py docs/experiments/ --metric val/f1 --mode max
\# Also scan logs:
python3 _bmad/bmad-dl-lifecycle/bmad-dl-revision/scripts/summarize_experiment_history.py logs/ --metric val/loss --top 10 2>/dev/null || true

\`\`\`



2\. **Read in order:**

   \- `docs/00_Research_Thesis.md` — active hypothesis, hypothesis history, domain constraints
   \- `docs/experiments/07_Analysis_EXP_[ID].md` — hypothesis verdict, TECHSPEC evaluation, recommendations
   \- `docs/techspecs/TECHSPEC_EXP_[ID].md` — which tier was committed and reached
   \- `docs/prd/01_PRD.md` — are any requirements outdated by what was learned?
   \- `docs/architecture/03_Architecture.md` — are any architectural decisions invalidated?
   \- `docs/design/04_Detailed_Design.md` — which tasks need to be added, changed, or removed?



3\. **Conduct the document audit.** For each upstream document, state one of:

   \- **No change needed** — with explicit reason why
   \- **Amendment needed** — with the exact proposed change



4\. **Formulate the next hypothesis** as a domain-grounded, testable statement:

   \- Format: "Using [specific change] will improve [metric] from [current baseline] to [target] because [domain or statistical reasoning from this experiment's results]."
   \- The hypothesis must be falsifiable. State what result would disprove it.



5\. **Generate new tasks** for the next cycle using the correct namespace:

   \- New infrastructure tasks → `INF-0XX` (if architecture changes require new infrastructure)
   \- New experiment tasks → `EXP-0XX` (increment from last used EXP number)

   Note: if the hypothesis was falsified and only a parameter change is needed, only EXP tasks are required. If the architecture must change, new INF tasks may be needed first.



6\. **CRITICAL:** Do not execute any changes yet. Present the full revision plan to the user:

   \- Experiment history table
   \- Hypothesis verdict
   \- Document audit (each doc: change or no change, with detail)
   \- New hypothesis with domain reasoning
   \- New task list

   Ask: "Does this amendment plan accurately capture the conclusions? Are there domain insights from this experiment I haven't included?" Halt and wait.



7\. Upon approval, execute all changes:

   \- Apply all document amendments (in order: Thesis → PRD → Architecture → Detailed Design)
   \- Append to `docs/revisions/08_Revision_Log.md`



\## 2. Expected Output Templates



\### Template A: Document Amendment to `docs/00_Research_Thesis.md`

\- Section II: Replace active hypothesis. Set status to "Untested — pending next experiment."
\- Section V: Append the previous hypothesis row:

\`\`\`markdown
| H-00N | "[Previous hypothesis]" | EXP-00X | [SUPPORTED/FALSIFIED/INCONCLUSIVE — one sentence] | [Domain Expert] / [Date] |
\`\`\`



\### Template B: Append to `docs/revisions/08_Revision_Log.md`

\`\`\`markdown

\### Revision Cycle [N]: [Date]

\* \*\*Triggered By:\*\* EXP-[ID]
\* \*\*Previous Hypothesis Verdict:\*\* [SUPPORTED / FALSIFIED / INCONCLUSIVE]
\* \*\*TECHSPEC Tier Reached:\*\* [Tier name]
\* \*\*Domain Expert Assessment:\*\* [Why the hypothesis outcome occurred, in domain terms]

\### New Hypothesis

\* \*\*H-00N:\*\* "[New hypothesis — domain-grounded, falsifiable]"
\* \*\*Rationale:\*\* [Domain expert reasoning + statistical evidence]
\* \*\*Falsification condition:\*\* [What result would disprove this hypothesis]

\### Document Amendment Log

\#### `docs/00_Research_Thesis.md`
\* Section II updated: new hypothesis set, old hypothesis archived to Section V

\#### `docs/prd/01_PRD.md`
\* [AMENDED: specific change] OR [No change — existing requirements still accurate]

\#### `docs/architecture/03_Architecture.md`
\* [AMENDED: specific change] OR [No change — architecture still valid for next experiment]

\#### `docs/design/04_Detailed_Design.md`
\* [AMENDED: tasks added/removed — with IDs] OR [No change — existing task set sufficient]

\### New Task Generation

| Task ID | Assigned Agent | Description | Linked Req | Depends On |
| :--- | :--- | :--- | :--- | :--- |
| \`EXP-0XX\` | [Agent] | [Training run with new hypothesis] | [REQ-ID] | TECHSPEC_EXP_[N+1] |
| \`INF-0XX\` | [Agent] | [New infra if architecture changed] | [REQ-ID] | None |

\### Clarification & Decision Log

\* \*\*Q1:\*\* [Your question] -> \*\*User Decision:\*\* [User's answer]
\* \*\*Status:\*\* [Approved — ready for bmad-dl-techspec then bmad-dl-experiment]

\`\`\`
