from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_retired_names_do_not_reenter_the_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_rename_inventory.py")],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
