# `ca eval` mem-mcp Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the three real gaps that stop mem-mcp's actual eval suites from running correctly under `ca eval`: agent-loop output metadata (`_tool_calls`/`_rounds`), score-return normalization with metrics, and `--tag`/`--sample-name` filtering.

**Architecture:** All three changes land in the existing eval runner (`composable_agents/ca/evalrun.py`) plus thin CLI plumbing (`composable_agents/ca/cli.py`). No new modules. The tool-loop output becomes a `dict` subclass carrying mem-mcp's `OutputWithMetadata` attributes so both julep-style dict scorers and mem-mcp-style `getattr` scorers work on the same object.

**Tech Stack:** Python 3.11+, typer CLI, pytest with fake `acompletion` callables (no network).

## Why (evidence, verified 2026-07-04)

- All 5 real mem-mcp agent-loop suites (`record/execute`, `slack/bootstrap`, `threads/merge_evaluator`, `semantic/classification_reviewer`, `linear/ingest`) score via `getattr(output, "_tool_calls", [])` (and `record/execute` also `_rounds`). julep's `_run_tool_loop` returns a plain dict, so the `getattr` default fires and every suite **silently scores as if zero tools were called**. Not fixable from `eval.py` — the runner owns the loop.
- `evalrun.py` coerces with `s = float(value)`, so the tuple `(score, metrics)` returns of `record/plan` and `record/execute` hard-fail as exit-4 setup errors, and their metrics (consumed by mem-mcp's `eval_diff` reporter) are dropped.
- mem-mcp's routine workflow is tag-driven (`--tag prod`, `--tag prod_smoke` poe tasks; 24/24 suites tag samples). `ca eval` has no sample filtering.

Parity source of truth (mem-mcp repo at `/home/diwank/github.com/julep-ai/mem-mcp-c`):
- `packages/python/dotctx/src/dotctx/agent_loop_runner.py:22-55` — `OutputWithMetadata` contract; `_tool_calls` items are `{"id": str, "name": str, "args": <parsed args>}`.
- `packages/python/dotctx/src/dotctx/eval_runner.py:181-218` — score contract: a 0.0–1.0 number, or a 2-tuple `(number, metrics_dict)`.
- `tooling/scripts/run_prompt_eval.py:102-126` — filter semantics: tags are any-match set intersection; sample names are exact-match and unknown names error.

## Global Constraints

- Gates (run all three before every commit): `python -m pytest` (NOT bare `pytest`), `uv run mypy --strict composable_agents` (package only, not tests), `ruff check .`
- Mirror mem-mcp shapes exactly: `_tool_calls` items `{"id", "name", "args"}`; score contract number-or-2-tuple; tag filter = any-match intersection; unknown `--sample-name` = error.
- Intentional divergences (keep, and keep documented in docstrings): invalid score returns are **exit-4 setup errors** here (mem-mcp soft-fails that sample to 0.0 with an error string); an empty post-filter sample set is an exit-4 setup error (silent empty runs are worse); dict-returning `score()` stays unsupported (it does not work in mem-mcp's runner either — `briefs/propose_template` errors to 0.0 there).
- Backward compatibility: `SampleScore.to_json()` must omit `metrics` when absent so existing baseline JSON files and the report-shape test (`tests/ca/test_eval_cli.py:224`) stay valid; `from_json` must accept old reports without a `metrics` key.
- No version bump or PyPI publish in this plan.
- New tests go in `tests/ca/test_eval_cli.py`, using its existing conventions: `run` from conftest, `SingleShotFake`/`ToolLoopFake`, `_write_eval_ctx`, module-top `pytest.importorskip("jinja2")`/`importorskip("yglu")` guards (already present).

## File Structure

- Modify: `composable_agents/ca/evalrun.py` — `EvalOutput` class, call collection in `_run_tool_loop`, `_coerce_score`, `SampleScore.metrics`, filter params on `run_eval`/`run_eval_sync`.
- Modify: `composable_agents/ca/cli.py` — `--tag`/`--sample-name` options on `eval_cmd`.
- Test: `tests/ca/test_eval_cli.py` — all new tests.

---

### Task 1: `EvalOutput` — mem-mcp `OutputWithMetadata` parity for tool-loop scores

**Files:**
- Modify: `composable_agents/ca/evalrun.py` (class after `EvalReport` ~line 76; `_run_tool_loop` ~lines 218–335)
- Test: `tests/ca/test_eval_cli.py`

**Interfaces:**
- Consumes: `drive_agent_loop(...) -> dict[str, Any]` (unchanged), julep tool-call dicts `{"id", "tool", "input"}` from `reply["tool_calls"]`.
- Produces: `class EvalOutput(dict[str, Any])` with `__init__(output: Mapping[str, Any], tool_calls: list[dict[str, Any]], rounds: int)` and instance attrs `_tool_calls: list[dict[str, Any]]`, `_rounds: int`. `_run_tool_loop` now returns `EvalOutput`. Add `"EvalOutput"` to the existing `__all__` list at the bottom of `evalrun.py` (~line 438).

- [ ] **Step 1: Write the failing tests**

Add to `tests/ca/test_eval_cli.py` (extend the existing `evalrun` import at the top of the file with `EvalOutput`; add `import shutil` to the stdlib imports):

```python
def _write_tool_eval_ctx(tmp_path: Path, eval_py: str) -> Path:
    """Copy the vendored tool-loop fixture, swapping in a custom eval.py."""
    ctx = tmp_path / "tool_case.ctx"
    shutil.copytree(FIXTURES / "execute_eval.ctx", ctx)
    (ctx / "eval.py").write_text(eval_py, encoding="utf-8")
    return ctx


# Scores exactly the way real mem-mcp agent-loop suites do (record/execute,
# slack/bootstrap, ...): getattr(output, "_tool_calls", []) + "_rounds".
META_SCORER_EVAL = '''\
from typing import Any

from dotctx.eval_types import Sample, stop_after_turns


def sample(limit: int = -1) -> list[Sample]:
    samples = [
        Sample(
            name="meta_ok",
            input={"task": "store a memory"},
            expected=None,
            mock_tools={"record_memory": {"ok": True}},
            stop_on=stop_after_turns(4),
        ),
    ]
    return samples if limit is None or limit < 0 else samples[:limit]


def score(_input: dict[str, Any], output: Any, expected: Any) -> float:
    calls = getattr(output, "_tool_calls", [])
    rounds = getattr(output, "_rounds", None)
    if not calls or not isinstance(rounds, int) or rounds < 1:
        return 0.0
    if any(set(c) != {"id", "name", "args"} for c in calls):
        return 0.0
    if [c["name"] for c in calls] != ["record_memory"]:
        return 0.0
    if calls[0]["args"] != {"content": "hi"}:
        return 0.0
    if not isinstance(output, dict) or getattr(output, "content", None) is not None:
        return 0.0
    return 1.0
'''


def test_eval_output_is_dict_with_memmcp_metadata() -> None:
    out = EvalOutput({"trace": [1]}, [{"id": "c1", "name": "t", "args": {}}], 2)
    assert isinstance(out, dict)
    assert out.get("trace") == [1]
    assert out["trace"] == [1]
    assert out._tool_calls == [{"id": "c1", "name": "t", "args": {}}]
    assert out._rounds == 2
    assert getattr(out, "content", None) is None


def test_tool_loop_output_carries_memmcp_metadata(tmp_path: Path) -> None:
    ctx = _write_tool_eval_ctx(tmp_path, META_SCORER_EVAL)
    report = run(
        run_eval(str(ctx), acompletion=ToolLoopFake("record_memory", '{"content": "hi"}'))
    )
    assert report.scores[0].id == "meta_ok"
    assert report.scores[0].score == 1.0
    assert report.passed is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/ca/test_eval_cli.py::test_eval_output_is_dict_with_memmcp_metadata tests/ca/test_eval_cli.py::test_tool_loop_output_carries_memmcp_metadata -v`
Expected: FAIL — `ImportError: cannot import name 'EvalOutput'`.

- [ ] **Step 3: Implement `EvalOutput` and wire collection into `_run_tool_loop`**

In `composable_agents/ca/evalrun.py`, add after the `EvalReport` dataclass (~line 76):

```python
class EvalOutput(dict[str, Any]):
    """Terminal agent-loop dict + mem-mcp ``OutputWithMetadata`` metadata.

    Real mem-mcp agent-loop scorers read ``getattr(output, "_tool_calls", [])``
    and ``getattr(output, "_rounds", None)`` (record/execute, slack/bootstrap,
    threads/merge_evaluator, classification_reviewer, linear/ingest). On a
    plain dict those getattr defaults fire and the suite silently scores as
    "no tools called". Subclassing dict keeps every dict consumer
    (``isinstance(output, dict)``, ``.get``, ``[...]``, ``str()``) unchanged.
    """

    def __init__(
        self,
        output: Mapping[str, Any],
        tool_calls: list[dict[str, Any]],
        rounds: int,
    ) -> None:
        super().__init__(output)
        self._tool_calls = tool_calls
        self._rounds = rounds
```

In `_run_tool_loop`, add alongside the existing `round_call_ids` declaration:

```python
    # mem-mcp OutputWithMetadata parity: every native tool call the MODEL EMITS,
    # in the {"id", "name", "args"} shape real mem-mcp scorers consume. Recorded
    # at emission (pre-execution), matching mem-mcp exactly — its runner parses
    # tool_calls out of the LLM response, so a denied/failed call appears there
    # too; scorers that care about execution read the trace/error instead.
    collected_calls: list[dict[str, Any]] = []
```

Inside `invoke_controller`, in the `if isinstance(tool_calls, list) and tool_calls:` branch, directly after the `round_call_ids = [...]` assignment:

```python
            for tc in tool_calls:
                if isinstance(tc, dict):
                    collected_calls.append(
                        {
                            "id": tc.get("id") or "",
                            "name": tc.get("tool") or "",
                            "args": tc.get("input"),
                        }
                    )
```

Replace the final `return await drive_agent_loop(...)` with:

```python
    result = await drive_agent_loop(
        input=sample.input,
        cfg=cfg,
        invoke_controller=invoke_controller,
        call_tool=call_tool,
        granted=granted,
        contracts=None,
    )
    return EvalOutput(result, collected_calls, turn_index)
```

Add `"EvalOutput",` to the `__all__` list at the bottom of the module (~line 438).

- [ ] **Step 4: Run the full eval test file + gates**

Run: `python -m pytest tests/ca/test_eval_cli.py -v`
Expected: all PASS — including the pre-existing `test_tool_loop_scores_trace_derived_output`, which proves the dict-subclass approach keeps `isinstance(output, dict)` scorers working (that fixture's scorer does exactly that check).
Run: `uv run mypy --strict composable_agents && ruff check .`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add composable_agents/ca/evalrun.py tests/ca/test_eval_cli.py
git commit -m "feat(ca): tool-loop eval output carries mem-mcp _tool_calls/_rounds metadata"
```

---

### Task 2: Score-return normalization + metrics in reports

**Files:**
- Modify: `composable_agents/ca/evalrun.py` (`SampleScore` ~lines 30–41; new `_coerce_score` after `_unique_sample_ids`; `score_one` ~lines 372–385)
- Test: `tests/ca/test_eval_cli.py`

**Interfaces:**
- Consumes: `SampleScore`, `EvalReport` JSON shapes (existing baselines must keep loading).
- Produces: `_coerce_score(value: Any) -> tuple[float, dict[str, Any]]`; `SampleScore` gains `metrics: Optional[dict[str, Any]] = None` (omitted from JSON when `None`/empty). Exports unchanged otherwise.

- [ ] **Step 1: Write the failing tests**

Add to `tests/ca/test_eval_cli.py` (extend the `evalrun` import with `SampleScore`):

```python
TUPLE_SCORER_EVAL = '''\
from typing import Any

from dotctx.eval_types import Sample


def sample(limit: int = -1) -> list[Sample]:
    return [Sample(name="t", input={"task": "x"}, expected=None)]


def score(_input: dict[str, Any], output: Any, expected: Any) -> Any:
    return 0.75, {"keywords": 3}
'''


BAD_SCORER_TEMPLATE = '''\
from typing import Any

from dotctx.eval_types import Sample


def sample(limit: int = -1) -> list[Sample]:
    return [Sample(name="t", input={{"task": "x"}}, expected=None)]


def score(_input: dict[str, Any], output: Any, expected: Any) -> Any:
    return {ret}
'''


def test_score_tuple_carries_metrics(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path, TUPLE_SCORER_EVAL)
    report = run(run_eval(str(ctx), acompletion=SingleShotFake("whatever")))
    s = report.scores[0]
    assert (s.score, s.passed, s.metrics) == (0.75, True, {"keywords": 3})
    data = report.to_json()
    assert data["scores"][0]["metrics"] == {"keywords": 3}
    assert EvalReport.from_json(data).to_json() == data


@pytest.mark.parametrize(
    "ret",
    [
        "(0.5,)",  # 1-tuple
        "(0.5, 3)",  # metrics not a dict
        '"high"',  # not a number
        "1.5",  # out of 0..1 range
        '{"score": 1.0, "reason": "dict returns are not the contract"}',
        '(0.5, {"seen": {"a", "b"}})',  # metrics not JSON-serializable
    ],
)
def test_bad_score_returns_are_setup_errors(tmp_path: Path, ret: str) -> None:
    ctx = _write_eval_ctx(tmp_path, BAD_SCORER_TEMPLATE.format(ret=ret))
    with pytest.raises(ValueError, match=r"eval score\(\) failed"):
        run(run_eval(str(ctx), acompletion=SingleShotFake("whatever")))


def test_sample_score_json_backcompat_without_metrics() -> None:
    s = SampleScore.from_json({"id": "a", "score": 1.0, "passed": True})
    assert s.metrics is None
    assert s.to_json() == {"id": "a", "score": 1.0, "passed": True}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/ca/test_eval_cli.py::test_score_tuple_carries_metrics tests/ca/test_eval_cli.py::test_bad_score_returns_are_setup_errors tests/ca/test_eval_cli.py::test_sample_score_json_backcompat_without_metrics -v`
Expected: `test_score_tuple_carries_metrics` FAILs (`float(tuple)` TypeError wrapped as `eval score() failed`); `test_sample_score_json_backcompat_without_metrics` FAILs (`SampleScore` has no `metrics`); the out-of-range `1.5` param FAILs (no error raised today). The other bad-return params may already pass — that's fine.

- [ ] **Step 3: Implement `_coerce_score` and `SampleScore.metrics`**

In `composable_agents/ca/evalrun.py`, replace the `SampleScore` dataclass with:

```python
@dataclass(frozen=True)
class SampleScore:
    id: str
    score: float
    passed: bool
    metrics: Optional[dict[str, Any]] = None

    def to_json(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "score": self.score, "passed": self.passed}
        if self.metrics:
            d["metrics"] = self.metrics
        return d

    @staticmethod
    def from_json(d: dict[str, Any]) -> "SampleScore":
        m = d.get("metrics")
        return SampleScore(
            id=str(d["id"]),
            score=float(d["score"]),
            passed=bool(d["passed"]),
            metrics=dict(m) if isinstance(m, dict) else None,
        )
```

Add after `_unique_sample_ids`:

```python
def _coerce_score(value: Any) -> tuple[float, dict[str, Any]]:
    """The mem-mcp score() contract: a 0..1 number, or a (number, metrics_dict)
    2-tuple (record/plan and record/execute return metrics for reporters).

    Anything else — e.g. propose_template's dict return — is invalid in
    mem-mcp's runner too; here it surfaces as a setup error (exit 4) instead
    of mem-mcp's silent per-sample 0.0-with-error."""
    metrics: dict[str, Any] = {}
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(
                f"score returned a tuple; expected (score, metrics) with 2 elements, got {len(value)}"
            )
        value, metrics = value
        if not isinstance(metrics, dict):
            raise ValueError(
                "score returned (score, metrics) but metrics must be a dict, "
                f"got {type(metrics).__name__}"
            )
        try:
            json.dumps(metrics)
        except (TypeError, ValueError) as exc:
            # Catch non-serializable metrics HERE (setup error, exit 4) so
            # `ca eval --json` doesn't crash at report-write time (exit 1).
            raise ValueError(f"score metrics must be JSON-serializable: {exc}") from exc
    if not isinstance(value, (int, float)):
        # bool passes on purpose: mem-mcp's runner accepts it (bool is an int
        # subclass there too), so True -> 1.0 is parity, not an accident.
        raise ValueError(f"score must be a number, got {type(value).__name__}")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score must be 0.0-1.0, got {score}")
    return score, metrics
```

In `score_one`, replace the `s = float(value)` line and the return:

```python
                s, metrics = _coerce_score(value)
            except Exception as exc:  # noqa: BLE001 - user eval.py score() code -> setup error (exit 4)
                raise ValueError(f"eval score() failed: {exc!r}") from exc
            sid = sids[index]
            return SampleScore(id=sid, score=s, passed=s >= threshold, metrics=metrics or None)
```

(The `except` clause already exists — only the coercion line and the `return` change.)

- [ ] **Step 4: Run the full eval test file + gates**

Run: `python -m pytest tests/ca/test_eval_cli.py -v`
Expected: all PASS — including the pre-existing `test_single_shot_report_shape_and_pass`, which asserts score JSON keys are exactly `{"id", "score", "passed"}` (metrics omitted when absent).
Run: `uv run mypy --strict composable_agents && ruff check .`
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add composable_agents/ca/evalrun.py tests/ca/test_eval_cli.py
git commit -m "feat(ca): mem-mcp score contract - (score, metrics) tuples, range check, metrics in reports"
```

---

### Task 3: `--tag` / `--sample-name` filtering

**Files:**
- Modify: `composable_agents/ca/evalrun.py` (`run_eval` ~lines 337–370; `run_eval_sync` ~line 400)
- Modify: `composable_agents/ca/cli.py` (`eval_cmd` ~lines 369–390)
- Test: `tests/ca/test_eval_cli.py`

**Interfaces:**
- Consumes: `Sample.tags` (list of strings, may be empty) and `Sample.name` from `composable_agents.dotctx_evals`.
- Produces: `run_eval(..., tags: Optional[Sequence[str]] = None, sample_names: Optional[Sequence[str]] = None)` and the same two kwargs on `run_eval_sync`; CLI options `--tag` (repeatable) and `--sample-name` (repeatable) on `ca eval`. Filter semantics: tags = any-match intersection (mem-mcp `run_prompt_eval.py:118`); unknown sample names raise `ValueError` (exit 4, checked after tag filtering — mem-mcp parity); when either filter is set, `sample(-1)` is called and `--limit` applies **after** filtering; an empty post-filter-post-limit set raises `ValueError` (so `--limit 0` can't produce a silent zero-sample report).

- [ ] **Step 1: Write the failing tests**

Add to `tests/ca/test_eval_cli.py`:

```python
TAGGED_EVAL = '''\
from typing import Any

from dotctx.eval_types import Sample


def sample(limit: int = -1) -> list[Sample]:
    samples = [
        Sample(name="a", input={"task": "a"}, expected=None, tags=["prod"]),
        Sample(name="b", input={"task": "b"}, expected=None, tags=["smoke"]),
        Sample(name="c", input={"task": "c"}, expected=None, tags=["prod", "smoke"]),
    ]
    return samples if limit is None or limit < 0 else samples[:limit]


def score(_input: dict[str, Any], output: Any, expected: Any) -> float:
    return 1.0
'''


def test_tag_filter_any_match(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    report = run(run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["prod"]))
    assert [s.id for s in report.scores] == ["a", "c"]
    assert report.samples == 2


def test_tag_filter_applies_before_limit(tmp_path: Path) -> None:
    # A naive sample(limit=1) would only see "a" (tagged prod) and return
    # nothing for smoke; filtering must happen on sample(-1) first.
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    report = run(run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["smoke"], limit=1))
    assert [s.id for s in report.scores] == ["b"]


def test_sample_name_filter_and_missing_name(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    report = run(run_eval(str(ctx), acompletion=SingleShotFake("x"), sample_names=["b"]))
    assert [s.id for s in report.scores] == ["b"]
    with pytest.raises(ValueError, match="zzz"):
        run(run_eval(str(ctx), acompletion=SingleShotFake("x"), sample_names=["zzz"]))


def test_no_matching_tag_is_setup_error(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    with pytest.raises(ValueError, match="no samples"):
        run(run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["nope"]))
    # --limit 0 on a filtered run must not slip through as a zero-sample report
    with pytest.raises(ValueError, match="no samples"):
        run(run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["prod"], limit=0))


def test_eval_cmd_passes_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    from typer.testing import CliRunner

    import composable_agents.ca.evalrun as evalrun

    captured: dict[str, Any] = {}

    def fake_run_eval_sync(ctx_path: str, **kwargs: Any) -> EvalReport:
        captured.update(kwargs, ctx_path=ctx_path)
        return EvalReport(
            ctx="x", model="m", samples=0, scores=(), mean=1.0, threshold=0.5, passed=True
        )

    monkeypatch.setattr(evalrun, "run_eval_sync", fake_run_eval_sync)
    monkeypatch.setattr(cli, "_eval_env_vars", lambda env: {})
    result = CliRunner().invoke(
        cli.app,
        ["eval", "some.ctx", "--tag", "prod", "--tag", "smoke", "--sample-name", "a"],
    )
    assert result.exit_code == 0, result.output
    assert captured["tags"] == ["prod", "smoke"]
    assert captured["sample_names"] == ["a"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/ca/test_eval_cli.py -k "tag_filter or sample_name or no_matching or passes_filters" -v`
Expected: FAIL — `run_eval() got an unexpected keyword argument 'tags'` and CLI `Error: No such option: --tag`.

- [ ] **Step 3: Implement filtering in `run_eval` / `run_eval_sync`**

In `composable_agents/ca/evalrun.py`, change the `run_eval` signature:

```python
async def run_eval(
    ctx_path: str,
    *,
    env_vars: Optional[Mapping[str, str]] = None,
    limit: Optional[int] = None,
    tags: Optional[Sequence[str]] = None,
    sample_names: Optional[Sequence[str]] = None,
    acompletion: Optional[AnyCompletion] = None,
    registry: Registry = DEFAULT_REGISTRY,
) -> EvalReport:
```

Replace the sample-loading block (from `try: raw = module.sample(...)` through `sids = _unique_sample_ids(samples)`) with:

```python
    filtered = bool(tags) or bool(sample_names)
    try:
        raw = module.sample(-1 if (limit is None or filtered) else limit)
        loaded_samples = await raw if inspect.isawaitable(raw) else raw
    except Exception as exc:  # noqa: BLE001 - user eval.py sample() code -> setup error (exit 4)
        raise ValueError(f"eval sample() failed: {exc!r}") from exc
    samples = _validate_samples(loaded_samples)
    if tags:
        # mem-mcp semantics (run_prompt_eval.py): any-match set intersection.
        tag_set = set(tags)
        samples = [s for s in samples if tag_set.intersection(s.tags or ())]
    if sample_names:
        # Checked AFTER tag filtering, matching mem-mcp (run_prompt_eval.py):
        # a name excluded by --tag reports as missing there too.
        name_set = set(sample_names)
        selected = [s for s in samples if s.name in name_set]
        missing = sorted(name_set - {s.name for s in selected})
        if missing:
            where = f"{ctx!r} (after --tag filtering)" if tags else repr(ctx)
            raise ValueError(
                f"sample names not found in {where}: {', '.join(missing)} "
                "(names come from Sample(name=...))"
            )
        samples = selected
    if filtered:
        if limit is not None:
            samples = samples[: max(0, limit)]
        if not samples:
            # Covers both no-tag-match and --limit 0: never emit a silent
            # zero-sample report (exit 2) when the user asked for a subset.
            raise ValueError(
                f"no samples in {ctx!r} match --tag/--sample-name/--limit "
                "(tag filtering is any-match on Sample.tags)"
            )
    sids = _unique_sample_ids(samples)
```

Update `run_eval_sync`:

```python
def run_eval_sync(
    ctx_path: str,
    *,
    env_vars: Optional[Mapping[str, str]] = None,
    limit: Optional[int] = None,
    tags: Optional[Sequence[str]] = None,
    sample_names: Optional[Sequence[str]] = None,
    acompletion: Optional[AnyCompletion] = None,
) -> EvalReport:
    return asyncio.run(
        run_eval(
            ctx_path,
            env_vars=env_vars,
            limit=limit,
            tags=tags,
            sample_names=sample_names,
            acompletion=acompletion,
        )
    )
```

- [ ] **Step 4: Implement the CLI options**

In `composable_agents/ca/cli.py`, add two parameters to `eval_cmd` after `limit`:

```python
    tag: list[str] = typer.Option(
        [], "--tag", help="Run only samples carrying this tag (repeatable; any-match)."
    ),
    sample_name: list[str] = typer.Option(
        [], "--sample-name", help="Run only samples with this exact name (repeatable; unknown names exit 4)."
    ),
```

and thread them through the `run_eval_sync` call:

```python
        report = run_eval_sync(
            ctx_path,
            env_vars=env_vars,
            limit=(None if limit < 0 else limit),
            tags=(tag or None),
            sample_names=(sample_name or None),
        )
```

- [ ] **Step 5: Run the full eval test file + gates**

Run: `python -m pytest tests/ca/test_eval_cli.py -v`
Expected: all PASS.
Run: `python -m pytest && uv run mypy --strict composable_agents && ruff check .`
Expected: full suite green, mypy and ruff clean.

- [ ] **Step 6: Commit**

```bash
git add composable_agents/ca/evalrun.py composable_agents/ca/cli.py tests/ca/test_eval_cli.py
git commit -m "feat(ca): --tag/--sample-name filtering on ca eval (mem-mcp prod/smoke workflow)"
```

---

## Explicitly out of scope (verified unnecessary for real-suite parity)

- `eval.yaml` `models`/`datasets`/`scoring`/`profiles` consumption — all 9 real yamls carry a single model, a `format: py` dataset pointing back at `eval.py`, and a `smoke` profile that even mem-mcp's own runners bypass (they filter by tags).
- Dict-returning `score()` — broken in mem-mcp's runner too (`briefs/propose_template` errors to 0.0 there; its `score()` doesn't even match the 3-arg call signature).
- Multi-suite discovery/fan-out, per-repo threshold overrides, provider-fallback bridging, cost tracking, model sweeps, the metrics-aware `eval_diff` reporter — thin wrappers or one-off research tooling on the mem-mcp side; reproducible there without framework changes.
