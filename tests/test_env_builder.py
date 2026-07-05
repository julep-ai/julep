from __future__ import annotations

from pathlib import Path

import pytest

from julep.execution import env_builder


def _write_dist_info(site_packages: Path, name: str, version: str) -> None:
    dist_info = site_packages / f"{name}-{version}.dist-info"
    dist_info.mkdir(parents=True)
    dist_info.joinpath("METADATA").write_text(
        f"Metadata-Version: 2.3\nName: {name}\nVersion: {version}\n",
        encoding="utf-8",
    )


def test_verify_pinned_versions_accepts_matching_version(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    _write_dist_info(site_packages, "regex", "2024.11.6")

    env_builder._verify_pinned_versions(("regex==2024.11.6",), site_packages)


def test_verify_pinned_versions_rejects_mismatched_exact_pin(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    _write_dist_info(site_packages, "regex", "2024.11.6")

    with pytest.raises(env_builder.EnvBuildError) as excinfo:
        env_builder._verify_pinned_versions(("regex==2023.12.25",), site_packages)

    message = str(excinfo.value)
    assert "regex==2023.12.25" in message
    assert "==2023.12.25" in message
    assert "2024.11.6" in message


def test_verify_pinned_versions_allows_name_only_requirement(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    _write_dist_info(site_packages, "regex", "2024.11.6")

    env_builder._verify_pinned_versions(("regex",), site_packages)


def test_verify_pinned_versions_matches_pep503_normalized_dist_info_name(
    tmp_path: Path,
) -> None:
    site_packages = tmp_path / "site-packages"
    _write_dist_info(site_packages, "pydantic_core", "2.41.5")

    env_builder._verify_pinned_versions(("pydantic-core==2.41.5",), site_packages)


def test_verify_pinned_versions_uses_dist_info_directory_version_when_metadata_missing(
    tmp_path: Path,
) -> None:
    site_packages = tmp_path / "site-packages"
    site_packages.joinpath("regex-2024.11.6.dist-info").mkdir(parents=True)

    env_builder._verify_pinned_versions(("regex==2024.11.6",), site_packages)


def test_verify_pinned_versions_rejects_when_pinned_distribution_absent(
    tmp_path: Path,
) -> None:
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir(parents=True)

    with pytest.raises(env_builder.EnvBuildError) as excinfo:
        env_builder._verify_pinned_versions(("regex==2024.11.6",), site_packages)

    assert "regex==2024.11.6" in str(excinfo.value)


def test_build_env_component_rejects_unpinned_requirement_before_network() -> None:
    with pytest.raises(env_builder.EnvBuildError) as excinfo:
        env_builder.build_env_component(("regex",), ">=3.11")

    message = str(excinfo.value)
    assert "regex" in message
    assert "exact-version pins" in message


@pytest.mark.skipif(
    not (env_builder._WASM_ROOT / "wit_world").is_dir(),
    reason="requires generated _wasm/wit_world bindings (produced by the wasm build)",
)
def test_build_env_component_accepts_exact_pin_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Wheels are local-first (vendored under _wasm/wasi_wheels/), so the exact-pin
    # and dist-info version guards run against the real vendored regex package.
    # Stub only componentize-py so this stays a fast guard test, not a wasm build.
    observed: dict[str, bool] = {}

    def fake_run(
        command: list[str],
        *,
        cwd: Path,  # noqa: ARG001
        check: bool,  # noqa: ARG001
    ) -> object:
        # The temp site-packages is cleaned up when build_env_component returns, so
        # assert per-dep isolation here while it still exists: the declared dep was
        # staged and the other supported wheel (pydantic_core) was NOT dragged in.
        # Command tail is: --python-path <runtime> --python-path <site_packages>
        # env_component -o <output>, so site_packages is the 4th-from-last arg.
        site_packages = Path(command[-4])
        observed["invoked"] = True
        observed["has_regex"] = (site_packages / "regex").is_dir()
        observed["no_pydantic_core"] = not (site_packages / "pydantic_core").exists()
        output = Path(command[-1])
        output.write_bytes(b"component")
        return object()

    monkeypatch.setattr(env_builder.subprocess, "run", fake_run)

    path = env_builder.build_env_component(("regex==2024.11.6",), ">=3.11", out_dir=tmp_path)

    assert path.read_bytes() == b"component"
    assert observed.get("invoked"), "componentize-py was not invoked"
    assert observed["has_regex"]
    assert observed["no_pydantic_core"]
