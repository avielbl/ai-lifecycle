#!/usr/bin/env python3
"""
build_notebook.py — BMAD AI Lifecycle (Stage 2 — EDA)
Programmatically builds the EDA notebook skeleton (`notebooks/eda_report.ipynb`)
with nbformat: markdown cells for narrative, code cells that call the importable
functions of the EDA suite (eda_analyzer, class_weights_calculator,
clustering_explorer, baseline_classifier).

Designed for CSV/tabular datasets. For other formats (image dirs, npy, hdf5),
generate the skeleton and adapt the data-loading cells before executing.

No project installs required — run via ephemeral environments:

    uv run --with nbformat python scripts/build_notebook.py data/features.csv \
        --output notebooks/eda_report.ipynb

Then execute headlessly so committed output includes rendered plots/tables:

    uv run --with jupyter --with nbformat --with pandas --with scikit-learn --with matplotlib \
        jupyter nbconvert --to notebook --execute --inplace notebooks/eda_report.ipynb

Exit codes:
    0 — success, notebook written
    2 — error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import nbformat
    from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False


# ── Cell sources ───────────────────────────────────────────────────────────────
# Only the setup cell is parameterized; all other cells are static so the
# skeleton stays deterministic and easy to diff.

SETUP_SRC = """\
import sys
from pathlib import Path

DATA_PATH = Path({data_path!r})
SCRIPTS_DIR = Path({scripts_dir!r})
LABEL_COL = {label_col!r}  # None = auto-detect

sys.path.insert(0, str(SCRIPTS_DIR))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(DATA_PATH)

_candidates = ("label", "class", "target", "y", "category")
label_col = LABEL_COL or next((c for c in df.columns if c.lower() in _candidates), None)
numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != label_col]

print(f"Loaded {{df.shape[0]:,}} rows x {{df.shape[1]}} columns from {{DATA_PATH}}")
print(f"Label column: {{label_col}} | Numeric features: {{len(numeric_cols)}}")\
"""

OVERVIEW_SRC = """\
overview = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "non_null": df.notna().sum(),
    "unique": df.nunique(),
})
display(df.head())
overview\
"""

MISSINGNESS_SRC = """\
missing = df.isna().sum().rename("missing").to_frame()
missing["pct"] = (missing["missing"] / len(df) * 100).round(2)
missing = missing.sort_values("missing", ascending=False)
if missing["missing"].sum() == 0:
    print("No missing values detected.")
else:
    ax = missing.loc[missing["missing"] > 0, "pct"].plot.bar(
        figsize=(8, 3), title="Missing values per column (%)")
    ax.set_ylabel("% missing")
    plt.tight_layout()
