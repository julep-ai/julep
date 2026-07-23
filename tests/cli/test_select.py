# tests/cli/test_select.py
from julep.cli.config import load_config
from julep.cli.model import build_module
from julep.cli.select import select


def names(agents):
    return sorted(a.name for a in agents)


def test_select_by_name(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "triage")) == ["triage"]


def test_select_by_tag(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "tag:support")) == ["triage"]


def test_select_union_and_intersection(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "triage escalate")) == ["escalate", "triage"]   # space = union
    assert names(select(m, "tag:support,triage")) == ["triage"]            # comma = intersection


def test_select_path_glob(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "path:pkg/*.py")) == ["escalate", "support_bot", "triage"]


def test_empty_selector_returns_all(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "")) == ["escalate", "support_bot", "triage"]


def test_exclude(sample_module):
    m = build_module(load_config(sample_module))
    assert names(select(m, "", exclude="tag:support")) == ["escalate", "support_bot"]
