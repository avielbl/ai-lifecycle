"""Unit tests for init_project.py"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))
import init_project as ip

SCRIPT = Path(__file__).parent.parent / "init_project.py"

GIT_AVAILABLE = shutil.which("git") is not None
UV_AVAILABLE = shutil.which("uv") is not None


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


def test_write_clinerules_opencode(tmp_root):
    ip.write_clinerules(tmp_root, "opencode", "clearml")

    agents_md = tmp_root / "AGENTS.md"
    assert agents_md.exists()
    # opencode must NOT get a .clinerules — AGENTS.md is its native rules file
    assert not (tmp_root / ".clinerules").exists()
    content = agents_md.read_text()
    assert "ai-agent-domain-expert" in content
    assert "domain-research" in content
    assert "clearml" in content
    assert ".claude/skills/" in content       # where opencode discovers the skills
    assert "opencode" in content
    assert "uv sync" in content
    assert "TECHSPEC" in content


def test_write_clinerules_copilot(tmp_root):
    ip.write_clinerules(tmp_root, "copilot", "wandb")

    instructions = tmp_root / ".github" / "copilot-instructions.md"
    assert instructions.exists()
    assert not (tmp_root / ".clinerules").exists()
    content = instructions.read_text()
    assert "wandb" in content
    assert "uv sync" in content
    assert "tool-calling" in content          # agent-mode model caveat documented
    assert "/ai-agent-domain-expert" in content

    # One prompt-file wrapper per agent → /<name> commands in Copilot chat
    for name, stages, role in ip.AGENT_ROSTER:
        pf = tmp_root / ".github" / "prompts" / f"{name}.prompt.md"
        assert pf.exists(), f"missing prompt file for {name}"
        body = pf.read_text()
        assert body.startswith("---")         # YAML front matter
        assert "description:" in body
        assert f".claude/skills/{name}/SKILL.md" in body
        assert "which capability to activate" in body
    assert len(list((tmp_root / ".github" / "prompts").glob("*.prompt.md"))) == len(ip.AGENT_ROSTER)


def test_write_gitignore(tmp_root):
    ip.write_gitignore(tmp_root)

    gi = tmp_root / ".gitignore"
    assert gi.exists()
    content = gi.read_text()
    assert ".venv/" in content
    assert "*.ckpt" in content
    assert "mlruns/" in content
    assert "wandb/" in content
    # imports/ is gitignored by default (internal exports are often sensitive),
    # but its README stays tracked
    assert "imports/*" in content
    assert "!imports/README.md" in content


def test_write_imports_tree_creates_subfolders_and_readme(tmp_root):
    ip.write_imports_tree(tmp_root)

    for sub in ["jira", "confluence", "sharepoint", "docs"]:
        assert (tmp_root / "imports" / sub).is_dir()

    readme = tmp_root / "imports" / "README.md"
    assert readme.exists()
    content = readme.read_text()
    # Expected export formats are documented per subfolder
    assert "jira/" in content
    assert "confluence/" in content
    assert "sharepoint/" in content
    assert "docs/" in content
    assert "CSV" in content
    assert "gitignored" in content


def test_write_imports_tree_does_not_overwrite_readme(tmp_root):
    (tmp_root / "imports").mkdir()
    existing = tmp_root / "imports" / "README.md"
    existing.write_text("# custom")

    ip.write_imports_tree(tmp_root)

    assert existing.read_text() == "# custom"


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


# ---------------------------------------------------------------------------
# CLI flag parsing
# ---------------------------------------------------------------------------

def test_parse_args_all_flags():
    args = ip.parse_args([
        "--ide", "claude-code",
        "--tracker", "mlflow",
        "--python-version", "3.12",
        "--data-location", "s3",
        "--data-uri", "s3://bucket/data",
        "--artifact-registry", "gcs",
        "--artifact-uri", "gs://bucket/artifacts",
        "--compute", "cloud-managed",
        "--compute-service", "vertex-ai",
        "--git-remote", "git@github.com:org/repo.git",
        "--yes",
    ])
    assert args.ide == "claude-code"
    assert args.tracker == "mlflow"
    assert args.python_version == "3.12"
    assert args.data_location == "s3"
    assert args.data_uri == "s3://bucket/data"
    assert args.artifact_registry == "gcs"
    assert args.artifact_uri == "gs://bucket/artifacts"
    assert args.compute == "cloud-managed"
    assert args.compute_service == "vertex-ai"
    assert args.git_remote == "git@github.com:org/repo.git"
    assert args.yes is True


def test_parse_args_defaults_to_none():
    args = ip.parse_args([])
    assert args.ide is None
    assert args.data_location is None
    assert args.compute is None
    assert args.yes is False


def test_parse_args_rejects_invalid_choice():
    with pytest.raises(SystemExit):
        ip.parse_args(["--compute", "quantum"])


def test_parse_args_accepts_new_ide_choices():
    assert ip.parse_args(["--ide", "opencode"]).ide == "opencode"
    assert ip.parse_args(["--ide", "copilot"]).ide == "copilot"


def test_parse_args_rejects_unknown_ide():
    with pytest.raises(SystemExit):
        ip.parse_args(["--ide", "emacs"])


def test_resolve_prefers_flag_over_default():
    assert ip._resolve("s3", True, "Data location", "local") == "s3"


def test_resolve_uses_default_with_yes():
    assert ip._resolve(None, True, "Data location", "local") == "local"


def test_ask_returns_default_on_eof(monkeypatch):
    def raise_eof(_prompt):
        raise EOFError
    monkeypatch.setattr("builtins.input", raise_eof)
    # Must NOT exit — old printf pipes exhaust stdin before the new questions
    assert ip._ask("Data location", "local", choices=["local", "s3"]) == "local"


# ---------------------------------------------------------------------------
# configs/project_infra.yaml
# ---------------------------------------------------------------------------

def test_write_infra_config_defaults(tmp_root):
    yaml = pytest.importorskip("yaml")
    (tmp_root / "configs").mkdir()

    ip.write_infra_config(tmp_root, "local", "", "local", "", "same-machine", None)

    dest = tmp_root / "configs" / "project_infra.yaml"
    assert dest.exists()
    content = dest.read_text()
    assert "TECHSPEC (Stage 4.5)" in content
    assert "infra (Stage 5)" in content

    data = yaml.safe_load(content)
    assert data["data"]["location"] == "local"
    assert data["data"]["uri"] is None
    assert data["artifacts"]["registry"] == "local"
    assert data["artifacts"]["uri"] is None
    assert data["compute"]["topology"] == "same-machine"
    assert data["compute"]["service"] is None


def test_write_infra_config_cloud_managed(tmp_root):
    yaml = pytest.importorskip("yaml")
    (tmp_root / "configs").mkdir()

    ip.write_infra_config(
        tmp_root, "s3", "s3://bucket/data", "tracker-native", "",
        "cloud-managed", "vertex-ai",
    )

    data = yaml.safe_load((tmp_root / "configs" / "project_infra.yaml").read_text())
    assert data["data"]["location"] == "s3"
    assert data["data"]["uri"] == "s3://bucket/data"
    assert data["artifacts"]["registry"] == "tracker-native"
    assert data["compute"]["topology"] == "cloud-managed"
    assert data["compute"]["service"] == "vertex-ai"


def test_write_infra_config_does_not_overwrite(tmp_root):
    (tmp_root / "configs").mkdir()
    existing = tmp_root / "configs" / "project_infra.yaml"
    existing.write_text("# custom")

    ip.write_infra_config(tmp_root, "gcs", "", "gcs", "", "remote-gpu", None)

    assert existing.read_text() == "# custom"


# ---------------------------------------------------------------------------
# docker/ templates
# ---------------------------------------------------------------------------

def test_write_docker_templates(tmp_root):
    ip.write_docker_templates(tmp_root, "test_proj", "3.11", "cloud-managed", "clearml")

    dockerfile = tmp_root / "docker" / "Dockerfile.train"
    readme = tmp_root / "docker" / "README.md"
    assert dockerfile.exists()
    assert readme.exists()

    df = dockerfile.read_text()
    assert "FROM python:3.11-slim" in df
    assert "uv sync --frozen" in df
    assert "ENTRYPOINT" in df
    assert "nvidia/cuda" in df  # CUDA note in comments

    rd = readme.read_text()
    assert "Vertex AI" in rd
    assert "ClearML" in rd
    assert "docker run" in rd
    # The chosen service section is emphasized
    assert "## ClearML Agent queues  <- configured target" in rd


def test_write_docker_templates_default_marks_generic(tmp_root):
    ip.write_docker_templates(tmp_root, "test_proj", "3.12", "same-machine", None)

    rd = (tmp_root / "docker" / "README.md").read_text()
    assert "## Generic docker run / Kubernetes  <- configured target" in rd
    df = (tmp_root / "docker" / "Dockerfile.train").read_text()
    assert "FROM python:3.12-slim" in df


def test_write_docker_templates_does_not_overwrite(tmp_root):
    (tmp_root / "docker").mkdir()
    existing = tmp_root / "docker" / "Dockerfile.train"
    existing.write_text("# custom")

    ip.write_docker_templates(tmp_root, "test_proj", "3.11", "same-machine", None)

    assert existing.read_text() == "# custom"


# ---------------------------------------------------------------------------
# git helpers (unit level, real git in a tmp dir)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_run_git_init_creates_repo(tmp_root):
    assert ip.run_git_init(tmp_root) is True
    assert (tmp_root / ".git").is_dir()


@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_run_git_init_skips_existing_repo(tmp_root):
    ip.run_git_init(tmp_root)
    assert ip.run_git_init(tmp_root) is True  # second call skips, still True


# ---------------------------------------------------------------------------
# End-to-end: main() via subprocess in a tmp dir
# ---------------------------------------------------------------------------

def _git_env():
    import os
    env = dict(os.environ)
    env.update({
        "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
    })
    return env


@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_main_with_flags_end_to_end(tmp_root):
    yaml = pytest.importorskip("yaml")
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--ide", "cline", "--tracker", "clearml", "--python-version", "3.11",
         "--data-location", "gcs", "--data-uri", "gs://bucket/data",
         "--artifact-registry", "tracker-native",
         "--compute", "cloud-managed", "--compute-service", "clearml",
         "--git-remote", "https://example.com/repo.git", "--yes"],
        cwd=tmp_root, capture_output=True, text=True, timeout=120, env=_git_env(),
    )
    assert result.returncode == 0, result.stderr

    # infra config written with the flag values
    data = yaml.safe_load((tmp_root / "configs" / "project_infra.yaml").read_text())
    assert data["data"]["location"] == "gcs"
    assert data["data"]["uri"] == "gs://bucket/data"
    assert data["artifacts"]["registry"] == "tracker-native"
    assert data["compute"]["topology"] == "cloud-managed"
    assert data["compute"]["service"] == "clearml"

    # docker templates exist
    assert (tmp_root / "docker" / "Dockerfile.train").exists()
    assert (tmp_root / "docker" / "README.md").exists()

    # imports/ export drop-folder created; gitignored except its README
    for sub in ["jira", "confluence", "sharepoint", "docs"]:
        assert (tmp_root / "imports" / sub).is_dir()
    assert (tmp_root / "imports" / "README.md").exists()
    tracked = subprocess.run(["git", "ls-files", "imports"],
                             cwd=tmp_root, capture_output=True, text=True)
    assert tracked.stdout.split() == ["imports/README.md"]

    # git repo initialised with the remote registered, never pushed
    assert (tmp_root / ".git").is_dir()
    remotes = subprocess.run(["git", "remote", "get-url", "origin"],
                             cwd=tmp_root, capture_output=True, text=True)
    assert remotes.stdout.strip() == "https://example.com/repo.git"
    log = subprocess.run(["git", "log", "--oneline"],
                         cwd=tmp_root, capture_output=True, text=True)
    assert "scaffold AI/ML project structure" in log.stdout
    assert "git push" in result.stdout  # push offered as next step, not executed

    # venv created (empty) when uv is available; warn-only otherwise
    if UV_AVAILABLE:
        assert (tmp_root / ".venv").exists()


@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_main_legacy_stdin_pipe_still_works(tmp_root):
    """The old printf pipe (ide, tracker, python, yes) must not hang and must
    fall back to defaults for the new infra questions."""
    yaml = pytest.importorskip("yaml")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input="cline\nwandb\n3.11\nyes\n",
        cwd=tmp_root, capture_output=True, text=True, timeout=120, env=_git_env(),
    )
    assert result.returncode == 0, result.stderr

    # Old answers honoured
    assert (tmp_root / ".clinerules").exists()
    assert "wandb" in (tmp_root / ".clinerules").read_text()

    # New questions defaulted (tracker chosen -> registry defaults to tracker-native)
    data = yaml.safe_load((tmp_root / "configs" / "project_infra.yaml").read_text())
    assert data["data"]["location"] == "local"
    assert data["artifacts"]["registry"] == "tracker-native"
    assert data["compute"]["topology"] == "same-machine"
    assert data["compute"]["service"] is None

    assert (tmp_root / "docker" / "Dockerfile.train").exists()
    assert (tmp_root / ".git").is_dir()


@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_main_opencode_end_to_end(tmp_root):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--ide", "opencode", "--yes"],
        cwd=tmp_root, capture_output=True, text=True, timeout=120, env=_git_env(),
    )
    assert result.returncode == 0, result.stderr

    assert (tmp_root / "AGENTS.md").exists()
    assert not (tmp_root / ".clinerules").exists()
    # Skills copied where opencode discovers Claude-compatible skill dirs
    assert (tmp_root / ".claude" / "skills" / "ai-agent-domain-expert" / "SKILL.md").exists()
    assert "ai-agent-domain-expert" in result.stdout  # stage-1 next-step hint


@pytest.mark.skipif(not GIT_AVAILABLE, reason="git not available")
def test_main_copilot_end_to_end(tmp_root):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--ide", "copilot", "--yes"],
        cwd=tmp_root, capture_output=True, text=True, timeout=120, env=_git_env(),
    )
    assert result.returncode == 0, result.stderr

    assert (tmp_root / ".github" / "copilot-instructions.md").exists()
    prompts = sorted((tmp_root / ".github" / "prompts").glob("*.prompt.md"))
    assert len(prompts) == len(ip.AGENT_ROSTER)
    # Prompt files must point at paths that actually exist in the scaffold
    for name, _stages, _role in ip.AGENT_ROSTER:
        assert (tmp_root / ".claude" / "skills" / name / "SKILL.md").exists()
    # Glue files are committed with the scaffold
    tracked = subprocess.run(["git", "ls-files", ".github"],
                             cwd=tmp_root, capture_output=True, text=True)
    assert ".github/copilot-instructions.md" in tracked.stdout.split()
