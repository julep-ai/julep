# Observability and trajectory capture

Julep exposes two derived observability planes. The projection plane in
`julep/projection.py` is the per-run blueprint and observability view; the trajectory plane in
`julep/trajectory.py` stitches cross-run causal history into a future training-data plane.

## Redaction

`redact_secret_shaped` provides a secret-key floor. Its regular expression includes
`authorization` and `bearer`, while deliberately excluding bare `key` to avoid false positives
such as `cache_key`. Capture is fail-closed: if a redactor raises, the value is dropped and raw
data is never written. Payloads without matching keys are byte-preserved under canonical JSON
serialization.

Set `JULEP_REDACTION` to a JSON object, or configure `[tool.julep.redaction]` in
`pyproject.toml`. The environment variable wins when both are present. Supported fields are
`key_patterns`, `path_patterns`, and `disable_default`. Key patterns are regular expressions.
Path patterns are exact dot-separated paths where `*` matches one dictionary segment or one list
level; list indices are not supported. `serve()` installs the configured redactor as the default
`WorkerContext.redactor` only when the context factory left it unset. A factory-provided redactor
is authoritative.

```json
{
  "key_patterns": ["(?i)^customer_email$"],
  "path_patterns": ["items.*.private_note"],
  "disable_default": false
}
```

```toml
[tool.julep.redaction]
key_patterns = ["(?i)^customer_email$"]
path_patterns = ["items.*.private_note"]
disable_default = false
```

The full trajectory product—Postgres sink, blob-store product, and export pipelines—is deferred;
trajectory remains derived and best-effort. WS1 egress computes value references from
post-redaction bytes.
