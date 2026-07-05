import base64
from julep.execution.langfuse import LangfuseConfig

def test_endpoint_and_headers():
    cfg = LangfuseConfig(host="https://lf.example.com/", public_key="pk", secret_key="sk")
    assert cfg.endpoint() == "https://lf.example.com/api/public/otel/v1/traces"
    h = cfg.headers()
    assert h["x-langfuse-ingestion-version"] == "4"
    assert h["Authorization"] == "Basic " + base64.b64encode(b"pk:sk").decode()

def test_from_env(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://h")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "p")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "s")
    cfg = LangfuseConfig.from_env()
    assert cfg.host == "https://h" and cfg.public_key == "p" and cfg.secret_key == "s"
