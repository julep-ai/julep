# Gotchas & FAQ

The recurring traps when authoring with `composable_agents`, and how to get
unstuck. Most of these surface as a define-time diagnostic with a `fix:` line —
read that first. Deep references: [Authoring Guide](AUTHORING.md) ·
[Capabilities & Safety](capabilities-and-safety.md) · [Concepts](concepts.md).

## Define-time vs runtime

**The single biggest source of confusion.** A `@flow` body runs **once at define
time** to build a graph. The values you handle are `Handle`s, not data. A step
call (`my_tool(h)`, `think(...)`, `h["key"]`) **appends graph structure** — it
does not execute and does not return a real value you can branch on.

So this **fails** at define time:

```python
@flow
def bad(x):
    hit = lookup(x)
    if hit["found"]:          # ✗ Handle truthiness — there's no runtime value yet
        return think("a", hit)
    return think("b", hit)
```

Express control flow with graph constructs instead:

```python
@flow
def good(x):
    hit = lookup(x)
    return cond(found_pred, hit, then=branch_a, orelse=branch_b)   # registered pure predicate
```

Anything that needs a *runtime* value — looping over data, inspecting a result,
calling out — belongs **inside** a `@tool`, `@pure`, or reasoner handler, not in
the flow body. ([the model](concepts.md))

## Determinism contract

Every callable used on a `Handle` must be **registered by its raw function
source** with `@tool` or `@pure`. Pins are source hashes, so:

- **No wrappers, closures, or lambdas** as registered tools/pures. Register the
  raw `def`.
- **Captured constants must be canonical JSON** and small. Captured handles must
  come from the **enclosing** graph (no foreign-scope captures).
- **No secrets in the flow.** Credentials are banned from captures and static
  args — they belong in environment-backed tools or run principals, never in the
  frozen artifact.

Full rules: [Determinism Contract](AUTHORING.md#determinism-contract).

## Define-time error → rewrite

| Diagnostic | Rewrite |
|---|---|
| Handle truthiness or iteration | Use `cond(...)`, `switch(...)`, or `each(...)`. |
| Unregistered callable on a handle | Decorate with `@pure`/`@tool`, or call `think(...)`. |
| Unsaturated flow | Apply the flow to handles / bind captures by keyword / pass it to `each`. |
| Rebinding or tuple-unpacking a handle | Assign each step to one graph name, or pass `name=`. |
| Unused `@flow` parameter | Remove it or use it — unused params are **blocking**. |
| Foreign-scope handle capture | Capture only handles from the enclosing graph. |
| Invalid / oversized / secret-shaped capture | Keep captures small canonical JSON; move secrets out. |
| Non-handle return | Return a handle produced by the authored graph. |

Names come from the function's AST source when available; use `name=` as the
explicit escape hatch (REPL/`exec` contexts fall back to generated names).

## Capability denials (deny-by-default)

A tool the flow wasn't granted is **denied**, not routed somewhere surprising:

```text
- [CAP_TOOL_DENIED@$] error: tool 'srv/denied' is not granted
    --> app.py:42  (call(mcp("srv", "denied")))
    fix: Add this tool to the capability manifest's tools: allow-list, or remove the call.
```

Fix: grant it in `deploy(..., tools=[...] / reasoners=[...])` (or the capability
manifest for kernel flows), or remove the call. [Capabilities & Safety →](capabilities-and-safety.md)

## Approval gates for dangerous actions

A tool declared `effect="dangerous"` (or approval-required) **must sit behind**
`human_gate(...)`. Strict deploy refuses any ungated path to it — that's by
design, not a bug. Put the gate immediately before the effect:
`draft -> human_gate -> send`. See `examples/email_approval.py`.

## dev mode vs strict

Strict is the **default** and is what production runs. While iterating, use
`deploy(..., mode="dev")` / `Agent(..., mode="dev")`: it keeps compiling/running
locally but **retains** the diagnostics strict prod would block on.

- `deployment.prod_gap_summary()` → exactly what strict prod would reject.
- `result.prod_gap` → same, on a run result.
- **Temporal stays prod-strict.** `Deployment.run(...)` rejects dev-mode
  deployments and `Agent.deploy(...)` uses the strict path — so "works in dev"
  does not mean "deploys." Clear the prod gap before shipping.

## Keyless default reasoner

If you build an `Agent` without `llm=`, it does **not** call a model. It uses a
keyless default reasoner that emits **one** `RuntimeWarning` and returns the
input unprocessed. That's intentional for keyless local iteration — but if your
agent "does nothing," check whether you forgot to wire `llm=`. For a real model,
pass a controller (or `make_local_reasoner()` with the `providers` extra).

## PEP 723 metadata placement (load-bearing footgun)

A pure declares third-party deps with a `# /// script` block. `register_pure`
captures source via `inspect.getsource`, which **only sees from the decorator
line through the function body** — *not* a module-top block.

A module-top block is **silently dropped**: the pure publishes as no-dependency,
deploy passes (the import works on the native host), then the **wasm-tier run
fails at import**. Place the block **between `@pure(...)` and `def`**:

```python
@pure("cad.extract_emails.v1")
# /// script
# dependencies = ["regex==2024.11.6"]
# requires-python = ">=3.11"
# ///
def extract_emails(record: dict) -> dict:
    import regex
    ...
```

Supported WASI wheels are exactly `pydantic-core` and `regex`. Off-list deps
(e.g. `numpy`) only run on the **native tier**, which is opt-in per pure via the
`CA_PURE_NATIVE_DEPS` allowlist at both publish and worker. Details:
[Authoring Guide §Dependencies](AUTHORING.md#third-party-dependencies-on-pures-pep-723).

## Verify gates

Run the same checks CI runs before pushing
([CONTRIBUTING](../CONTRIBUTING.md#running-the-checks)):

```bash
ruff check composable_agents
python -m mypy composable_agents
python -m pytest -q
```

- Use **`python -m pytest`**, not bare `pytest`, so it runs against the project's
  interpreter and resolves the package correctly.
- The pure core must stay free of `temporalio`; only `composable_agents/execution/`
  may import it. `mypy` and `ruff` must be clean and public APIs stay typed.
- Tests run both with Temporal **absent** and **present** — `HAVE_TEMPORAL`
  gates the runtime, and the authoring path must pass either way.

## "The golden hashes changed and CI is red"

`tests/golden/` is the cross-language wire-format contract. A moved pin means the
IR, manifest JSON, diagnostics, or shape projection changed. If that change was
**intentional**, regenerate and review the diff as part of the change:

```bash
python -m tests.golden.regenerate --update
```

If a pin moved and you didn't mean to change the wire format, **stop and
investigate** — something in the compile path shifted.
[Golden corpus rules →](../CONTRIBUTING.md#the-golden-corpus-is-a-contract)
