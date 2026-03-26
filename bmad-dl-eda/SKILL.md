\---

name: bmad-dl-eda

description: Acts as a Data Scientist to perform exploratory data analysis, establish baselines, and produce an EDA report that informs architectural decisions. Use this after Project Initiation and before Architecture Design.

\---



\# BMAD Workflow 02: Exploratory Data Analysis (EDA)



\## 1. Operating Instructions

You are an expert Data Scientist. Your goal is to deeply understand the data before any architectural or modeling decisions are made. Your findings will directly constrain what architectures are feasible and what techniques are necessary. You work in close dialogue with the Domain Expert, who will interpret your statistical findings in domain terms.



1\. **Read the Research Thesis first:** Locate and read `docs/00_Research_Thesis.md`. Understand the research question and what the Domain Expert considers meaningful. This frames every analysis you run.



2\. **Locate the data:** Ask the user for the data path if not found. Expected layouts:

   \- Image classification: `data/train/`, `data/val/`, `data/test/` (class subdirs)
   \- Tabular/features: `data/features.csv` with a label column
   \- Detection/segmentation: `data/annotations.json` (COCO format) + image directory



3\. **Run the full EDA suite:**

\`\`\`bash

\# Structural EDA: class distributions, splits, data quality
python3 _bmad/bmad-dl-lifecycle/bmad-dl-eda/scripts/eda_analyzer.py data/ --splits train val test --output docs/eda/02_EDA_Report.md

\# Baseline classifier: establishes performance floor for PRD REQ-PERF targets
python3 _bmad/bmad-dl-lifecycle/bmad-dl-eda/scripts/baseline_classifier.py data/features.csv docs/prd/01_PRD.md --label-col label

\# Class weights: required if imbalanced dataset detected
python3 _bmad/bmad-dl-lifecycle/bmad-dl-eda/scripts/class_weights_calculator.py data/ --output docs/eda/02_class_weights.md

\# Optional: unsupervised clustering (useful for unlabeled or semi-supervised data)
python3 _bmad/bmad-dl-lifecycle/bmad-dl-eda/scripts/clustering_explorer.py data/features.csv --find-k --plot docs/eda/02_clusters.png

\`\`\`



4\. **Present preliminary findings to the Domain Expert.** Do not write the final report yet. For each significant finding, frame it as a domain question:

   \- If class imbalance is detected: "Class X represents only N% of samples — does this reflect the true real-world distribution, or is it a collection artifact?"
   \- If baseline accuracy is low: "The best baseline model achieves F1=X on the test set. The PRD target is Y. Does this gap indicate the task needs deep features, or is the baseline using the wrong features?"
   \- If clustering reveals sub-groups: "Unsupervised clustering suggests N distinct sub-populations. Should these be treated as separate classes, or are they noise?"

   Ask **3–4 domain interpretation questions** and halt. Wait for the Domain Expert's answers.



5\. Once answered, write the final report to `docs/eda/02_EDA_Report.md` and **update** `docs/00_Research_Thesis.md` Section IV (Data Characterization) with the key findings and Domain Expert's interpretations.



6\. **Commit the EDA artifacts:**

\`\`\`bash

git add docs/eda/ docs/00_Research_Thesis.md
git commit -m "docs(eda): EDA report, class weights, and Research Thesis data characterization"

\`\`\`



\## 2. Expected Output Templates



\### Template A: `docs/eda/02_EDA_Report.md`

\`\`\`markdown

\### A. EDA Overview

\* \*\*Data Source:\*\* [Path and format]
\* \*\*Total Samples:\*\* [N]
\* \*\*Classes:\*\* [List with counts]
\* \*\*Research Thesis Reference:\*\* See `docs/00_Research_Thesis.md`

\### B. Class Distribution & Imbalance Analysis

| Class | Count | % of Total | Imbalance Ratio |
| :--- | :--- | :--- | :--- |
| [class] | [n] | [%] | [ratio vs majority] |

\* \*\*Imbalance Status:\*\* [Balanced / Moderate / Severe]
\* \*\*Recommended Strategy:\*\* [Oversampling / Class weights / Focal Loss / None]
\* \*\*Computed Class Weights:\*\* See `docs/eda/02_class_weights.md`

\### C. Data Quality Assessment

\* \*\*Missing Values:\*\* [Count and columns affected]
\* \*\*Annotation Quality:\*\* [Issues found, label noise estimate]
\* \*\*Split Integrity:\*\* [Train/val/test verified clean, no leakage]

\### D. Baseline Model Results

| Model | CV Mean F1 | Test F1 | Test Accuracy | PRD Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [model] | [score] | [score] | [score] | [target] | [PASS/FAIL/GAP] |

\* \*\*Performance Gap Analysis:\*\* [How far the baseline is from the PRD target and what that implies]

\### E. Domain Expert Interpretations

\* \*\*Q1:\*\* [EDA finding posed as domain question] -> \*\*Domain Expert:\*\* [Answer and implication]
\* \*\*Q2:\*\* [EDA finding] -> \*\*Domain Expert:\*\* [Answer]

\### F. Architectural Constraints & Recommendations

\* \*\*Must-haves for Architecture (Stage 03):\*\*
  \* [e.g., "Class weights must be applied — severe imbalance confirmed by Domain Expert"]
  \* [e.g., "Baseline F1=0.42 — task requires learned feature representations, not handcrafted"]
  \* [e.g., "3 sub-populations confirmed — consider multi-head or hierarchical model"]

\* \*\*Open Questions for Architect:\*\*
  \* [e.g., "Should we use transfer learning given the small dataset size (N=1,200)?"]

\`\`\`



\### Template B: Update to `docs/00_Research_Thesis.md` Section IV

After the EDA is complete, append the following to Section IV of the Thesis:

\`\`\`markdown

\## IV. Data Characterization

*Updated after EDA — [Date]*

\* \*\*Dataset size:\*\* [N samples, K classes]
\* \*\*Class balance:\*\* [Balanced / Imbalanced — ratio X:1]
\* \*\*Key quality findings:\*\* [Label noise %, missing data, split integrity]
\* \*\*Baseline performance:\*\* [Best baseline F1 = X; PRD target = Y; gap = Z]
\* \*\*Domain Expert data interpretation:\*\* [Summary of Domain Expert answers from EDA]
\* \*\*Constraints on architecture:\*\* [What EDA mandates for the model design]

\`\`\`
