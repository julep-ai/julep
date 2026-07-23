from __future__ import annotations

import importlib.util
import os
import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from julep._env import LEGACY_ENV_VAR_RENAMES
from julep.cli.config import JulepConfig
from julep.cli.model import build_module
from julep.secrets import SECRET_REF_RE, SecretResolutionError, SecretResolver


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def _new_env_name(old: str) -> str:
    known = LEGACY_ENV_VAR_RENAMES.get(old)
    if known is not None:
        return known
    if old.startswith("CA_"):
        return f"JULEP_{old.removeprefix('CA_')}"
    if old.startswith("COMPOSABLE_WASM_"):
        return f"JULEP_WASM_{old.removeprefix('COMPOSABLE_WASM_')}"
    if old.startswith("COMPOSABLE_NATIVE_"):
        return f"JULEP_NATIVE_{old.removeprefix('COMPOSABLE_NATIVE_')}"
    return f"JULEP_{old.removeprefix('COMPOSABLE_')}"


def legacy_checks(
    root: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> list[Check]:
    """Return soft warnings for state left behind by the hard cutover."""
    root = Path(root).resolve()
    checks: list[Check] = []
    if (root / "ca.toml").exists():
        checks.append(
            Check(
                "legacy-config",
                False,
                "ca.toml found; rename it to julep.toml",
            )
        )

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*\[tool\.ca(?:\.|\])", text):
            checks.append(
                Check(
                    "legacy-config",
                    False,
                    "[tool.ca] found; rename it to [tool.julep]",
                )
            )

    if (root / ".ca").exists():
        checks.append(
            Check(
                "legacy-state",
                False,
                ".ca/ found; move retained state to .julep/",
            )
        )

    source = os.environ if environ is None else environ
    for name in sorted(source):
        if name in LEGACY_ENV_VAR_RENAMES or name.startswith(("CA_", "COMPOSABLE_")):
            checks.append(
                Check(
                    "legacy-env",
                    False,
                    f"{name} is set; rename it to {_new_env_name(name)}",
                )
            )
    return checks


def run_checks(
    cfg: JulepConfig,
    *,
    environ: Mapping[str, str] | None = None,
) -> list[Check]:
    checks = legacy_checks(cfg.root, environ=environ)
    module = build_module(cfg)
    n = len(module.agents)
    where = ", ".join(cfg.src) if cfg.src else str(cfg.root)
    checks.append(Check("discovery", n > 0, f"{n} agent(s) discovered under {where}"))

    source = os.environ if environ is None else environ
    references: dict[str, list[str]] = {}
    malformed_references: list[str] = []
    for server_name, server in cfg.mcp_servers.items():
        for header_name, value in server.headers.items():
            match = SECRET_REF_RE.fullmatch(value)
            if match is not None:
                references.setdefault(match.group(1), []).append(
                    f"mcp.servers.{server_name}.headers.{header_name}"
                )
            elif value.startswith("secret://"):
                malformed_references.append(
                    f"mcp.servers.{server_name}.headers.{header_name}"
                )
    dangling: list[str] = []
    resolver = SecretResolver.from_env(source)
    for secret_name in sorted(references):
        try:
            resolver.resolve(secret_name)
        except SecretResolutionError:
            dangling.append(secret_name)
    if malformed_references:
        checks.append(
            Check(
                "secrets",
                False,
                "malformed secret:// reference(s): "
                + ", ".join(malformed_references),
            )
        )
    elif dangling:
        checks.append(
            Check(
                "secrets",
                False,
                "dangling secret:// reference(s): " + ", ".join(dangling),
            )
        )
    else:
        checks.append(
            Check(
                "secrets",
                True,
                (
                    f"{len(references)} secret:// reference(s) resolved"
                    if references
                    else "no secret:// references"
                ),
            )
        )

    has_git = shutil.which("git") is not None
    checks.append(Check("git", has_git, "git found" if has_git else "git not on PATH (state:modified disabled)"))

    lf = bool(source.get("LANGFUSE_HOST"))
    checks.append(Check("langfuse", lf, "LANGFUSE_HOST set" if lf else "LANGFUSE_HOST unset (no deep links)"))

    has_temporal = importlib.util.find_spec("temporalio") is not None
    checks.append(Check("temporal", has_temporal, "temporalio installed" if has_temporal else "temporalio missing (deploy disabled)"))

    return checks


def overall_code(checks: list[Check]) -> int:
    """Exit 1 only if a hard-required check (discovery) fails; soft checks are warnings."""
    discovery = next((c for c in checks if c.name == "discovery"), None)
    return 0 if (discovery is None or discovery.ok) else 1
