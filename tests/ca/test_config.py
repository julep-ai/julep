from julep.ca.config import load_config


def test_defaults_when_no_config(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.src == [str(tmp_path)]
    assert cfg.exclude == []
    assert cfg.tags == {}
    assert cfg.fail_severity == "error"


def test_reads_tool_ca_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca]\nsrc = ["agents"]\nexclude = ["x_*.py"]\n'
        '[tool.ca.tags]\ntriage = ["support"]\n'
        '[tool.ca.gates]\nfail_severity = "warning"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.src == ["agents"]
    assert cfg.exclude == ["x_*.py"]
    assert cfg.tags == {"triage": ["support"]}
    assert cfg.fail_severity == "warning"


def test_ca_toml_overrides_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[tool.ca]\nsrc = ["a"]\n', encoding="utf-8")
    (tmp_path / "ca.toml").write_text('src = ["b"]\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.src == ["b"]
