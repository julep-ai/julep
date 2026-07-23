from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.check_rename_inventory import _is_excluded


ROOT = Path(__file__).resolve().parents[2]


def test_generated_docs_output_is_not_scanned() -> None:
    assert _is_excluded(Path("docs-site/.next/server/page.rsc"))
    assert _is_excluded(Path("docs-site/out/docs/page.txt"))
    assert not _is_excluded(Path("docs-site/content/docs/page.md"))


def test_retired_names_do_not_reenter_the_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_rename_inventory.py")],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
