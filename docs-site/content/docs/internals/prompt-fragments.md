---
title: "Prompt Fragments"
description: "Prompt fragments and how they assemble."
---

**Status: proposed (design).** Let a `Reasoner`'s system prompt be computed by a
**registered renderer** — a pure, name-addressed `Context -> str` — referenced by
name on the reasoner, reading a per-invoke **projected context** that does not exist
in the runtime today. Additive and deploy-safe: `Reasoner.system: str` stays as the
literal/fallback; a new `system_render: Optional[str]` carries the renderer name.
Only **strings** (`system` + `system_render`) ever enter the deploy artifact, so
canonical-JSON artifact hashing and the cross-language corpus keep working. The
`Fragment` ADT (`Reader`/string-monoid combinators) is the *authoring builder*
for a renderer; what crosses deploy is the registered name, exactly like a pure.
It references [the Specification](/docs/internals/specification) (§6.4 pure-function drift, §8.2 WHOLE_SESSION
degradation, §10 agent loop), [the Typed Flow Calculus](/docs/internals/typed-flow-calculus) (the `project`/`decide`
model), and [the Typed Flow Calculus](/docs/internals/typed-flow-calculus) (freeze-isolation: every callable is
named/registered before freeze).

## Motivation — two gaps, not one

`Reasoner.system` is a static `str` (`dotctx.py:42`). To make a prompt react to
context you tool-assemble the upstream `payload`; the prompt itself stays inert.
`algebra.hs` models what's missing — `decide reasoner x ctx` with `ctx = project
(ctxPolicy reasoner) s x` — but that is the **formal model**, not the code. Two real
gaps in the Python:

1. **No projected context at the invoke boundary.** The interpreter passes only
   `(reasoner, value, cid)` to `env.invoke_reasoner` (`execution/interpreter.py`), and
   the Temporal `InvokeReasonerInput` carries only `reasoner`/`value`/`cid`
   (`execution/activities.py`). There is no `Context` object for a prompt to read.
2. **No way to compute a prompt from context.** `system` is a constant handed
   straight to the LLM caller; existing callers may read `reasoner.system` as a
   plain string.

So this is **not** "expose what the loop already gives you" — that context isn't
there. We add both: a context projection at the invoke boundary, and a renderer
that consumes it. Doing it the durable way (named renderers, not inline Python
objects) is what keeps deploy and cross-language honest.

## The model — a renderer is a registered pure `Context -> str`

```python
Context = Mapping[str, Any]      # the projected value (see "The projection path")
Renderer = Callable[[Context], str]   # registered by name in DEFAULT_REGISTRY, like a pure
```

`Reasoner` gains one optional **string** field; `system` stays a `str`:

```python
@dataclass(frozen=True)
class Reasoner:
    system: str = ""                       # literal / fallback (unchanged)
    system_render: Optional[str] = None    # registered renderer name (new; a string)
    ...

def render_system(reasoner: Reasoner, ctx: Context) -> str:
    if reasoner.system_render is not None:
        return DEFAULT_REGISTRY.get_renderer(reasoner.system_render)(ctx)
    return reasoner.system
```

`render_system` is called where the system prompt is materialized — inside
`invokeReasoner` (`execution/activities.py`), the one place `ctx` is in tool — and
its **`str`** result is what every existing LLM caller sees. Reasoners without a
renderer are byte-for-byte unchanged; `reasoner.system` never becomes a non-string,
so no downstream `reasoner.system` reader breaks.

### The Fragment ADT — an authoring builder for renderers

A `Fragment` is `Reader[Context, str]` valued in the string monoid. It is the
*authoring* convenience; `register_renderer(name, fragment)` registers its
`.render` as a named `Renderer`. The ADT is a **closed set of frozen dataclasses,
each with a concrete `render` method** — no `typing.Protocol` + `isinstance`
(that needs `@runtime_checkable` and is avoided here entirely):

```python
@dataclass(frozen=True)
class Lift:    text: str;                                    # Reader unit (constant)
@dataclass(frozen=True)
class Ask:     key: str; fmt: Callable[[Any], str] = str     # read one Context field
@dataclass(frozen=True)
class Concat:  parts: tuple["Fragment", ...]                 # string-monoid op; identity = Lift("")
@dataclass(frozen=True)
class Under:   project: Callable[[Context], Context]; body: "Fragment"   # Reader.local / contramap env
@dataclass(frozen=True)
class Map:     body: "Fragment"; fn: Callable[[str], str]    # fmap on the rendered output
# each defines .render(self, ctx) -> str; Fragment = Union[Lift, Ask, Concat, Under, Map]

def fragments(*parts: "Fragment | str") -> "Fragment":
    return Concat(tuple(p if isinstance(p, (Lift, Ask, Concat, Under, Map)) else Lift(p) for p in parts))

