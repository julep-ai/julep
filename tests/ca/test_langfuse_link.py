# tests/ca/test_langfuse_link.py
from composable_agents.ca.langfuse_link import trace_url
from composable_agents.execution.langfuse import trace_id_for


def test_url_uses_stable_trace_id(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.setenv("LANGFUSE_PROJECT_ID", "proj-123")
    url = trace_url("run-1")
    expected_hex = format(trace_id_for("run-1"), "032x")
    assert url == f"https://cloud.langfuse.com/project/proj-123/traces/{expected_hex}"


def test_url_falls_back_to_api_path_without_project(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.delenv("LANGFUSE_PROJECT_ID", raising=False)
    url = trace_url("run-1")
    assert url is not None
    assert url.endswith(f"/api/public/traces/{format(trace_id_for('run-1'), '032x')}")


def test_url_none_without_host(monkeypatch):
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    assert trace_url("run-1") is None
