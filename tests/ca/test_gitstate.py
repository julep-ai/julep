# tests/ca/test_gitstate.py
import subprocess

from composable_agents.ca.gitstate import modified_agent_files


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_modified_files_vs_head(sample_module):
    root = sample_module
    _git(root, "init")
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    (root / "pkg" / "agents.py").write_text(
        (root / "pkg" / "agents.py").read_text() + "\n# edit\n", encoding="utf-8"
    )
    changed = modified_agent_files(str(root), "HEAD")
    assert any(f.endswith("pkg/agents.py") for f in changed)


def test_no_changes_returns_empty(sample_module):
    root = sample_module
    _git(root, "init")
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    assert modified_agent_files(str(root), "HEAD") == set()
