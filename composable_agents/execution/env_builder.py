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


def _pep503_normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


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
        _verify_pinned_versions(deps, site_packages)

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


def _safe_extract(tar: tarfile.TarFile, target: Path) -> None:
    root = target.resolve()
    for member in tar.getmembers():
        destination = (target / member.name).resolve()
        if not str(destination).startswith(f"{root}/") and destination != root:
            raise EnvBuildError(f"WASI wheel archive contains unsafe path: {member.name!r}")
    tar.extractall(target)
