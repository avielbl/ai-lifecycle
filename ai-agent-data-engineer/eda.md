# Capability: Exploratory Data Analysis (EDA)

## Overview
This capability allows the agent to deeply understand the data before any architectural decisions are made. It establishes a performance floor and identifies data quality issues.

## Operating Instructions
1. **Read the Research Thesis first:** Locate and read `docs/00_Research_Thesis.md`. Understand the research question framed by the Domain Expert.
2. **Locate the data:** If not already found, ask for the data path and format.
3. **Execute EDA Suite:** Run the scripts in `scripts/`:
   - `eda_analyzer.py`: Analyze distributions and splits.
   - `baseline_classifier.py`: Establish the performance floor.
   - `class_weights_calculator.py`: Handle imbalances.
4. **Dialogue with Domain Expert:** Present findings to the user (acting as or conveying to the Domain Expert) to interpret anomalies in domain terms.
5. **Output Report:** Generate `docs/eda/02_EDA_Report.md`.
6. **Update Thesis:** Update Section IV of `docs/00_Research_Thesis.md` with the findings.

## Output Template
(Refer to the template in the original ai-lifecycle EDA documentation for `02_EDA_Report.md`)
