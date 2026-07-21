"""CLI/test-time runner for mem-mcp-style ``.ctx`` eval suites.

This module executes user-provided ``eval.py`` code with the same trust stance
as :func:`julep.dotctx_evals.load_eval_module`: explicit eval entry
points only, never prompt loading. Tests inject a fake ``acompletion``; real CLI
runs resolve the provider completion lazily.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping, Optional, Sequence

from julep.agent_loop import AgentConfig, ROUND_NOTE_KEY, drive_agent_loop
from julep.dotctx_evals import MockToolConfig, Sample, Turn, load_ctx_evals
from julep.dotctx_rich import RichDotctx, load_rich_dotctx
from julep.execution.llm import (
    AnyCompletion,
    _resolve_acompletion,
    complete_reasoner,
)
from julep.prompt import rendered_user_for
from julep.qos import ReasonerDispatch
from julep.registry import DEFAULT_REGISTRY, Registry

EvalLlmCaller = Callable[..., Awaitable[Any]]


async def _invoke_eval_llm(
    reasoner: Any,
    value: Any,
    *,
    acompletion: Optional[AnyCompletion],
    llm_caller: Optional[EvalLlmCaller],
    transcript: Optional[list[dict[str, Any]]] = None,
    tools: Optional[list[dict[str, Any]]] = None,
) -> Any:
    if llm_caller is None:
        result = await complete_reasoner(
            reasoner,
            value,
            acompletion=acompletion,
            transcript=transcript,
            tools=tools,
            parallel_tool_calls=True if tools else None,
        )
        return result.reply

    kwargs: dict[str, Any] = {}
    if tools:
        try:
            signature = inspect.signature(llm_caller)
        except (TypeError, ValueError):
            signature = None
        accepts_tools = signature is not None and (
            "tools" in signature.parameters
            or any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
        )
        if not accepts_tools:
            raise ValueError(
                "an injected LlmCaller used by a tool-loop eval must accept "
                "the keyword argument tools"
            )
        kwargs["tools"] = tools
    raw = await llm_caller(
        reasoner,
        value,
        None,
        transcript,
        ReasonerDispatch(),
        **kwargs,
    )
    return getattr(raw, "reply", raw)


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


@dataclass(frozen=True)
class EvalReport:
    ctx: str
    model: str
    samples: int
    scores: tuple[SampleScore, ...]
    mean: float
    threshold: float
    passed: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "ctx": self.ctx,
            "model": self.model,
            "samples": self.samples,
            "scores": [s.to_json() for s in self.scores],
            "mean": self.mean,
            "threshold": self.threshold,
            "passed": self.passed,
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "EvalReport":
        return EvalReport(
            ctx=str(d["ctx"]),
            model=str(d["model"]),
            samples=int(d["samples"]),
            scores=tuple(SampleScore.from_json(s) for s in d["scores"]),
            mean=float(d["mean"]),
            threshold=float(d["threshold"]),
            passed=bool(d["passed"]),
        )


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
        # mem-mcp OutputWithMetadata parity: extract_llm_content()/scorers that
        # read the final assistant text walk ``__dict__["output"]`` (llm_utils
        # extract_llm_content). The terminal harness dict nests the final reply
        # at output["output"] (e.g. {"content": ...}); expose it as the ``output``
        # attribute so extract_llm_content(EvalOutput) returns that text instead
        # of None. ``getattr(output, "content")`` stays None, matching mem-mcp
        # (a litellm response object has no top-level ``.content`` attribute).
        self.output = output.get("output") if isinstance(output, Mapping) else None


def _normalize_tool_args(value: Any) -> Any:
    """mem-mcp parity: an agent-loop tool call's ``args`` is ALWAYS a dict.

    mem-mcp's ``_extract_tool_calls_from_response`` yields ``{"_raw": args_str}``
    when the provider arguments don't JSON-decode and defaults missing arguments
    to ``{}``. Native tool-call parsing here (execution/llm._parse_tool_call_arguments)
    instead returns the raw string on a decode failure and ``None`` for absent
    arguments, so a ported scorer doing ``call.get("args", {}).get(...)`` would hit
    ``''`` / ``None`` and raise AttributeError, aborting the whole eval as a setup
    error (exit 4). Coerce to the shape mem-mcp guarantees.
    """
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        return {"_raw": value}
    return value


def _provider_tool_defs(
    expected: Mapping[str, dict[str, Any]],
    descriptions: Mapping[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": key,
                "description": descriptions.get(key, ""),
                "parameters": schema,
            },
        }
        for key, schema in expected.items()
    ]


def _validate_samples(loaded: Any) -> list[Sample]:
    """Validate the eval.py sample() contract as a setup-time error.

    A wrong return (None, a scalar, or raw dicts) surfaces as ValueError so
    `julep eval` exits 4 instead of crashing while scoring.
    """
    if loaded is None or isinstance(loaded, (str, bytes, Mapping)):
        raise ValueError(
            f"eval sample() must return an iterable of Sample, got {type(loaded).__name__}"
        )
    try:
        items = list(loaded)
    except TypeError as exc:
        raise ValueError(
            f"eval sample() must return an iterable of Sample, got {type(loaded).__name__}"
        ) from exc
    for i, s in enumerate(items):
        if not isinstance(s, Sample):
            raise ValueError(
                f"eval sample()[{i}] must be a Sample, got {type(s).__name__} "
                "(construct Sample(input=..., expected=...), do not return raw dicts)"
            )
    return items


def _unique_sample_ids(samples: Sequence[Sample]) -> list[str]:
    counts: dict[str, int] = {}
    ids: list[str] = []
    for i, s in enumerate(samples):
        base = s.name if s.name else f"sample-{i}"
        n = counts.get(base)
        if n is None:
            counts[base] = 0
            ids.append(base)
        else:
            counts[base] = n + 1
            ids.append(f"{base}#{counts[base]}")
    return ids


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
            # `julep eval --json` doesn't crash at report-write time (exit 1).
            raise ValueError(f"score metrics must be JSON-serializable: {exc}") from exc
    if not isinstance(value, (int, float)):
        # bool passes on purpose: mem-mcp's runner accepts it (bool is an int
        # subclass there too), so True -> 1.0 is parity, not an accident.
        raise ValueError(f"score must be a number, got {type(value).__name__}")
    score = float(value)
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score must be 0.0-1.0, got {score}")
    return score, metrics


def _resolve_mock(
    mock: Any,
    args: Any,
    counters: dict[str, int],
    key: str,
) -> Any:
    if isinstance(mock, MockToolConfig):
        margs = args if isinstance(args, dict) else {}
        for pattern, response in mock.match:
            if all(margs.get(k) == v for k, v in pattern.items()):
                return response
        if mock.match:
            # `match` patterns were defined but none matched -> documented
            # `default`. `responses` is used ONLY when no `match` is defined
            # (per MockToolConfig), so it must not shadow `default` here.
            return mock.default
        if mock.responses:
            idx = counters.get(key, 0)
            counters[key] = idx + 1
            return mock.responses[idx % len(mock.responses)]
        return mock.default
    return mock


def _turn_from_reply(reply: Any) -> Turn:
    if isinstance(reply, dict) and isinstance(reply.get("tool_calls"), list):
        tool_calls = [
            {"name": tc.get("tool"), "args": tc.get("input")}
            for tc in reply["tool_calls"]
            if isinstance(tc, dict)
        ]
        return Turn(output=reply, tool_calls=tool_calls, tool_results=[], content=None, refusal=None)
    content = reply if isinstance(reply, str) else None
    return Turn(output=reply, tool_calls=[], tool_results=[], content=content, refusal=None)


def _seed_user_turn(reasoner: Any, value: Any) -> dict[str, Any]:
    """The leading user turn the model saw on round 0, replayed so later rounds
    start from a valid user turn (providers reject a leading assistant turn)."""
    text = rendered_user_for(reasoner, value)
    content = text if text is not None else (value if isinstance(value, str) else json.dumps(value))
    return {"role": "user", "content": content}


def _assistant_call_turn(tool_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """An assistant turn carrying this round's native tool calls (OpenAI grammar),
    so execution/llm._transcript_messages round-trips them as native tool_calls."""
    calls: list[dict[str, Any]] = []
    for tc in tool_calls:
        args = tc.get("input") if isinstance(tc, dict) else None
        name = (tc.get("tool") if isinstance(tc, dict) else None) or ""
        calls.append(
            {
                "id": tc.get("id") if isinstance(tc, dict) else None,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(args if args is not None else {}),
                },
            }
        )
    return {"role": "assistant", "content": None, "tool_calls": calls}


def _tool_result_turn(call_id: Optional[str], content: Any) -> dict[str, Any]:
    """A tool-result turn matching a prior assistant tool_call id (native grammar)."""
    turn: dict[str, Any] = {"role": "tool", "content": content}
    if call_id is not None:
        turn["tool_call_id"] = call_id
    return turn


async def _run_single_shot(
    reasoner: Any,
    sample: Sample,
    acompletion: Optional[AnyCompletion],
    llm_caller: Optional[EvalLlmCaller] = None,
) -> Any:
    reply = await _invoke_eval_llm(
        reasoner,
        sample.input,
        acompletion=acompletion,
        llm_caller=llm_caller,
    )
    text = reply if isinstance(reply, str) else json.dumps(reply)
    return {"content": text}


async def _run_tool_loop(
    rich: RichDotctx,
    sample: Sample,
    acompletion: Optional[AnyCompletion],
    llm_caller: Optional[EvalLlmCaller] = None,
) -> Any:
    reasoner = rich.reasoner
    tool_defs = _provider_tool_defs(
        rich.expected_tool_schemas,
        rich.expected_tool_descriptions,
    )
    stop_on = sample.stop_on
    turns_bound = getattr(stop_on, "_julep_max_turns", None)
    if isinstance(turns_bound, int):
        # "stop_after_turns(n) -> max_rounds override" (plan Task 8): the sample's
        # turn budget governs the run. +1 headroom so the StopFn fires as a clean
        # 'done' at the next controller entry BEFORE the loop's hard max_rounds cap
        # trips (n == cap would otherwise terminate as 'max_rounds', not 'done').
        max_rounds = turns_bound + 1
    else:
        max_rounds = reasoner.max_rounds or 24
    cfg = AgentConfig(
        max_rounds=max_rounds,
        native_tools=True,
        require_tool_call=reasoner.require_tool_call,
        # A native-tool agent's normal completion is: call tools, then answer in
        # prose. Under strict control that final text reply is a malformed reply
        # and the run halts as `controller_error` before the sample's StopFn is
        # consulted. Permissive control FINISHES on it instead, so eval replays
        # the normal completion path (finding: strict mode mis-scored completion).
        permissive_controller=True,
    )
    granted = set(reasoner.tools)
    mock_tools = sample.mock_tools or {}
    counters: dict[str, int] = {}

    base_value = dict(sample.input) if isinstance(sample.input, dict) else sample.input
    # Neutral transcript accumulated across rounds so the controller SEES its own
    # prior tool calls and their observations (native tool-call grammar per
    # execution/llm._transcript_messages). Without this the model re-renders the
    # static sample input every round and is blind to tool results and errors —
    # it could never recover from a tool-error observation or chain tool results.
    transcript: list[dict[str, Any]] = []
    # This round's provider tool_call ids, positionally aligned with the loop's
    # call_index, so each tool observation attaches to the right assistant call.
    round_call_ids: list[Optional[str]] = []
    # mem-mcp OutputWithMetadata parity: every native tool call the MODEL EMITS,
    # in the {"id", "name", "args"} shape real mem-mcp scorers consume. Recorded
    # at emission (pre-execution), matching mem-mcp exactly — its runner parses
    # tool_calls out of the LLM response, so a denied/failed call appears there
    # too; scorers that care about execution read the trace/error instead.
    collected_calls: list[dict[str, Any]] = []

    async def call_tool(
        name: str,
        value: Any,
        *,
        call_index: Optional[int] = None,
    ) -> Any:
        idx = call_index if call_index is not None else 0
        call_id = round_call_ids[idx] if 0 <= idx < len(round_call_ids) else None
        try:
            if name not in mock_tools:
                raise KeyError(f"tool {name!r} was not mocked for this eval sample")
            out = _resolve_mock(mock_tools[name], value, counters, name)
        except Exception as exc:  # noqa: BLE001 - mirror the loop's observation wrapping
            # Record the SAME error observation the loop will surface as state.last
            # so the NEXT round's controller can recover from it (Task 1 / Phase 3
            # acceptance), then re-raise so the loop records TraceEntry.error.
            transcript.append(_tool_result_turn(call_id, {"error": repr(exc), "tool": name}))
            raise
        transcript.append(_tool_result_turn(call_id, out))
        return out

    turn_index = 0
    last_turn: Optional[Turn] = None

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        nonlocal last_turn, turn_index, round_call_ids
        if last_turn is not None and stop_on(last_turn, turn_index):
            # Clean StopFn 'done': the output is the post-tool observation
            # (payload["input"] == state.last), NOT the assistant tool-call reply
            # dict — an output-based scorer must see the tool result, not tool_calls.
            return {"done": True, "output": payload.get("input")}
        turn_index += 1
        value = dict(base_value) if isinstance(base_value, dict) else base_value
        if isinstance(value, dict) and ROUND_NOTE_KEY in payload:
            value[ROUND_NOTE_KEY] = payload[ROUND_NOTE_KEY]
        reply = await _invoke_eval_llm(
            reasoner,
            value,
            acompletion=acompletion,
            llm_caller=llm_caller,
            tools=tool_defs,
            transcript=list(transcript) if transcript else None,
        )
        last_turn = _turn_from_reply(reply)
        tool_calls = reply.get("tool_calls") if isinstance(reply, dict) else None
        if isinstance(tool_calls, list) and tool_calls:
            if not transcript:
                transcript.append(_seed_user_turn(reasoner, base_value))
            transcript.append(_assistant_call_turn(tool_calls))
            round_call_ids = [
                (tc.get("id") if isinstance(tc, dict) else None) for tc in tool_calls
            ]
            for tc in tool_calls:
                if isinstance(tc, dict):
                    collected_calls.append(
                        {
                            "id": tc.get("id") or "",
                            "name": tc.get("tool") or "",
                            "args": _normalize_tool_args(tc.get("input")),
                        }
                    )
        else:
            round_call_ids = []
            # A content-only (natural-language) final reply: normalize to the
            # same {"content": ...} shape single-shot runs use, so a content
            # scorer reads the model's actual final message and the loop FINISHES
            # here (permissive control) instead of halting as controller_error.
            if isinstance(reply, str):
                return {"output": {"content": reply}}
        return reply

    result = await drive_agent_loop(
        input=sample.input,
        cfg=cfg,
        invoke_controller=invoke_controller,
        call_tool=call_tool,
        granted=granted,
        contracts=None,
    )
    return EvalOutput(result, collected_calls, turn_index)


async def run_eval(
    ctx_path: str,
    *,
    env_vars: Optional[Mapping[str, str]] = None,
    limit: Optional[int] = None,
    tags: Optional[Sequence[str]] = None,
    sample_names: Optional[Sequence[str]] = None,
    acompletion: Optional[AnyCompletion] = None,
    llm_caller: Optional[EvalLlmCaller] = None,
    registry: Registry = DEFAULT_REGISTRY,
) -> EvalReport:
    env = dict(env_vars) if env_vars is not None else {}
    ctx = os.fspath(ctx_path)
    evals = load_ctx_evals(ctx, env=env)
    if evals.eval_module is None:
        raise ValueError(
            f"no eval.py in {ctx!r}: `julep eval` needs an eval.py exposing "
            "sample()/score() (see the mem-mcp eval surface)"
        )
    rich = load_rich_dotctx(ctx, registry=registry, env=env)
    module = evals.eval_module
    config = evals.eval_config
    threshold = config.threshold if config is not None else 0.5
    concurrency = config.concurrency if config is not None else 5
    reasoner = rich.reasoner
    resolved = None if llm_caller is not None else _resolve_acompletion(acompletion)

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

    is_tool_loop = bool(reasoner.tools)
    sem = asyncio.Semaphore(max(1, concurrency))

    async def score_one(index: int, sample: Sample) -> SampleScore:
        async with sem:
            if is_tool_loop:
                output = await _run_tool_loop(
                    rich,
                    sample,
                    resolved,
                    llm_caller=llm_caller,
                )
            else:
                output = await _run_single_shot(
                    reasoner,
                    sample,
                    resolved,
                    llm_caller=llm_caller,
                )
            try:
                raw_score = module.score(sample.input, output, sample.expected)
                value = await raw_score if inspect.isawaitable(raw_score) else raw_score
                s, metrics = _coerce_score(value)
            except Exception as exc:  # noqa: BLE001 - user eval.py score() code -> setup error (exit 4)
                raise ValueError(f"eval score() failed: {exc!r}") from exc
            sid = sids[index]
            return SampleScore(id=sid, score=s, passed=s >= threshold, metrics=metrics or None)

    results = await asyncio.gather(*(score_one(i, s) for i, s in enumerate(samples)))
    mean = sum(r.score for r in results) / len(results) if results else 0.0
    return EvalReport(
        ctx=ctx,
        model=reasoner.model,
        samples=len(results),
        scores=tuple(results),
        mean=mean,
        threshold=threshold,
        passed=mean >= threshold,
    )


def run_eval_sync(
    ctx_path: str,
    *,
    env_vars: Optional[Mapping[str, str]] = None,
    limit: Optional[int] = None,
    tags: Optional[Sequence[str]] = None,
    sample_names: Optional[Sequence[str]] = None,
    acompletion: Optional[AnyCompletion] = None,
    llm_caller: Optional[EvalLlmCaller] = None,
) -> EvalReport:
    return asyncio.run(
        run_eval(
            ctx_path,
            env_vars=env_vars,
            limit=limit,
            tags=tags,
            sample_names=sample_names,
            acompletion=acompletion,
            llm_caller=llm_caller,
        )
    )


def diff_reports(
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    *,
    mean_tolerance: float = 0.01,
) -> tuple[list[str], bool]:
    def _passes_by_id(report: Mapping[str, Any]) -> dict[str, list[bool]]:
        groups: dict[str, list[bool]] = {}
        for s in report.get("scores", []):
            if isinstance(s, dict):
                groups.setdefault(str(s["id"]), []).append(bool(s.get("passed")))
        return groups

    base = _passes_by_id(baseline)
    cur = _passes_by_id(current)
    regressed: list[str] = []
    for sid, base_passes in base.items():
        # Optimistic on baseline, pessimistic on current: duplicate ids or
        # disappeared samples must not hide a passed -> failed regression.
        was_passing = any(base_passes)
        cur_passes = cur.get(sid)
        now_passing = cur_passes is not None and bool(cur_passes) and all(cur_passes)
        if was_passing and not now_passing:
            regressed.append(sid)
    mean_regressed = (float(baseline.get("mean", 0.0)) - float(current.get("mean", 0.0))) > mean_tolerance
    return regressed, mean_regressed


__all__ = [
    "EvalOutput",
    "EvalLlmCaller",
    "EvalReport",
    "SampleScore",
    "diff_reports",
    "run_eval",
    "run_eval_sync",
]
