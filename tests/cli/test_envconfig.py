from julep.cli.config import EnvConfig, load_config


def test_implicit_local_env_present_by_default(tmp_path):
    """With no config, an implicit `local` env always exists."""
    cfg = load_config(tmp_path)
    assert "local" in cfg.envs
    local = cfg.envs["local"]
    assert isinstance(local, EnvConfig)
    assert local.name == "local"
    # local cas defaults to `.julep/cas` (a local path URI)
    assert local.cas is not None
    assert local.cas.endswith(".julep/cas")
    # local has no Temporal target
    assert local.temporal_address is None
    # canonical defaults
    assert local.temporal_namespace == "default"
    assert local.task_queue == "julep"
    assert local.langfuse_host is None


def test_existing_config_fields_unchanged(tmp_path):
    """EnvConfig support must not disturb the existing JulepConfig fields/behavior."""
    cfg = load_config(tmp_path)
    assert cfg.src == [str(tmp_path)]
    assert cfg.exclude == []
    assert cfg.tags == {}
    assert cfg.fail_severity == "error"


def test_env_table_parses_from_pyproject(tmp_path):
    """A [tool.julep.env.<name>] table parses the environment fields."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.julep]\n"
        'src = ["agents"]\n'
        "[tool.julep.env.staging]\n"
        'temporal_address = "temporal.staging:7233"\n'
        'temporal_namespace = "staging-ns"\n'
        'task_queue = "julep-staging"\n'
        'cas = "s3://my-bucket/julep-prefix"\n'
        'langfuse_host = "https://lf.staging"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert "staging" in cfg.envs
    staging = cfg.envs["staging"]
    assert staging.name == "staging"
    assert staging.temporal_address == "temporal.staging:7233"
    assert staging.temporal_namespace == "staging-ns"
    assert staging.task_queue == "julep-staging"
    assert staging.cas == "s3://my-bucket/julep-prefix"
    assert staging.langfuse_host == "https://lf.staging"
    # implicit local still present alongside parsed envs
    assert "local" in cfg.envs


def test_env_table_uses_canonical_defaults_for_missing_fields(tmp_path):
    """An env table needs only override what it wants; the rest take canonical defaults."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.julep.env.prod]\n"
        'temporal_address = "temporal.prod:7233"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    prod = cfg.envs["prod"]
    assert prod.temporal_address == "temporal.prod:7233"
    assert prod.temporal_namespace == "default"
    assert prod.task_queue == "julep"
    assert prod.cas is None
    assert prod.langfuse_host is None


def test_julep_toml_overrides_env_field(tmp_path):
    """julep.toml overrides one env field with the usual precedence."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.julep.env.staging]\n"
        'temporal_address = "temporal.staging:7233"\n'
        'temporal_namespace = "from-pyproject"\n',
        encoding="utf-8",
    )
    (tmp_path / "julep.toml").write_text(
        "[env.staging]\n"
        'temporal_namespace = "from-julep-toml"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    staging = cfg.envs["staging"]
    # overridden field comes from julep.toml
    assert staging.temporal_namespace == "from-julep-toml"
    # non-overridden field still comes from pyproject
    assert staging.temporal_address == "temporal.staging:7233"


def test_julep_toml_can_override_implicit_local(tmp_path):
    """A user may point the implicit local env's cas at a custom path."""
    (tmp_path / "julep.toml").write_text(
        "[env.local]\n"
        'cas = "/custom/cas/dir"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    local = cfg.envs["local"]
    assert local.name == "local"
    assert local.cas == "/custom/cas/dir"
    # local stays Temporal-less even when overridden
    assert local.temporal_address is None