# authoring:
register_renderer("research.system.v1", fragments(
    "You are a careful research agent.\n\n",
    Ask("persona", fmt=lambda p: f"Persona: {p}\n"),
    Under(lambda c: c["task"], TASK_BLOCK),     # render TASK_BLOCK against ctx["task"]
    Ask("trace", fmt=summarize_trace),           # fold the trace slice -> str
))
Reasoner(name="researcher", model="claude-opus-4-8", system_render="research.system.v1")
```

`Under` is the variance point made concrete: a template *consumes* its
environment, so it is contravariant in `Context` — `Under` is Reader's `local`.
`Concat` is the string-monoid combine (identity `Lift("")`), which is what lets
overlapping-context fragments assemble into one prompt without threading a dict by
tool.

### The projection path (the new wiring — gap #1)

This is the real work, and the spec owns it explicitly. Extend the invoke
boundary so the activity computes `Context` from `(value, reasoner.context_scope,
session)` and passes it to `render_system`:

- `InvokeReasonerInput` / `env.invoke_reasoner` gain the projected `Context` (or the
  inputs to compute it). `Context` = the leaf `value` plus the session slice that
  `reasoner.context_scope` (`ContextScope` / `ContextPolicy`) already authorizes —
  `NoCtx` → just `value`; `Local` → value + local thread; `WholeSession` → value +
  the full (degraded, [SPEC §8.2](/docs/internals/specification#82-whole_session-degradation)) slice.
- For the agent loop, the round payload `{"input": state.last, "trace": [...]}`
  (`agent_loop.py:451`) is the natural `Context` for a controller reasoner.

The projection *is* the security boundary (gap #7, below): a renderer can only
read what `project(ctxPolicy)` put in `Context`, so it **cannot widen
`ctxPolicy`** — not because the renderer is trusted, but because the narrowed
`Context` is the only thing it's handed.

## Deploy, drift, and cross-language (gaps #6/#8 — solved, not deferred)

- **Artifact stays string-only.** `deploy.py` canonical-JSON-hashes `reasoner.system`
  (`deploy.py:143,181,201`). With this design the artifact carries `system`
  (str) + `system_render` (str **name**) — both serializable. A `Fragment`
  object never touches the wire. No artifact-hash breakage.
- **Drift detection like a pure.** The renderer's *body* is not in the artifact;
  its **name + content hash** is registered exactly like a pure
  ([SPEC §6.4 pure-function drift](/docs/internals/specification#64-pure-function-drift)), so a
  silently-changed renderer is caught on replay the same way a changed pure is.
- **Cross-language.** Another runtime registers a renderer under the same name
  (the pures discipline). The corpus pins the *name*, not Python.

## Enforcement honesty (gap #7)

`Ask.fmt`, `Under.project`, `Map.fn` are arbitrary Python callables — they
*could* read a clock or do I/O. The guarantee is therefore **exactly the pure
contract, no stronger**: a renderer must register as pure, and an impure renderer
is the same violation as an impure `arr` pure, caught by the same §6.4 drift/
purity discipline at registration — not a new, stronger static guarantee. If we
want it airtight, restrict fragments to a *closed combinator set* with no
user callables (open question below). The spec asserts the contract and names the
registry as the enforcement point; it does not pretend the callables are
sandboxed.

## The through-line (and the pomset caveat)

`Ask("trace", fmt=summarize_trace)` is where this meets
[Agent Loop As Turn](/docs/internals/agent-loop-as-turn): a **monoid homomorphism**
`trace → str` lifted into a `Reader`, consumed by a round the loop iterates. But
`Session`/`trace` is a *pomset*, not a free monoid (`algebra.hs:133–137`) — with
real `:***` concurrency, independent branches have **no canonical order**. So
`summarize_trace` must be **order-insensitive** (a multiset/by-key summary) or
read an explicit linearization, and it should summarize *its already-projected
slice*, never re-derive global history. Summarization is generally **not** a
homomorphism (`summarize(a++b) ≠ summarize(a)++summarize(b)`), which is why
compaction lives at the Sub firewall (`SummaryPolicy`,
[SPEC §8.2](/docs/internals/specification#82-whole_session-degradation)), not inline.

## Invariants preserved (checklist)

- **`reasoner.system` stays `str`** — renderer output is a string; no downstream
  `reasoner.system` reader breaks (the additive promise, kept literally).
- **Artifact / golden / cross-language** — only strings (`system`,
  `system_render`) are hashed; the renderer is name+hash-registered like a pure;
  hashes don't move for existing string reasoners.
- **Context honesty (`algebra.hs` law 2).** A renderer reads only the projected
  `Context`; it cannot reach global session state or widen `ctxPolicy`, because
  the projection is what builds `Context`.
- **Determinism / freeze isolation ([the Typed Flow Calculus](/docs/internals/typed-flow-calculus)).** A
  renderer is a registered pure — the same named-before-freeze rule as every
  other callable; drift caught by §6.4.

## Phasing

1. **The projection path.** Compute `Context` at the invoke boundary
   (`InvokeReasonerInput` / `env.invoke_reasoner`) from `(value, context_scope,
   session)`. No prompt change yet — just make `Context` exist. Tests: existing
   reasoners render identically (no renderer ⇒ `system` verbatim).
2. **Renderer registry + `Reasoner.system_render` + `render_system`** wired into
   `invokeReasoner`. Existing string reasoners untouched.
3. **Fragment ADT** (`Lift`/`Ask`/`Concat`/`Under`/`Map`) + `register_renderer` +
   `fragments()` + the order-insensitive `summarize_trace` example.
4. **Drift/determinism parity** for renderers (§6.4 content-hash + purity gate)
   and cross-language same-name registration.

## Open questions

- **Context contract.** Pin the exact `Context` mapping each `ContextScope`
  projects, so renderer authors have a stable surface (phase 1).
- **Closed combinators vs callables.** Allow `Ask.fmt`/`Under.project`/`Map.fn`
  arbitrary callables (flexible, pure-by-contract), or restrict to a closed
  combinator set (airtight, less expressive)? (Gap #7.)
- **YAML reach.** Let `settings.yaml` carry `system_render: <name>` (just a
  string ref), keeping inline `system:` string-only? (Lean yes — it's a name.)

## Non-goals

- A templating language (Jinja/format-string DSL). Renderers are Python values
  built from typed combinators, registered by name.
- Putting `Fragment` objects on the wire — only names cross deploy.
- Changing `ContextScope`/`ContextPolicy` or what each scope projects.
- Type-safety across the model/LLM boundary (the reply is still honestly `Any`).

<!-- ported-by ca-docs-site: internals/prompt-fragments -->
