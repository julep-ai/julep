"""Build dependency-specific wasm executor environment components.

This module is deploy/build-time only. Importing it performs no filesystem,
network, or toolchain I/O; all expensive work is inside explicit functions.
"""

from __future__ import annotations

import re
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from collections.abc import Sequence

from .. import deps as deps_mod

SUPPORTED_WASI_WHEELS: frozenset[str] = frozenset({"pydantic-core", "regex"})

_PROJECT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_WASI_WHEELS_RELEASE = "https://github.com/dicej/wasi-wheels/releases/download/latest"
_WASM_ROOT = Path(__file__).parent / "_wasm"
_WIT = _WASM_ROOT / "wit" / "executor.wit"
_BASE_COMPONENT = _WASM_ROOT / "executor.wasm"


class EnvBuildError(Exception):
    pass


def _normalized_project_name(requirement: str) -> str:
    match = _PROJECT_NAME.match(requirement)
    if match is None:
        raise EnvBuildError(f"dependency requirement has no PEP 508 project name: {requirement!r}")
    return match.group(1).lower().replace("_", "-").replace(".", "-")


def _env_hash(deps: Sequence[str], requires_python: str | None) -> str:
    return deps_mod.env_hash(deps, requires_python, deps_mod.base_component_hash())


def supported_deps(deps: Sequence[str]) -> bool:
    """Return True when every dependency has a curated WASI wheel env.

    Empty dependency lists return False: there is no env component to build, and
    no-dep pures must keep using the base executor component.
    """
    if not deps:
        return False
    return all(_normalized_project_name(dep) in SUPPORTED_WASI_WHEELS for dep in deps)


def _leb128_u32(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _custom_section(name: str, payload: bytes) -> bytes:
    name_bytes = name.encode("utf-8")
    section_payload = _leb128_u32(len(name_bytes)) + name_bytes + payload
    return b"\x00" + _leb128_u32(len(section_payload)) + section_payload


def synthesize_env_component(
    deps: Sequence[str],
    requires_python: str | None,
    *,
    marker: bytes = b"",
) -> bytes:
    """Return a deterministic, loadable env component for tests/dev.

    The bytes are the vendored base executor component plus a deterministic wasm
    custom section carrying the env identity. That keeps the component
    instantiable while giving different dependency pins different CAS digests.
    It does not bundle or validate third-party wheels.
    """
    env_hash = _env_hash(deps, requires_python)
    payload = env_hash.encode("ascii") + b"\0" + marker
    return _BASE_COMPONENT.read_bytes() + _custom_section("composable-env", payload)


def build_env_component(
    deps: Sequence[str],
    requires_python: str | None,
    *,
    out_dir: str | Path | None = None,
) -> Path:
    """Build a pre-initialized wasm env component for supported WASI wheels."""
    if not supported_deps(deps):
        unsupported = sorted(
            {
                _normalized_project_name(dep)
                for dep in deps
                if _normalized_project_name(dep) not in SUPPORTED_WASI_WHEELS
            }
        )
        raise EnvBuildError(
            "dependency env cannot be built for unsupported WASI wheel(s): "
            f"{', '.join(unsupported) or '<none>'}. Supported: "
            f"{', '.join(sorted(SUPPORTED_WASI_WHEELS))}."
        )

    env_hash = _env_hash(deps, requires_python)
    output_root = Path(out_dir) if out_dir is not None else Path(
        tempfile.mkdtemp(prefix="composable-env-")
    )
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / f"env_{env_hash}.wasm"

    with tempfile.TemporaryDirectory(prefix="composable-env-site-") as temp:
        site_packages = Path(temp) / "site-packages"
        site_packages.mkdir(parents=True)
        for project in sorted({_normalized_project_name(dep) for dep in deps}):
            _download_and_extract_wasi_wheel(project, site_packages)

        command = [
            "componentize-py",
            "-d",
            str(_WIT),
            "-w",
            "executor",
            "componentize",
            "--stub-wasi",
            "--python-path",
            str(_WASM_ROOT),
            "--python-path",
            str(site_packages),
            "executor_component",
            "-o",
            str(output),
        ]
        try:
            subprocess.run(command, cwd=_WASM_ROOT, check=True)
        except FileNotFoundError as e:
            raise EnvBuildError(
                "componentize-py is not available; install the build toolchain "
                "and retry env component publishing"
            ) from e
        except subprocess.CalledProcessError as e:
            raise EnvBuildError(
                "componentize-py failed while building the dependency env component; "
                "check the supported WASI wheels and componentize-py toolchain"
            ) from e

    return output


def publish_env_component(
    deps: Sequence[str],
    requires_python: str | None,
    store: object,
) -> tuple[str, str]:
    env_hash = _env_hash(deps, requires_python)
    component_path = build_env_component(deps, requires_python)
    data = component_path.read_bytes()
    digest = store.put(data)
    if not isinstance(digest, str):
        raise EnvBuildError("CAS store returned a non-string digest for env component")
    return env_hash, digest


def _download_and_extract_wasi_wheel(project: str, target: Path) -> None:
    archive_project = project.replace("-", "_")
    url = f"{_WASI_WHEELS_RELEASE}/{archive_project}-wasi.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
    except (OSError, urllib.error.URLError) as e:
        raise EnvBuildError(
            f"failed to download WASI wheel archive for {project!r} from {url}; "
            "check network access or prebuild the env component"
        ) from e

    archive_path = target.parent / f"{archive_project}-wasi.tar.gz"
    archive_path.write_bytes(data)
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            _safe_extract(tar, target)
    except (tarfile.TarError, OSError) as e:
        raise EnvBuildError(f"failed to extract WASI wheel archive for {project!r}") from e


def _safe_extract(tar: tarfile.TarFile, target: Path) -> None:
    root = target.resolve()
    for member in tar.getmembers():
        destination = (target / member.name).resolve()
        if not str(destination).startswith(f"{root}/") and destination != root:
            raise EnvBuildError(f"WASI wheel archive contains unsafe path: {member.name!r}")
    tar.extractall(target)
