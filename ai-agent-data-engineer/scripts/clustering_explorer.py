#!/usr/bin/env python3
"""
clustering_explorer.py — BMAD DL Lifecycle
(Inspired by K-Dense claude-scientific-skills/scikit-learn/clustering_analysis.py)

Unsupervised cluster analysis for EDA on unlabeled or partially-labeled datasets.
Useful during TSK-001 to discover natural groupings before annotation or labeling.

Runs K-Means, Agglomerative, and DBSCAN; scores with Silhouette, Calinski-Harabasz,
and Davies-Bouldin indices; optionally saves a PCA 2D scatter plot.

Usage:
    python3 scripts/clustering_explorer.py <data_csv> [--k N] [--find-k] [--output report.md] [--plot clusters.png]
    python3 scripts/clustering_explorer.py data/features.csv --find-k --plot clusters.png

Exit codes:
    0 — success
    2 — error
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
    from sklearn.impute import SimpleImputer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class ClusterResult:
    name: str
    n_clusters: int
    silhouette: float | None
    calinski: float | None
    davies: float | None
    labels: "list | None" = None
    n_noise: int = 0
    notes: str = ""


# ── Data loading ───────────────────────────────────────────────────────────────

def load_numeric_csv(path: Path) -> tuple["np.ndarray", list[str]]:
    """Load CSV, drop non-numeric and label columns, return (X, feature_names)."""
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV is empty")

    columns = list(rows[0].keys())
    # Exclude likely label columns
    label_cols = {c for c in columns if c.lower() in ("label", "class", "target", "y", "category")}

    numeric_cols: list[str] = []
    for col in columns:
        if col in label_cols:
            continue
        try:
            [float(row[col]) for row in rows if row.get(col, "").strip()]
            numeric_cols.append(col)
        except ValueError:
            pass

    if not numeric_cols:
        raise ValueError("No numeric feature columns found")

    X = np.array([
        [float(row[c]) if row.get(c, "").strip() else float("nan") for c in numeric_cols]
        for row in rows
    ], dtype=float)
    return X, numeric_cols


def preprocess(X: "np.ndarray") -> "np.ndarray":
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    return scaler.fit_transform(imputer.fit_transform(X))


# ── Optimal K search ───────────────────────────────────────────────────────────

def find_optimal_k(X: "np.ndarray", k_range: range) -> tuple[int, list[float], list[float]]:
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X, labels))
    best_k = list(k_range)[int(np.argmax(silhouettes))]
    return best_k, inertias, silhouettes


# ── Clustering ─────────────────────────────────────────────────────────────────

def run_clustering(X: "np.ndarray", n_clusters: int) -> list[ClusterResult]:
    results: list[ClusterResult] = []

    algorithms = {
        "K-Means": KMeans(n_clusters=n_clusters, random_state=42, n_init=10),
        "Agglomerative": AgglomerativeClustering(n_clusters=n_clusters, linkage="ward"),
    }
    for name, algo in algorithms.items():
        labels = algo.fit_predict(X)
        try:
            sil = silhouette_score(X, labels)
            cal = calinski_harabasz_score(X, labels)
            dav = davies_bouldin_score(X, labels)
        except Exception:
            sil = cal = dav = None
        results.append(ClusterResult(
            name=name, n_clusters=n_clusters,
            silhouette=sil, calinski=cal, davies=dav, labels=labels.tolist(),
        ))

    # DBSCAN (auto eps via 5th-NN heuristic)
    try:
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=5)
        nn.fit(X)
        distances, _ = nn.kneighbors(X)
        eps = float(np.percentile(distances[:, -1], 90))
    except Exception:
        eps = 0.5

    dbscan = DBSCAN(eps=eps, min_samples=5)
    db_labels = dbscan.fit_predict(X)
    unique_clusters = set(db_labels) - {-1}
    n_noise = int((db_labels == -1).sum())

    if len(unique_clusters) > 1:
        mask = db_labels != -1
        try:
            sil = silhouette_score(X[mask], db_labels[mask])
            cal = calinski_harabasz_score(X[mask], db_labels[mask])
            dav = davies_bouldin_score(X[mask], db_labels[mask])
        except Exception:
            sil = cal = dav = None
        results.append(ClusterResult(
            name="DBSCAN", n_clusters=len(unique_clusters),
            silhouette=sil, calinski=cal, davies=dav,
            labels=db_labels.tolist(), n_noise=n_noise,
        ))
    else:
        results.append(ClusterResult(
            name="DBSCAN", n_clusters=len(unique_clusters),
            silhouette=None, calinski=None, davies=None,
            labels=db_labels.tolist(), n_noise=n_noise,
            notes=f"Only {len(unique_clusters)} cluster(s) found — try adjusting eps",
        ))
    return results


# ── Visualization ──────────────────────────────────────────────────────────────

def save_cluster_plot(X: "np.ndarray", results: list[ClusterResult], output_path: Path) -> None:
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)
    var = pca.explained_variance_ratio_

    n_plots = len(results)
    ncols = min(3, n_plots)
    nrows = (n_plots + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows), squeeze=False)
    axes = axes.flatten()

    for idx, r in enumerate(results):
        ax = axes[idx]
        labels = np.array(r.labels)
        unique = sorted(set(labels))
        colors = cm.tab10(np.linspace(0, 1, max(len(unique), 1)))

        for i, lbl in enumerate(unique):
            mask = labels == lbl
            color = "gray" if lbl == -1 else colors[i % len(colors)]
            marker = "x" if lbl == -1 else "o"
            label = "Noise" if lbl == -1 else f"C{lbl}"
            ax.scatter(X_2d[mask, 0], X_2d[mask, 1], c=[color], marker=marker,
                       alpha=0.6, s=20, label=label)

        title = f"{r.name} (k={r.n_clusters})"
        if r.silhouette is not None:
            title += f"\nSil={r.silhouette:.3f}"
        ax.set_title(title, fontsize=9)
        ax.set_xlabel(f"PC1 ({var[0]:.1%})", fontsize=8)
        ax.set_ylabel(f"PC2 ({var[1]:.1%})", fontsize=8)
        ax.tick_params(labelsize=7)
        if r.n_clusters <= 8:
            ax.legend(fontsize=7, markerscale=1.2)

    for idx in range(len(results), len(axes)):
        axes[idx].axis("off")

    plt.suptitle("Cluster Analysis — PCA Projection", fontsize=11, y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


# ── Report generation ──────────────────────────────────────────────────────────

def generate_report(
    results: list[ClusterResult],
    data_path: Path,
    n_samples: int,
    n_features: int,
    k_range: range | None,
    inertias: list[float] | None,
    silhouettes_per_k: list[float] | None,
    optimal_k: int | None,
    plot_path: Path | None,
) -> str:
    lines: list[str] = [
        "# Clustering Explorer Report",
        f"*Dataset: `{data_path.name}` | {n_samples} samples | {n_features} features*",
        "",
        "---",
        "",
    ]

    if k_range and optimal_k:
        lines += [
            "## A. Optimal K Analysis (K-Means Silhouette)",
            "",
            "| K | Inertia | Silhouette Score |",
            "| ---: | ---: | ---: |",
        ]
        for k, inert, sil in zip(k_range, inertias or [], silhouettes_per_k or []):
            marker = " ←" if k == optimal_k else ""
            lines.append(f"| {k} | {inert:.1f} | {sil:.4f}{marker} |")
        lines += ["", f"**Recommended K = {optimal_k}** (highest silhouette score)", "", "---", ""]

    lines += [
        "## B. Algorithm Comparison",
        "",
        "| Algorithm | Clusters | Silhouette ↑ | Calinski-Harabasz ↑ | Davies-Bouldin ↓ | Notes |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
    ]
    for r in results:
        sil = f"{r.silhouette:.4f}" if r.silhouette is not None else "N/A"
        cal = f"{r.calinski:.1f}" if r.calinski is not None else "N/A"
        dav = f"{r.davies:.4f}" if r.davies is not None else "N/A"
        noise = f" ({r.n_noise} noise pts)" if r.n_noise else ""
        lines.append(f"| {r.name} | {r.n_clusters}{noise} | {sil} | {cal} | {dav} | {r.notes} |")

    # Best algorithm by silhouette
    scored = [r for r in results if r.silhouette is not None]
    if scored:
        best = max(scored, key=lambda r: r.silhouette)
        lines += ["", f"**Best algorithm by silhouette: {best.name}** (score: {best.silhouette:.4f})", ""]

    if plot_path:
        lines += [
            "---",
            "",
            "## C. Cluster Visualization",
            "",
            f"![Cluster scatter]({plot_path.name})",
            "",
            "*2D PCA projection. Colors indicate cluster assignments.*",
            "",
        ]

    lines += [
        "---",
        "",
        "## D. Interpretation Guide",
        "",
        "| Metric | Good Range | Meaning |",
        "| :--- | :--- | :--- |",
        "| Silhouette Score | 0.5 – 1.0 | Points are well-separated from other clusters |",
        "| Calinski-Harabasz | Higher = better | Dense, well-separated clusters |",
        "| Davies-Bouldin | 0.0 – 1.0 | Low = compact, well-separated clusters |",
        "",
        "**Next steps:**",
        "1. Use the best cluster assignments as pseudo-labels for semi-supervised training.",
        "2. Investigate outlier/noise points (DBSCAN noise) — these may be rare defects or data errors.",
        "3. If clusters align with known classes, your feature space is discriminative — good sign for DL.",
        "",
        "---",
        "*Generated by `clustering_explorer.py` — BMAD DL Lifecycle (TSK-001)*",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Unsupervised clustering explorer for BMAD DL")
    parser.add_argument("data_csv", type=Path)
    parser.add_argument("--k", type=int, default=3, help="Number of clusters (default: 3)")
    parser.add_argument("--find-k", action="store_true", help="Search for optimal K (2–10)")
    parser.add_argument("--k-max", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--plot", type=Path, default=None, help="Save cluster plot PNG")
    args = parser.parse_args()

    if not HAS_SKLEARN or not HAS_NUMPY:
        print("Error: scikit-learn and numpy required. Run: pip install scikit-learn numpy",
              file=sys.stderr)
        return 2
    if not args.data_csv.exists():
        print(f"Error: File not found: {args.data_csv}", file=sys.stderr)
        return 2

    try:
        X_raw, feature_names = load_numeric_csv(args.data_csv)
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        return 2

    X = preprocess(X_raw)
    n_samples, n_features = X.shape
    print(f"Dataset: {n_samples} samples, {n_features} features")

    # Find optimal K
    k_range = inertias = silhouettes_k = optimal_k = None
    n_clusters = args.k
    if args.find_k:
        k_max = min(args.k_max, n_samples - 1)
        k_range = range(2, k_max + 1)
        print(f"Searching optimal K in range 2–{k_max}...")
        optimal_k, inertias, silhouettes_k = find_optimal_k(X, k_range)
        n_clusters = optimal_k
        print(f"Optimal K = {n_clusters}")

    print(f"Running clustering with k={n_clusters}...")
    results = run_clustering(X, n_clusters)

    # Plot
    plot_path: Path | None = None
    if args.plot:
        if HAS_MPL:
            save_cluster_plot(X, results, args.plot)
            plot_path = args.plot
            print(f"✓ Cluster plot: {plot_path}")
        else:
            print("⚠ matplotlib not available — skipping plot")

    report = generate_report(
        results, args.data_csv, n_samples, n_features,
        k_range, inertias, silhouettes_k, optimal_k, plot_path,
    )
    output = args.output or args.data_csv.parent / f"{args.data_csv.stem}_clustering_report.md"
    output.write_text(report, encoding="utf-8")
    print(f"✓ Report: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
