from __future__ import annotations

import subprocess
from pathlib import Path


def modified_agent_files(root: str, ref: str = "HEAD") -> set[str]:
    """Absolute paths of .py files changed vs `ref`, including uncommitted working-tree edits."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", ref],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    return {
        str((Path(root) / line).resolve())
        for line in out.splitlines()
        if line.strip().endswith(".py")
    }
