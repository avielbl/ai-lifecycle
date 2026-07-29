# Capability: Exploratory Data Analysis (EDA)

## Overview
This capability allows the agent to deeply understand the data before any architectural decisions are made. It establishes a performance floor and identifies data quality issues.

The stage produces **two artifacts**:

1. `{ai_output_folder}/eda/EDA_Report.md` — the markdown lifecycle document that downstream stages (Architecture, Detailed Design) read.
2. `notebooks/eda_report.ipynb` — an **executed** Jupyter notebook with rendered plots and tables mirroring the report sections, for visual review.

> **No project installs at this stage.** EDA is Stage 2 — the first `uv sync` happens in Infrastructure (Stage 5). Run all Python tooling through ephemeral environments (`uv run --with <pkg> ...` or `uvx`). Never run `uv add`, `uv sync`, or `pip install` here.

## Operating Instructions
1. **Read the Research Thesis first:** Locate and read `docs/Research_Thesis.md`. Understand the research question framed by the Domain Expert.
2. **Locate the data:** If not already found, ask for the data path and format.
3. **Execute EDA Suite:** Run the scripts in `scripts/` via ephemeral environments:
   - `eda_analyzer.py`: Analyze distributions and splits — `uv run --with numpy --with pillow python scripts/eda_analyzer.py <data_path>`
   - `baseline_classifier.py`: Establish the performance floor — `uv run --with numpy --with scikit-learn python scripts/baseline_classifier.py <data_csv>`
   - `class_weights_calculator.py`: Handle imbalances — `python3 scripts/class_weights_calculator.py <data_path>` (stdlib only)
   - `clustering_explorer.py` (optional): Discover natural groupings — `uv run --with numpy --with scikit-learn --with matplotlib python scripts/clustering_explorer.py <data_csv> --find-k`
4. **Dialogue with Domain Expert:** Present findings to the user (acting as or conveying to the Domain Expert) to interpret anomalies in domain terms.
5. **Write the EDA Report:** Generate `{ai_output_folder}/eda/EDA_Report.md` (template below). Include a pointer to the notebook: *"Full visual analysis in `notebooks/eda_report.ipynb`."*
6. **Build the notebook programmatically:** Do not hand-edit JSON — build `notebooks/eda_report.ipynb` with `nbformat` (markdown cells for narrative, code cells that import the scripts' functions — `analyze`, `run_baseline`, `compute_weights`, `run_clustering` — rather than shelling out). Use the provided generator:

   ```bash
   uv run --with nbformat python scripts/build_notebook.py <data_csv> \
       --label-col <label> --output notebooks/eda_report.ipynb
   ```

   The generator targets CSV/tabular data. For other formats (image dirs, npy, hdf5), generate the skeleton and adapt the data-loading cells before executing. To extend or customize sections, follow the same pattern:

   ```python
   import nbformat
   from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

   nb = new_notebook(cells=[
       new_markdown_cell("## 5. Class Balance"),
       new_code_cell(
           "from class_weights_calculator import compute_weights\n"
           "counts = df['label'].value_counts()\n"
           "counts.plot.bar(title='Class balance')\n"
           "compute_weights({k: int(v) for k, v in counts.items()})"
       ),
   ])
   nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
   nbformat.write(nb, "notebooks/eda_report.ipynb")
   ```

7. **Execute the notebook headlessly** so the committed file contains rendered plots and tables:

   ```bash
   uv run --with jupyter --with nbformat --with pandas --with scikit-learn --with matplotlib \
       jupyter nbconvert --to notebook --execute --inplace notebooks/eda_report.ipynb
   ```

   Then verify: no cell errors, plots rendered (histograms, correlation heatmap, class balance bar chart, clustering projection), tables populated.
8. **Review Gate:** STOP after writing both artifacts. Present a summary of findings and wait for the user's approval. The gate covers **both** the markdown report and the executed notebook — do not proceed until both are approved.
9. **Update Thesis:** After approval, update Section IV of `docs/Research_Thesis.md` with the findings.

## Output Template

`{ai_output_folder}/eda/EDA_Report.md` should contain:

1. **Dataset Summary** — source, size, schema, splits (train/val/test counts and proportions).
2. **Distributions** — per-feature summary statistics, label/class distribution, imbalance ratios.
3. **Data Quality** — missingness, duplicates, outliers, leakage checks, label noise indicators.
4. **Baseline Performance** — metrics from `baseline_classifier.py` (the performance floor a model must beat).
5. **Recommended Class Weights** — output of `class_weights_calculator.py`, if classification.
6. **Findings & Risks** — anomalies, domain-relevant flags, and open questions for the Domain Expert.
7. **Implications for Architecture** — concrete asks/constraints to feed the Researcher in Stage 3.
8. **Notebook Reference** — "Full visual analysis in `notebooks/eda_report.ipynb`."

`notebooks/eda_report.ipynb` (executed, with output cells committed) should mirror the report with these sections:

1. **Data Overview** — shape, schema, head, per-column summary table.
2. **Missingness** — missing counts/percentages table and bar chart.
3. **Feature Distributions** — histograms plus `describe()` table.
4. **Correlations** — Pearson correlation heatmap.
5. **Class Balance** — label bar chart, counts table, balanced class weights.
6. **Outliers** — IQR outlier counts table and boxplots.
7. **Clustering Exploration** — algorithm comparison table and PCA scatter.
8. **Baseline Results** — model comparison table and the performance floor.
