# tests/ca/test_resolve.py
from julep.ca.config import load_config
from julep.ca.resolve import resolve_agent
from julep.ca.runner import run_agent_local


def test_resolve_flow_returns_ir_json(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "triage")
    assert resolved.name == "triage"
    assert resolved.ir["op"]  # serialized ir.Node has an "op" key
    assert resolved.error is None


def test_resolve_unknown_agent_reports_error(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "nope")
    assert resolved.error is not None
    assert "nope" in resolved.error


def test_resolve_agent_instance_by_name(sample_module):
    # support_bot is an Agent(...) instance whose name lives on ._name, not .name.
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "support_bot")
    assert resolved.error is None, resolved.error
    assert resolved.name == "support_bot"
    assert resolved.ir["op"]


def test_run_agent_instance_end_to_end(sample_module):
    cfg = load_config(sample_module)
    resolved = resolve_agent(cfg, "support_bot")
    assert resolved.error is None, resolved.error
    outcome = run_agent_local(cfg, "support_bot", "TICKET-1", run_id="run-bot-1")
    assert outcome.error is None, outcome.error
    assert outcome.run_id == "run-bot-1"


def test_resolve_surfaces_import_error(tmp_path):
    # A module that raises on import must surface the real error, not a bare
    # "not found".
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "broken.py").write_text(
        "import does_not_exist_xyz  # noqa\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca]\nsrc = ["pkg"]\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    resolved = resolve_agent(cfg, "whatever")
    assert resolved.error is not None
    assert "import errors" in resolved.error
    assert "broken" in resolved.error


def test_resolve_src_layout_with_intrapackage_import(tmp_path):
    # src/ layout: src/myapp/agents.py must import as myapp.agents with src/ on
    # sys.path so `from myapp.helper import ...` resolves.
    src = tmp_path / "src"
    app = src / "myapp"
    app.mkdir(parents=True)
    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "helper.py").write_text("PREFIX = 'hi'\n", encoding="utf-8")
    (app / "agents.py").write_text(
        "from julep import flow, think\n"
        "from myapp.helper import PREFIX\n"
        "@flow\n"
        "def greet(x: str) -> dict:\n"
        "    return think(PREFIX, x)\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca]\nsrc = ["src"]\n', encoding="utf-8"
    )
    from julep.ca.config import load_config
    from julep.ca.resolve import resolve_agent

    cfg = load_config(tmp_path)
    resolved = resolve_agent(cfg, "greet")
    assert resolved.error is None, resolved.error
    assert resolved.name == "greet"


def test_resolve_tolerates_user_stdout_noise(tmp_path):
    # User module-level prints (before AND simulated after) must not corrupt the
    # sentinel-delimited payload.
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "noisy.py").write_text(
        "print('banner line from user code')\n"
        "import atexit\n"
        "atexit.register(lambda: print('trailing atexit line'))\n"
        "from julep import flow, think\n"
        "@flow\n"
        "def chatty(x: str) -> dict:\n"
        "    return think('r', x)\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca]\nsrc = ["pkg"]\n', encoding="utf-8"
    )
    from julep.ca.config import load_config
    from julep.ca.resolve import resolve_agent

    cfg = load_config(tmp_path)
    resolved = resolve_agent(cfg, "chatty")
    assert resolved.error is None, resolved.error
    assert resolved.name == "chatty"
