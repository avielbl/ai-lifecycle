# Capability: Experiment Analysis

## Overview
Interprets experiment results against the TECHSPEC acceptance gates, design document, and research thesis. Analyzes root causes of failures, captures lessons learned, and recommends follow-up experiments. This is the single decision-making document for whether to proceed, pivot, or retry. Subsumes the retrospective — failed attempts and infrastructure lessons are part of the analysis, not a separate doc.

## Operating Instructions
1. **Inputs:** Read TECHSPEC, RUN log, and RESULTS from `{ai_output_folder}/experiments/{ID}/`.
2. **Verdict:** State pass/fail for each acceptance tier at the top. Link back to TECHSPEC gates.
3. **Interpretation:** Discuss what the results mean in context of the research thesis and design goals. Go beyond the numbers.
4. **Root cause analysis:** For any failing arm or unexpected result, analyze why. Consider: data scale, model capacity, hyperparameters, preprocessing.
5. **What went wrong:** Document every failed attempt, workaround, and root cause encountered during execution. Include the fix and a generalizable rule.
6. **Parameters validated:** Table of hyperparameters confirmed to work.
7. **Infrastructure lessons:** Tooling, compute, pipeline learnings.
8. **Confounds and limitations:** What could have biased the results.
9. **Next steps:** Priority-ordered actions for the next experiment. Each should trace to a specific finding. **Ask, don't guess:** when results support more than one interpretation or next step, present the options with a brief recommendation and let the user decide.
10. **Output:** `{ai_output_folder}/experiments/{ID}/ANALYSIS_{timestamp}.md`
11. **Review Gate:** Stop. Summarize the verdict and next steps, ask the user to review and comment, and wait for explicit approval before any handoff (revision-audit or hparam).

## Template Sections
- Verdict (tier table at top — pass/fail with deltas)
- Interpretation by Modality / Task
- Root Cause Analysis (for failures)
- What Went Wrong (numbered failed attempts with fixes and rules)
- Parameters Validated
- Infrastructure Lessons
- Confounds and Limitations
- Next Steps for E-{N+1} (priority-ordered, traceable)
