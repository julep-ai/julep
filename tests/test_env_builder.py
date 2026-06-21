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