missing\
"""

DISTRIBUTIONS_SRC = """\
if numeric_cols:
    df[numeric_cols].hist(bins=30, figsize=(12, 3 * ((len(numeric_cols) + 2) // 3)))
    plt.suptitle("Numeric feature distributions")
    plt.tight_layout()
    display(df[numeric_cols].describe().T)
else:
    print("No numeric feature columns - skipping distributions.")\
"""

CORRELATIONS_SRC = """\
if len(numeric_cols) >= 2:
    corr = df[numeric_cols].corr()
    side = 0.6 * len(numeric_cols) + 3
    fig, ax = plt.subplots(figsize=(side, side - 1))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns)
    fig.colorbar(im, ax=ax, label="Pearson r")
    ax.set_title("Correlation heatmap")
    plt.tight_layout()
else:
    print("Fewer than two numeric columns - skipping correlation heatmap.")\
"""

CLASS_BALANCE_SRC = """\
if label_col is not None:
    from class_weights_calculator import compute_weights

    counts = df[label_col].astype(str).value_counts()
    ax = counts.plot.bar(figsize=(6, 3), title=f"Class balance - {label_col}")
    ax.set_ylabel("count")
    plt.tight_layout()

    weights = compute_weights({k: int(v) for k, v in counts.items()})
    balance = pd.DataFrame({
        "count": counts,
        "pct": (counts / counts.sum() * 100).round(2),
        "balanced_weight": pd.Series(weights),
    })
    display(balance)
    print(f"Imbalance ratio (majority:minority): {counts.max() / counts.min():.1f}:1")
else:
    print("No label column detected - skipping class balance.")\
"""

OUTLIERS_SRC = """\
if numeric_cols:
    rows = []
    for col in numeric_cols:
        s = df[col].dropna()
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_out = int(((s < lo) | (s > hi)).sum())
        rows.append({"feature": col, "outliers_iqr": n_out,
                     "pct": round(n_out / max(len(s), 1) * 100, 2)})
    outliers = pd.DataFrame(rows).sort_values("outliers_iqr", ascending=False)
    df[numeric_cols].plot.box(figsize=(10, 4), rot=90, title="Feature boxplots (IQR outliers)")
    plt.tight_layout()
    display(outliers)
else:
    print("No numeric feature columns - skipping outlier analysis.")\
"""

CLUSTERING_SRC = """\
try:
    import matplotlib
    _backend = matplotlib.get_backend()
    from clustering_explorer import load_numeric_csv, preprocess, run_clustering
    plt.switch_backend(_backend)  # clustering_explorer forces Agg on import; restore inline
    from sklearn.decomposition import PCA

    X_raw, cluster_features = load_numeric_csv(DATA_PATH)
    X = preprocess(X_raw)
    cluster_results = run_clustering(X, n_clusters=3)
    display(pd.DataFrame([{
        "algorithm": r.name,
        "clusters": r.n_clusters,
        "silhouette": r.silhouette,
        "calinski_harabasz": r.calinski,
        "davies_bouldin": r.davies,
        "noise_points": r.n_noise,
        "notes": r.notes,
    } for r in cluster_results]))

    X_2d = PCA(n_components=2).fit_transform(X)
    scored = [r for r in cluster_results if r.silhouette is not None]
    best = max(scored, key=lambda r: r.silhouette) if scored else cluster_results[0]
    labels = np.array(best.labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap="tab10", s=15, alpha=0.7)
    ax.set_title(f"{best.name} clusters - PCA projection")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    plt.tight_layout()
except Exception as exc:
    print(f"Clustering exploration skipped: {exc}")\
"""

BASELINE_SRC = """\
try:
    from baseline_classifier import load_csv, _to_numeric_matrix, run_baseline
    from sklearn.preprocessing import LabelEncoder

    feature_names, X_rows, y_raw = load_csv(DATA_PATH, label_col)
    X_base, base_features = _to_numeric_matrix(X_rows, feature_names)
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    baseline_results = run_baseline(X_base, y, base_features, [str(c) for c in le.classes_])
    display(pd.DataFrame([{
        "model": r.name,
        "cv_f1_mean": round(r.cv_mean, 4),
        "cv_f1_std": round(r.cv_std, 4),
        "test_accuracy": round(r.test_accuracy, 4),
        "test_f1": round(r.test_f1, 4),
        "test_precision": round(r.test_precision, 4),
        "test_recall": round(r.test_recall, 4),
        "roc_auc": round(r.roc_auc, 4) if r.roc_auc is not None else None,
    } for r in baseline_results]))
    print(f"Performance floor (best baseline): "
          f"{baseline_results[0].name} - weighted F1 {baseline_results[0].test_f1:.4f}")
except Exception as exc:
    print(f"Baseline skipped: {exc}")\
"""


SECTION_TITLES = [
    "1. Data Overview",
    "2. Missingness",
    "3. Feature Distributions",
    "4. Correlations",
    "5. Class Balance",
    "6. Outliers",
    "7. Clustering Exploration",
    "8. Baseline Results",
]


def build_notebook(data_path: Path, scripts_dir: Path | None = None,
                   label_col: str | None = None) -> "nbformat.NotebookNode":
    """Return an nbformat v4 notebook mirroring the EDA_Report.md sections."""
    if not HAS_NBFORMAT:
        raise RuntimeError("nbformat is required. Run via: uv run --with nbformat python ...")

    scripts_dir = (scripts_dir or Path(__file__).parent).resolve()
    # Embed absolute paths: headless executors (nbconvert/jupyter execute) run
    # with the notebook's own directory as cwd, so relative paths would break.
    data_path = Path(data_path).resolve()

    setup_src = SETUP_SRC.format(
        data_path=str(data_path),
        scripts_dir=str(scripts_dir),
        label_col=label_col,
    )

    cells = [
        new_markdown_cell(
            f"# EDA Report Notebook\n\n"
            f"Dataset: `{data_path}`\n\n"
            f"Visual companion to the markdown EDA Report "
            f"(`{{ai_output_folder}}/eda/EDA_Report.md`). Built programmatically with "
            f"`nbformat` and executed headlessly — Stage 2 of the BMAD AI Lifecycle."
        ),
        new_code_cell(setup_src),
        new_markdown_cell("## 1. Data Overview\n\nShape, schema, and per-column summary."),
        new_code_cell(OVERVIEW_SRC),
        new_markdown_cell("## 2. Missingness\n\nMissing values per column."),
        new_code_cell(MISSINGNESS_SRC),
        new_markdown_cell("## 3. Feature Distributions\n\nHistograms and summary statistics for numeric features."),
        new_code_cell(DISTRIBUTIONS_SRC),
        new_markdown_cell("## 4. Correlations\n\nPearson correlation heatmap of numeric features."),
        new_code_cell(CORRELATIONS_SRC),
        new_markdown_cell("## 5. Class Balance\n\nLabel distribution and recommended balanced class weights."),
        new_code_cell(CLASS_BALANCE_SRC),
        new_markdown_cell("## 6. Outliers\n\nIQR-based outlier counts and boxplots per numeric feature."),
        new_code_cell(OUTLIERS_SRC),
        new_markdown_cell("## 7. Clustering Exploration\n\nUnsupervised structure — K-Means, Agglomerative, DBSCAN with PCA projection."),
        new_code_cell(CLUSTERING_SRC),
        new_markdown_cell("## 8. Baseline Results\n\nClassical ML performance floor (LR, RF, Gradient Boosting)."),
        new_code_cell(BASELINE_SRC),
        new_markdown_cell(
            "## 9. Summary\n\n"
            "*Fill in after execution:* key findings, risks, and implications for architecture. "
            "The authoritative narrative lives in the markdown EDA Report."
        ),
    ]

    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    nb.metadata["language_info"] = {"name": "python"}
    return nb


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the EDA notebook skeleton with nbformat")
    parser.add_argument("data_path", type=Path, help="Path to the dataset CSV")
    parser.add_argument("--output", type=Path, default=Path("notebooks/eda_report.ipynb"),
                        help="Output notebook path (default: notebooks/eda_report.ipynb)")
    parser.add_argument("--label-col", type=str, default=None,
                        help="Label column name (default: auto-detect)")
    parser.add_argument("--scripts-dir", type=Path, default=None,
                        help="Directory containing the EDA scripts (default: this file's directory)")
    args = parser.parse_args()

    if not HAS_NBFORMAT:
        print("Error: nbformat not available. Run via: "
              "uv run --with nbformat python scripts/build_notebook.py ...", file=sys.stderr)
        return 2
    if not args.data_path.exists():
        print(f"Error: Path not found: {args.data_path}", file=sys.stderr)
        return 2

    nb = build_notebook(args.data_path, args.scripts_dir, args.label_col)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(args.output))

    print(f"✓ Notebook skeleton written to: {args.output}")
    print("  Execute headlessly with:")
    print("  uv run --with jupyter --with nbformat --with pandas --with scikit-learn --with matplotlib \\")
    print(f"      jupyter nbconvert --to notebook --execute --inplace {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
