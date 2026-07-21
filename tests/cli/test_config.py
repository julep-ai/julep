import pytest

from julep.cli.config import load_config


def test_defaults_when_no_config(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.src == [str(tmp_path)]
    assert cfg.exclude == []
    assert cfg.tags == {}
    assert cfg.fail_severity == "error"


def test_reads_tool_julep_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.julep]\nsrc = ["agents"]\nexclude = ["x_*.py"]\n'
        '[tool.julep.tags]\ntriage = ["support"]\n'
        '[tool.julep.gates]\nfail_severity = "warning"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.src == ["agents"]
    assert cfg.exclude == ["x_*.py"]
    assert cfg.tags == {"triage": ["support"]}
    assert cfg.fail_severity == "warning"


def test_julep_toml_overrides_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.julep]\nsrc = ["a"]\n',
        encoding="utf-8",
    )
    (tmp_path / "julep.toml").write_text('src = ["b"]\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.src == ["b"]


def test_legacy_ca_toml_errors_before_toml_parsing(tmp_path):
    (tmp_path / "ca.toml").write_text("this is not TOML = [", encoding="utf-8")

    with pytest.raises(ValueError, match=r"ca\.toml.*julep\.toml.*tool\.ca.*tool\.julep"):
        load_config(tmp_path)


def test_legacy_tool_ca_errors_before_strict_key_validation(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ca]\n"
        'src = ["legacy"]\n'
        "[tool.julep]\n"
        'srcc = ["typo"]\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"tool\.ca.*tool\.julep"):
        load_config(tmp_path)


def test_unknown_top_level_key_suggests_nearest_match(tmp_path):
    (tmp_path / "julep.toml").write_text('srcc = ["agents"]\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"unknown key 'srcc'.*did you mean 'src'"):
        load_config(tmp_path)


def test_unknown_nested_keys_are_rejected(tmp_path):
    (tmp_path / "julep.toml").write_text(
        "[env.prod]\n"
        'temporal_adress = "localhost:7233"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"unknown key 'temporal_adress'.*did you mean 'temporal_address'",
    ):
        load_config(tmp_path)

    (tmp_path / "julep.toml").write_text(
        "[schedule.hourly]\n"
        'cron = "0 * * * *"\n'
        'flow = "hourly"\n'
        "pausd = true\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"unknown key 'pausd'.*did you mean 'paused'"):
        load_config(tmp_path)

    (tmp_path / "julep.toml").write_text(
        "[gates]\nfail_severty = 'warning'\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"unknown key 'fail_severty'.*did you mean 'fail_severity'",
    ):
        load_config(tmp_path)

    (tmp_path / "julep.toml").write_text(
        "[env.prod.worker_secret_environment.API_KEY]\n"
        "secret_name = 'api'\n"
        "key = 'token'\n"
        "namespace = 'wrong-level'\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"unknown key 'namespace'"):
        load_config(tmp_path)


def test_future_sections_are_reserved_no_ops(tmp_path):
    (tmp_path / "julep.toml").write_text(
        "[mcp]\nenabled = true\n"
        "[pipeline]\nenabled = true\n"
        "[server]\nenabled = true\n"
        "[redaction]\nenabled = true\n",
        encoding="utf-8",
    )

    cfg = load_config(tmp_path)
    assert cfg.src == [str(tmp_path)]
