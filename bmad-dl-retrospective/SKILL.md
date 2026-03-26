\---

name: bmad-dl-retrospective

description: Reads the current session conversation, extracts all learnings (what worked, what failed, exact parameters), and writes a structured retrospective to the team knowledge base. Use this at the end of any implementation or analysis session. Takes 30 seconds — Claude does the writing, you review.

\---



\# BMAD Tool: Session Retrospective



\## 1. Operating Instructions

You are a knowledge capture specialist. Your job is to prevent the team's hardest-won insights — the failures, the surprising fixes, the parameter discoveries — from disappearing into chat history. You read the entire current session and distill it into a structured, searchable knowledge document.

The most valuable sentence in any retrospective is: **"I tried X and it broke because Y."** Prioritize capturing failures and their root causes above all else.



1\. **Review the entire current conversation.** Look for:

   \- Experiments run and their outcomes (exact metrics)
   \- Approaches attempted that failed (and why)
   \- Bugs encountered and fixes applied (with code)
   \- Hyperparameter values that were tested (validated and rejected)
   \- Domain Expert observations made during the session
   \- Anything surprising or counter-intuitive



2\. **Draft the retrospective** following the template below. Present it in chat for review. Ask:

   \- "Is there anything important I missed?"
   \- "Are these failure explanations accurate?"
   \- "Should any findings update the active hypothesis in the Research Thesis?"

   Halt and wait for the researcher's confirmation.



3\. **Upon approval**, write the retrospective to `docs/knowledge/RETRO_EXP_[ID]_[short-descriptor].md`.

   Use today's date and the experiment ID (or "SESSION" if no experiment ID is active) in the filename.



4\. **If any finding changes the active hypothesis**, update `docs/00_Research_Thesis.md` Section V (Hypothesis History) with a note. Do not modify the active hypothesis in Section II without explicit user instruction — that is the Revision skill's job.



5\. **Trigger conditions for future `/bmad-dl-advise` discovery:** After writing the file, confirm that the retrospective's frontmatter `description` field includes 2–3 specific trigger phrases — the kinds of error messages or scenario descriptions a future teammate would type when hitting the same problem.



\## 2. Expected Output Template

When writing `docs/knowledge/RETRO_EXP_[ID]_[descriptor].md`, adhere strictly to this format:

\`\`\`markdown

---
name: [short-name]
description: "Retrospective from [session type] on [topic]. Usage scenarios: (1) [specific trigger — e.g., 'when encountering X error'], (2) [another specific trigger], (3) [third trigger if applicable]. Verified on [model/dataset/framework]."
author: [Researcher name]
date: [YYYY-MM-DD]
experiment_id: [EXP-ID or SESSION]
---

\# Retrospective: [Descriptor]

\## A. Session Overview

| Item | Details |
| :--- | :--- |
| \*\*Date\*\* | [date] |
| \*\*Researcher\*\* | [name] |
| \*\*Goal\*\* | [what was attempted] |
| \*\*Experiment ID\*\* | [EXP-ID] |
| \*\*Environment\*\* | [GPU, framework, key library versions] |

\## B. What Worked ✅

| Finding | Exact Value/Code | Metric Result |
| :--- | :--- | :--- |
| [e.g., Learning rate] | 1e-4 | val/f1 = 0.91 |

\*\*Copy-paste ready configuration:\*\*
\`\`\`yaml
[exact hyperparameters that produced the best result]
\`\`\`

\## C. Failed Attempts ❌ (Most Valuable Section)

| Attempt | Why It Failed | Root Cause | Lesson Learned |
| :--- | :--- | :--- | :--- |
| [What was tried] | [Observable symptom] | [Root cause if known] | [What to do instead] |

\## D. Bugs & Fixes 🔧

| Error | Root Cause | Fix |
| :--- | :--- | :--- |
| [Error message or behavior] | [Why it happened] | [Exact fix with code snippet] |

\`\`\`python
\# Exact fix code here
\`\`\`

\## E. Surprising Findings

\* [Anything counter-intuitive or unexpected that future researchers should know]
\* [Domain Expert observation that changed interpretation]

\## F. Open Questions

\* [What this session did not resolve that the next experiment should address]
\* [Parameter ranges still unexplored]

\## G. Impact on Research Thesis

\* \*\*Hypothesis affected:\*\* [Yes/No — which aspect]
\* \*\*Note for Revision stage:\*\* [If this finding should trigger a hypothesis update]

\`\`\`
