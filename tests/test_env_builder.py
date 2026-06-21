from __future__ import annotations

from pathlib import Path

import pytest

from composable_agents.execution import env_builder


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


def test_build_env_component_accepts_exact_pin_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_download_and_extract_wasi_wheel(project: str, target: Path) -> None:
        _write_dist_info(target, project, "2024.11.6")

    def fake_run(
        command: list[str],
        *,
        cwd: Path,  # noqa: ARG001
        check: bool,  # noqa: ARG001
    ) -> object:
        output = Path(command[-1])
        output.write_bytes(b"component")
        return object()

    monkeypatch.setattr(
        env_builder,
        "_download_and_extract_wasi_wheel",
        fake_download_and_extract_wasi_wheel,
    )
    monkeypatch.setattr(env_builder.subprocess, "run", fake_run)

    path = env_builder.build_env_component(("regex==2024.11.6",), ">=3.11", out_dir=tmp_path)

    assert path.read_bytes() == b"component"
