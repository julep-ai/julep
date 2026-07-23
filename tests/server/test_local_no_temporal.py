from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def test_local_preflight_runs_without_temporalio(tmp_path: Path) -> None:
    script = textwrap.dedent(
        """
        import asyncio
        import importlib.abc
        import importlib.util
        import sys
        from pathlib import Path

        real_find_spec = importlib.util.find_spec
        importlib.util.find_spec = lambda name, package=None: (
            None
            if name == "temporalio" or name.startswith("temporalio.")
            else real_find_spec(name, package)
        )

        class BlockTemporal(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "temporalio" or fullname.startswith("temporalio."):
                    raise ModuleNotFoundError(
                        f"No module named {fullname!r}",
                        name=fullname,
                    )
                return None

        for name in tuple(sys.modules):
            if name == "temporalio" or name.startswith("temporalio."):
                del sys.modules[name]
        sys.meta_path.insert(0, BlockTemporal())

        from julep.execution import effects
        from julep.execution.mcp_preflight import McpPreflightError, preflight_mcp
        from julep.server.local import create_local_app

        assert "julep.execution.harness" not in sys.modules
        effects.configure(effects.WorkerContext())
        result = asyncio.run(
            preflight_mcp(
                {
                    "workflowId": "local-no-temporal",
                    "manifestJson": {},
                    "policy": "off",
                }
            )
        )
        assert result == {
            "policy": "off",
            "completed": True,
            "surfaceDigest": None,
        }
        try:
            asyncio.run(
                preflight_mcp(
                    {
                        "workflowId": "local-no-temporal-refusal",
                        "manifestJson": {},
                        "policy": "off",
                        "secrets": {"unused": "never-rendered"},
                    }
                )
            )
        except McpPreflightError as exc:
            assert exc.type == "invalid_run_secret_binding"
            assert "never-rendered" not in exc.detail
        else:
            raise AssertionError("unused local secret was accepted")

        app = create_local_app(project_root=Path(sys.argv[1]), host="127.0.0.1")
        assert app.state.local_mode is True
        assert "julep.execution.harness" not in sys.modules
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
