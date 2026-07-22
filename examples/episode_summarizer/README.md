# Episode summarizer example

This sample is the Julep v3 "after" picture of the mem-mcp episode-summary lane. The
older flow used a large `seq`/`par`/`alt`/`arr` combinator tree plus adapter pures to
reshape every tool result. Here, record binding builds MCP arguments directly,
field access lowers to `std.pluck`, and `summary | source` / `write_summary |
write_one_liner` lower to `std.merge`. The only custom pures are the found predicate,
the not-found terminal, and the batch status reducer.

The flow reads each episode from an authenticated `memory-tools` MCP server, produces
a short summary and one-liner, and writes the two surfaces separately under the same
source-hash stale guard. Both writes feed the returned status record, so dataflow
dead-code elimination cannot discard either side effect.

## Keyless demo

The offline demo compiles against the same frozen MCP listings and injects deterministic
fake MCP and reasoner callers. It needs no services or credentials:

```bash
uv run --no-sync python -m examples.episode_summarizer.flow
```

## Live full stack

The live harness starts Temporal, an authenticated streamable-HTTP MCP server, the
Julep API, and an in-process release-pinned worker. It publishes the application into
a temporary file artifact store, activates the release, submits the batch through `/v1/runs`,
consumes projection SSE through the terminal event, fetches the result, and renders a
remote Julep trace. It uses real Anthropic API calls for three short found episodes;
the missing fourth id exercises the no-model not-found branch.

Prerequisites are an `ANTHROPIC_API_KEY`, the `temporal` CLI, and PostgreSQL. Point at
an existing database with `EPISODE_E2E_PG_DSN`; otherwise the harness uses Docker
to start and remove `postgres:16`.

```bash
EPISODE_E2E_PG_DSN='postgresql://...' \
  uv run --no-sync python -m examples.episode_summarizer.run_live
```

Useful environment variables:

- `ANTHROPIC_API_KEY`: required by the live worker and read by `any-llm` at runtime.
- `EPISODE_E2E_PG_DSN`: optional existing PostgreSQL DSN; avoids Docker lifecycle.
- `EPISODE_SUMMARIZER_MODEL`: flow default is `anthropic:claude-sonnet-5`.
- `EPISODE_ONE_LINER_MODEL`: flow default is `openai:gpt-4o-mini`.

The harness generates ephemeral MCP Ed25519, bundle Ed25519, payload AES-GCM, and API
keys in memory. It sets `EPISODE_TOOLS_URL`, `JULEP_MCP_*`, `JULEP_ARTIFACT_STORE_URL`,
`JULEP_BUNDLE_ALLOWED_SIGNERS`, and the matching server/worker payload settings for the
duration of the run, then restores the caller's environment and tears down every
service.

The checked-in one-liner default intentionally remains the stable OpenAI model
`openai:gpt-4o-mini`. The OpenAI credential in the development environment used for
this sample is invalid, so the live CLI and test override that model to
`anthropic:claude-haiku-4-5-20251001`; no live OpenAI request is attempted. Override
the summarizer on the CLI if lower cost is preferred:

```bash
uv run --no-sync python -m examples.episode_summarizer.run_live \
  --summarizer-model anthropic:claude-haiku-4-5-20251001
```

The expensive pytest coverage is opt-in and self-skips when a prerequisite is absent:

```bash
EPISODE_E2E_PG_DSN='postgresql://...' \
  uv run --no-sync python -m pytest tests/test_episode_summarizer_live_e2e.py -m live -s
```
