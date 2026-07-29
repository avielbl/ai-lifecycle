"""Smoke tests for build_notebook.py — the EDA notebook skeleton generator.

Run without installing into the project venv:
    uv run --with pytest --with nbformat pytest ai-agent-data-engineer/scripts/tests/test_build_notebook.py -q
"""

import subprocess
import sys
from pathlib import Path

import nbformat
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from build_notebook import SECTION_TITLES, build_notebook  # noqa: E402

CSV_CONTENT = """feature_a,feature_b,label
1.0,2.5,cat
2.0,3.5,dog
3.0,1.5,cat
4.0,0.5,dog
"""


@pytest.fixture
def tiny_csv(tmp_path):
    csv_path = tmp_path / "tiny.csv"
    csv_path.write_text(CSV_CONTENT, encoding="utf-8")
    return csv_path


def test_build_notebook_is_valid_nbformat(tiny_csv):
    nb = build_notebook(tiny_csv)
    nbformat.validate(nb)  # raises on invalid structure


def test_build_notebook_has_all_sections(tiny_csv):
    nb = build_notebook(tiny_csv)
    md_text = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
    for title in SECTION_TITLES:
        assert f"## {title}" in md_text, f"missing section: {title}"


def test_build_notebook_cells_alternate_and_reference_scripts(tiny_csv):
    nb = build_notebook(tiny_csv, label_col="label")
    code_text = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    # Setup cell embeds paths and label column
    assert str(tiny_csv) in code_text
    assert "LABEL_COL = 'label'" in code_text
    assert str(SCRIPTS_DIR) in code_text
    # Code cells call the importable functions of the EDA suite
    assert "from class_weights_calculator import compute_weights" in code_text
    assert "from clustering_explorer import load_numeric_csv, preprocess, run_clustering" in code_text
    assert "from baseline_classifier import load_csv, _to_numeric_matrix, run_baseline" in code_text
    # Kernel metadata present so headless execution can pick a kernel
    assert nb.metadata["kernelspec"]["name"] == "python3"


def test_cli_writes_notebook_file(tiny_csv, tmp_path):
    out = tmp_path / "notebooks" / "eda_report.ipynb"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "build_notebook.py"), str(tiny_csv),
         "--output", str(out), "--label-col", "label"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    nb = nbformat.read(str(out), as_version=4)
    nbformat.validate(nb)
    assert len(nb.cells) >= 2 * len(SECTION_TITLES)


def test_code_cells_are_syntactically_valid(tiny_csv):
    nb = build_notebook(tiny_csv)
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"<cell {i}>", "exec")
