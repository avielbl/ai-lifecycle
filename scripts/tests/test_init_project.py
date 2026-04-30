"""Unit tests for init_project.py"""

import sys
import tempfile
from pathlib import Path

import pytest

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))
import init_project as ip


@pytest.fixture()
def tmp_root(tmp_path):
    root = tmp_path / "test_proj"
    root.mkdir()
    return root


def test_create_dirs_creates_all_expected_directories(tmp_root):
    ip.create_dirs(tmp_root, "test_proj")

    assert (tmp_root / "docs" / "prd").is_dir()
    assert (tmp_root / "docs" / "eda").is_dir()
    assert (tmp_root / "docs" / "architecture").is_dir()
    assert (tmp_root / "docs" / "design").is_dir()
    assert (tmp_root / "docs" / "techspecs").is_dir()
    assert (tmp_root / "docs" / "implementation").is_dir()
    assert (tmp_root / "docs" / "experiments").is_dir()
    assert (tmp_root / "docs" / "revisions").is_dir()
    assert (tmp_root / "docs" / "knowledge").is_dir()
    assert (tmp_root / "data" / "raw").is_dir()
    assert (tmp_root / "data" / "processed").is_dir()
    assert (tmp_root / "data" / "splits").is_dir()
    assert (tmp_root / "src" / "test_proj").is_dir()
    assert (tmp_root / "tests").is_dir()
    assert (tmp_root / "scripts").is_dir()
    assert (tmp_root / "logs").is_dir()
    assert (tmp_root / "notebooks").is_dir()
    assert (tmp_root / "configs").is_dir()


def test_create_dirs_creates_gitkeep_files(tmp_root):
    ip.create_dirs(tmp_root, "test_proj")

    assert (tmp_root / "data" / "raw" / ".gitkeep").exists()
    assert (tmp_root / "data" / "processed" / ".gitkeep").exists()
    assert (tmp_root / "data" / "splits" / ".gitkeep").exists()


def test_create_dirs_creates_init_files(tmp_root):
    ip.create_dirs(tmp_root, "test_proj")

    assert (tmp_root / "src" / "test_proj" / "__init__.py").exists()
    assert (tmp_root / "tests" / "__init__.py").exists()


def test_write_clinerules_cline(tmp_root):
    ip.write_clinerules(tmp_root, "cline", "wandb")

    cr = tmp_root / ".clinerules"
    assert cr.exists()
    content = cr.read_text()
    assert "ai-agent-domain-expert" in content
    assert "wandb" in content
    assert "uv sync" in content


def test_write_clinerules_claude_code(tmp_root):
    ip.write_clinerules(tmp_root, "claude-code", "mlflow")

    md = tmp_root / ".claude" / "CLAUDE.md"
    assert md.exists()
    content = md.read_text()
    assert "ai-agent-domain-expert" in content
    assert "mlflow" in content
    assert "uv sync" in content
    assert "uv add" in content


def test_write_gitignore(tmp_root):
    ip.write_gitignore(tmp_root)

    gi = tmp_root / ".gitignore"
    assert gi.exists()
    content = gi.read_text()
    assert ".venv/" in content
    assert "*.ckpt" in content
    assert "mlruns/" in content
    assert "wandb/" in content


def test_write_gitignore_does_not_overwrite_existing(tmp_root):
    existing = tmp_root / ".gitignore"
    existing.write_text("# custom")

    ip.write_gitignore(tmp_root)

    assert existing.read_text() == "# custom"


def test_write_pyproject_no_dependencies(tmp_root):
    ip.write_pyproject(tmp_root, "test_proj", "3.11")

    pf = tmp_root / "pyproject.toml"
    assert pf.exists()
    content = pf.read_text()
    assert "test_proj" in content
    assert 'dependencies = []' in content
    assert "requires-python" in content
    assert "3.11" in content


def test_write_pyproject_skips_if_exists(tmp_root):
    existing = tmp_root / "pyproject.toml"
    existing.write_text("[project]\nname = 'already'")

    ip.write_pyproject(tmp_root, "test_proj", "3.11")

    assert "already" in existing.read_text()


def test_write_python_version(tmp_root):
    ip.write_python_version(tmp_root, "3.11")

    pv = tmp_root / ".python-version"
    assert pv.exists()
    assert pv.read_text().strip() == "3.11"
