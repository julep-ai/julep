from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None


@dataclass(frozen=True)
class CaConfig:
    root: Path
    src: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    tags: dict[str, list[str]] = field(default_factory=dict)
    fail_severity: str = 'error'


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    if _tomllib is None:
        raise RuntimeError('reading TOML requires Python 3.11 or newer')
    with path.open('rb') as fh:
        data: dict[str, Any] = _tomllib.load(fh)
        return data


def load_config(root: str | Path) -> CaConfig:
    """Read [tool.ca] from pyproject.toml, then overlay a sibling ca.toml if present."""
    root = Path(root)
    pyproject = _read_toml(root / 'pyproject.toml').get('tool', {}).get('ca', {})
    ca_toml = _read_toml(root / 'ca.toml')
    merged: dict[str, Any] = {**pyproject, **ca_toml}
    gates = {**pyproject.get('gates', {}), **ca_toml.get('gates', {})}
    return CaConfig(
        root=root,
        src=list(merged.get('src', [str(root)])),
        exclude=list(merged.get('exclude', [])),
        tags={k: list(v) for k, v in merged.get('tags', {}).items()},
        fail_severity=str(gates.get('fail_severity', 'error')),
    )
