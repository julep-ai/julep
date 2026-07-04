"""Build dependency-specific wasm executor environment components.

This module is deploy/build-time only. Importing it performs no filesystem,
network, or toolchain I/O; all expensive work is inside explicit functions.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

from .. import deps as deps_mod

# regex is fully working in the wasm env tier (vendored, links, imports, runs).
# pydantic-core stays on the curated list but is NOT vendored: its wheel builds
# against the matched toolchain, but PyO3 0.20.0 (pinned by pydantic-core 2.14.5)
# references private CPython symbols (_PyLong_AsByteArray, _PyLong_NumBits) that
# componentize-py 0.24.0's embedded interpreter does not export, so componentize
# linking fails regardless of the wheel's build toolchain. Declaring a
# pydantic-core pure therefore fails closed at env build with a clear "not
# vendored" error until componentize exports those symbols (or PyO3 is bumped to a
# version that uses only public APIs). See TODOS.md (P4-1 / pydantic-core blocker).
SUPPORTED_WASI_WHEELS: frozenset[str] = frozenset({"pydantic-core", "regex"})
_WASI_PROJECT_IMPORT_MODULES: dict[str, str] = {
    "pydantic-core": "pydantic_core",
    "regex": "regex",
}

_PROJECT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_WASM_ROOT = Path(__file__).parent / "_wasm"
_WASI_WHEELS_DIR = _WASM_ROOT / "wasi_wheels"
_WIT = _WASM_ROOT / "wit" / "executor.wit"
_BASE_COMPONENT = _WASM_ROOT / "executor.wasm"
_ENV_SUPPORT_ENTRIES = (
    "executor_component.py",
    "wit_world",
    "poll_loop.py",
    "componentize_py_async_support",
    "componentize_py_runtime.pyi",
    "componentize_py_types.py",
)


class EnvBuildError(Exception):
    pass


def _normalized_project_name(requirement: str) -> str:
    match = _PROJECT_NAME.match(requirement)
    if match is None:
        raise EnvBuildError(f"dependency requirement has no PEP 508 project name: {requirement!r}")
    return match.group(1).lower().replace("_", "-").replace(".", "-")


def _pep503_normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _env_hash(deps: Sequence[str], requires_python: str | None) -> str:
    return deps_mod.env_hash(deps, requires_python, deps_mod.base_component_hash())


def _wasi_import_module(project: str) -> str:
    return _WASI_PROJECT_IMPORT_MODULES.get(project, project.replace("-", "_"))


def _vendored_wheel_dir(project: str) -> Path:
    wheel_dir = _WASI_WHEELS_DIR / project.replace("-", "_")
    if not wheel_dir.is_dir():
        raise EnvBuildError(
            f"supported WASI wheel project {project!r} is not vendored at {wheel_dir}"
        )
    return wheel_dir


def supported_deps(deps: Sequence[str]) -> bool:
    """Return True when every dependency has a curated WASI wheel env.

    Empty dependency lists return False: there is no env component to build, and
    no-dep pures must keep using the base executor component.
    """
    if not deps:
        return False
    return all(_normalized_project_name(dep) in SUPPORTED_WASI_WHEELS for dep in deps)


def unsupported_deps(deps: Sequence[str]) -> tuple[str, ...]:
    """Return dependency requirements outside the curated WASI wheel list."""
    return tuple(
        dep
        for dep in deps
        if _normalized_project_name(dep) not in SUPPORTED_WASI_WHEELS
    )


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
    """Build a pre-initialized wasm env component for supported WASI wheels.

    The *inputs* are now fully reproducible: immutable, content-hashed wheels
    vendored under ``_wasm/wasi_wheels/`` (no more mutable ``latest`` download)
    plus the deterministic generated entry module. The *output bytes* are still
    NOT bit-reproducible, however: componentize-py ``--stub-wasi`` bakes a fresh
    PRNG seed into the snapshot at every build (so Python ``random`` is fixed at
    runtime), and CPython's pre-init heap snapshot is not byte-stable across
    runs. So two builds of the same dep set yield the same ``envHash`` (the
    content-addressed identity, derived purely from deps + base component) but
    different ``envComponent`` CAS digests. Resolution is keyed by ``envHash``
    and ships whatever component bytes were published for it; byte-identical
    rebuilds would require an upstream componentize determinism mode or a
    post-link canonicalization pass (residual P4-1 follow-up; see TODOS.md).
    """
    _verify_exact_pins(deps)
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
        temp_root = Path(temp)
        site_packages = temp_root / "site-packages"
        site_packages.mkdir(parents=True)
        projects = sorted({_normalized_project_name(dep) for dep in deps})
        for project in projects:
            for source in sorted(_vendored_wheel_dir(project).iterdir(), key=lambda path: path.name):
                destination = site_packages / source.name
                if source.is_dir():
                    shutil.copytree(source, destination, symlinks=True)
                else:
                    shutil.copy2(source, destination)
        _verify_pinned_versions(deps, site_packages)

        runtime_dir = temp_root / "runtime"
        runtime_dir.mkdir()
        _copy_env_support(runtime_dir)
        runtime_dir.joinpath("env_component.py").write_text(
            _env_entry_source(tuple(_wasi_import_module(project) for project in projects)),
            encoding="utf-8",
        )

        command = [
            "componentize-py",
            "-d",
            str(_WIT),
            "-w",
            "executor",
            "componentize",
            "--stub-wasi",
            "--python-path",
            str(runtime_dir),
            "--python-path",
            str(site_packages),
            "env_component",
            "-o",
            str(output),
        ]
        try:
            subprocess.run(command, cwd=temp_root, check=True)
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


def _copy_env_support(runtime_dir: Path) -> None:
    for name in _ENV_SUPPORT_ENTRIES:
        source = _WASM_ROOT / name
        destination = runtime_dir / name
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                symlinks=True,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        else:
            shutil.copy2(source, destination)


def _env_entry_source(import_modules: Sequence[str]) -> str:
    import_lines = "".join(f"import {module}\n" for module in sorted(set(import_modules)))
    return (
        "# Generated by julep.execution.env_builder.\n"
        "# Pre-import dependency modules during componentize-py pre-init.\n"
        f"{import_lines}"
        "from executor_component import WitWorld  # noqa: F401\n"
    )


def _verify_exact_pins(deps: Sequence[str]) -> None:
    for requirement in deps:
        _, specifier = _requirement_name_and_specifier(requirement)
        if specifier and _is_exact_pin(specifier):
            continue
        raise EnvBuildError(
            f"dependency requirement {requirement!r} is not exactly version-pinned; "
            "wasm env components require exact-version pins like 'regex==2024.11.6'"
        )


def _is_exact_pin(specifier: str) -> bool:
    try:
        from packaging.specifiers import InvalidSpecifier, SpecifierSet
    except ImportError:
        compact = specifier.replace(" ", "")
        if "," in compact:
            return False
        if compact.startswith("==="):
            version = compact[3:]
        elif compact.startswith("=="):
            version = compact[2:]
        else:
            return False
        return bool(version) and "*" not in version

    try:
        specifiers = list(SpecifierSet(specifier))
    except InvalidSpecifier as e:
        raise EnvBuildError(f"dependency requirement has invalid version specifier {specifier!r}") from e
    if len(specifiers) != 1:
        return False
    only = specifiers[0]
    return only.operator in {"==", "==="} and "*" not in only.version


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


def _verify_pinned_versions(deps: Sequence[str], site_packages: Path) -> None:
    available_versions = _available_distribution_versions(site_packages)
    for dep in deps:
        project, specifier = _requirement_name_and_specifier(dep)
        if not specifier:
            continue

        available_version = available_versions.get(project)
        if available_version is None:
            raise EnvBuildError(
                "WASI wheel version cannot be verified for dependency "
                f"{dep!r}: requested {specifier!r}, but the fetched archive has "
                "available version <unknown>"
            )

        if _specifier_satisfied(specifier, available_version, dep):
            continue

        raise EnvBuildError(
            "WASI wheel version mismatch for dependency "
            f"{dep!r}: requested {specifier!r}, but the fetched archive provides "
            f"version {available_version!r}"
        )


def _available_distribution_versions(site_packages: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for dist_info in site_packages.rglob("*.dist-info"):
        if not dist_info.is_dir():
            continue
        name, version = _dist_info_name_version(dist_info)
        if name is None or version is None:
            continue

        normalized = _pep503_normalized_name(name)
        previous = versions.get(normalized)
        if previous is not None and previous != version:
            raise EnvBuildError(
                "WASI wheel archive contains multiple versions for distribution "
                f"{normalized!r}: {previous!r} and {version!r}"
            )
        versions[normalized] = version
    return versions


def _dist_info_name_version(dist_info: Path) -> tuple[str | None, str | None]:
    metadata_name, metadata_version = _metadata_name_version(dist_info / "METADATA")
    directory_name, directory_version = _dist_info_directory_name_version(dist_info)
    return metadata_name or directory_name, metadata_version or directory_version


def _metadata_name_version(metadata: Path) -> tuple[str | None, str | None]:
    try:
        lines = metadata.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None, None

    name: str | None = None
    version: str | None = None
    for line in lines:
        key, separator, value = line.partition(":")
        if separator != ":":
            continue
        normalized_key = key.lower()
        if normalized_key == "name":
            name = value.strip()
        elif normalized_key == "version":
            version = value.strip()
        if name is not None and version is not None:
            break
    return name, version


def _dist_info_directory_name_version(dist_info: Path) -> tuple[str | None, str | None]:
    suffix = ".dist-info"
    if not dist_info.name.endswith(suffix):
        return None, None

    stem = dist_info.name[: -len(suffix)]
    if "-" not in stem:
        return None, None

    name, version = stem.rsplit("-", 1)
    return name, version


def _requirement_name_and_specifier(requirement: str) -> tuple[str, str]:
    try:
        from packaging.requirements import InvalidRequirement, Requirement
    except ImportError:
        return _fallback_requirement_name_and_specifier(requirement)

    try:
        parsed = Requirement(requirement)
    except InvalidRequirement as e:
        raise EnvBuildError(f"dependency requirement is not valid PEP 508: {requirement!r}") from e
    return _pep503_normalized_name(parsed.name), str(parsed.specifier)


def _fallback_requirement_name_and_specifier(requirement: str) -> tuple[str, str]:
    match = _PROJECT_NAME.match(requirement)
    if match is None:
        raise EnvBuildError(f"dependency requirement has no PEP 508 project name: {requirement!r}")

    remainder = requirement[match.end() :].strip()
    if remainder.startswith("["):
        extras_end = remainder.find("]")
        if extras_end != -1:
            remainder = remainder[extras_end + 1 :].strip()
    specifier = remainder.split(";", 1)[0].strip()
    return _pep503_normalized_name(match.group(1)), specifier


def _specifier_satisfied(specifier: str, available_version: str, requirement: str) -> bool:
    try:
        from packaging.specifiers import InvalidSpecifier, SpecifierSet
        from packaging.version import InvalidVersion
    except ImportError:
        return _fallback_specifier_satisfied(specifier, available_version, requirement)

    try:
        return SpecifierSet(specifier).contains(available_version, prereleases=True)
    except InvalidSpecifier as e:
        raise EnvBuildError(
            f"dependency requirement {requirement!r} has invalid version specifier {specifier!r}"
        ) from e
    except InvalidVersion as e:
        raise EnvBuildError(
            "WASI wheel version cannot be verified for dependency "
            f"{requirement!r}: requested {specifier!r}, but the fetched archive provides "
            f"an invalid version {available_version!r}"
        ) from e


def _fallback_specifier_satisfied(
    specifier: str,
    available_version: str,
    requirement: str,
) -> bool:
    compact_specifier = specifier.replace(" ", "")
    if "," in compact_specifier:
        raise EnvBuildError(
            "packaging is required in the build toolchain to verify compound dependency "
            f"specifier {specifier!r} for {requirement!r}"
        )
    if compact_specifier.startswith("==="):
        expected = compact_specifier[3:]
    elif compact_specifier.startswith("=="):
        expected = compact_specifier[2:]
    else:
        raise EnvBuildError(
            "packaging is required in the build toolchain to verify dependency "
            f"specifier {specifier!r} for {requirement!r}"
        )

    return available_version == expected or _fallback_normalized_version(
        available_version
    ) == _fallback_normalized_version(expected)


def _fallback_normalized_version(version: str) -> str:
    return re.sub(r"[-_.]+", ".", version.strip().lower().removeprefix("v"))
