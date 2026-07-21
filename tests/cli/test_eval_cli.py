from __future__ import annotations

import asyncio
from importlib import import_module
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("yglu")  # the vendored .ctx settings carry `!?` env expressions

from julep.cli.main import app, main
from julep.cli.evalrun import (
    EvalOutput,
    EvalReport,
    SampleScore,
    _provider_tool_defs,
    _run_tool_loop,
    diff_reports,
    run_eval,
    run_eval_sync,
)
from julep.dotctx import load_dotctx
from julep.dotctx_evals import (
    MockToolConfig,
    Sample,
    extract_llm_content,
    stop_after_turns,
    stop_when_non_tool,
    stop_when_terminal_tool,
)
from julep.dotctx_rich import load_rich_dotctx
from conftest import run


@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None
    tool_calls: Any = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


def _content(text: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=text))])


def _parsed(obj: Any) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(parsed=obj))])


def _tool_call_completion(id: str, name: str, args_json: str) -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                FakeMessage(
                    tool_calls=[FakeToolCall(id, FakeFunction(name, args_json))]
                )
            )
        ]
    )


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "memmcp"


def _write_eval_ctx(tmp_path: Path, eval_py: str) -> Path:
    ctx = tmp_path / "case.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text('model: "openai/gpt-eval@low"\n', encoding="utf-8")
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\nHi.\n\n<<< role:user >>>\nT: {{ task | default('', true) }}\n",
        encoding="utf-8",
    )
    (ctx / "eval.yaml").write_text(
        "threshold: 0.5\n\ndatasets:\n  - file: eval.py\n    format: py\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(eval_py, encoding="utf-8")
    return ctx


def _write_tool_eval_ctx(tmp_path: Path, eval_py: str) -> Path:
    """Copy the vendored tool-loop fixture, swapping in a custom eval.py."""
    ctx = tmp_path / "tool_case.ctx"
    shutil.copytree(FIXTURES / "execute_eval.ctx", ctx)
    (ctx / "eval.py").write_text(eval_py, encoding="utf-8")
    return ctx


def test_eval_can_use_injected_production_llm_caller(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(
        tmp_path,
        '''\
from dotctx.eval_types import Sample

def sample(limit=-1):
    return [Sample(name="injected", input={"task": "x"}, expected="from caller")]

def score(_input, output, expected):
    return 1.0 if output.get("content") == expected else 0.0
''',
    )
    calls: list[tuple[Any, ...]] = []

    async def caller(reasoner, value, principal, transcript, dispatch):
        calls.append((reasoner, value, principal, transcript, dispatch))
        return "from caller"

    report = run(run_eval(str(ctx), llm_caller=caller))

    assert report.passed is True
    assert len(calls) == 1
    assert calls[0][1:] == ({"task": "x"}, None, None, calls[0][4])


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


def _good_summary_json() -> str:
    return json.dumps(
        {
            "summary": (
                "Alice met Bob in London about the Atlas rollout. "
                "Nina approved Atlas in Berlin."
            )
        }
    )


class SingleShotFake:
    def __init__(self, content: str, delay: float = 0.0):
        self.content = content
        self.delay = delay
        self.in_flight = 0
        self.max_in_flight = 0
        self.calls = 0

    async def __call__(self, **kwargs):
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            return _content(self.content)
        finally:
            self.in_flight -= 1


def _last_tool_result(messages: list[dict[str, Any]]) -> Any:
    for message in reversed(messages):
        if message.get("role") == "tool":
            return message.get("content")
    return None


class ToolLoopFake:
    """Scripted tool model: call ``tool_name`` once, then finish after seeing its
    observation. Faithful to a real provider (branches on the tool result the
    threaded transcript carries), unlike a message-identity fake."""

    def __init__(self, tool_name: str, tool_args_json: str):
        self.tool_name = tool_name
        self.tool_args_json = tool_args_json

    async def __call__(self, **kwargs):
        messages = kwargs["messages"]
        if any(m.get("role") == "tool" for m in messages):
            return _parsed({"done": True})
        return _tool_call_completion("c1", self.tool_name, self.tool_args_json)


class AlwaysCallsFake:
    """Never finishes on its own — calls ``tool_name`` every round. Used to prove
    a StopFn (not the model) terminates the loop."""

    def __init__(self, tool_name: str, args_json: str = "{}"):
        self.tool_name = tool_name
        self.args_json = args_json
        self.calls = 0

    async def __call__(self, **kwargs):
        self.calls += 1
        return _tool_call_completion(f"c{self.calls}", self.tool_name, self.args_json)


class RecoveringFake:
    """Calls the (unmocked -> raising) ``search`` tool first; after seeing the
    error observation, recovers by calling ``record_memory``; finishes once that
    succeeds. Proves the controller acts on prior tool observations."""

    async def __call__(self, **kwargs):
        last = _last_tool_result(kwargs["messages"])
        if last is None:
            return _tool_call_completion("c1", "search", '{"query": "x"}')
        text = last if isinstance(last, str) else json.dumps(last)
        if "error" in text:
            return _tool_call_completion("c2", "record_memory", '{"content": "recovered"}')
        return _parsed({"done": True})


class SearchThenRecordFake:
    """Calls ``search``, reads the returned top hit out of the transcript, then
    records it. Proves the model can CHAIN a prior tool result into the next call."""

    async def __call__(self, **kwargs):
        results = [m for m in kwargs["messages"] if m.get("role") == "tool"]
        if not results:
            return _tool_call_completion("c1", "search", '{"query": "who"}')
        if len(results) == 1:
            text = results[0].get("content", "")
            text = text if isinstance(text, str) else json.dumps(text)
            hit = "alice" if "alice" in text else "none"
            return _tool_call_completion("c2", "record_memory", json.dumps({"content": hit}))
        return _parsed({"done": True})


class CallThenTextFake:
    """Calls a tool once, then answers in natural language (content) — the normal
    completion path for a native-tool agent. Must FINISH cleanly, never halt as
    controller_error, and must expose the final text to a content scorer."""

    async def __call__(self, **kwargs):
        if any(m.get("role") == "tool" for m in kwargs["messages"]):
            return _content("all done, stored it")
        return _tool_call_completion("c1", "record_memory", '{"content": "hi"}')


def test_single_shot_report_shape_and_pass() -> None:
    report = run(
        run_eval(
            str(FIXTURES / "episode_summary.ctx"),
            acompletion=SingleShotFake(_good_summary_json()),
        )
    )

    data = report.to_json()
    assert set(data) == {"ctx", "model", "samples", "scores", "mean", "threshold", "passed"}
    assert data == EvalReport.from_json(data).to_json()
    assert report.samples == 2
    assert all(set(score) == {"id", "score", "passed"} for score in data["scores"])
    assert [score.id for score in report.scores] == ["meeting_with_context", "empty_background"]
    assert report.threshold == 0.5
    assert report.mean == 1.0
    assert report.passed is True
    assert report.model == load_dotctx(str(FIXTURES / "episode_summary.ctx"), env={}).model


def test_single_shot_below_threshold() -> None:
    report = run(
        run_eval(
            str(FIXTURES / "episode_summary.ctx"),
            acompletion=SingleShotFake("not json"),
        )
    )

    assert [score.score for score in report.scores] == [0.0, 0.0]
    assert report.mean == 0.0
    assert report.passed is False


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


def test_tag_filter_any_match(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    report = run(run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["prod"]))
    assert [s.id for s in report.scores] == ["a", "c"]
    assert report.samples == 2


def test_tag_filter_applies_before_limit(tmp_path: Path) -> None:
    # A naive sample(limit=1) would only see "a" (tagged prod) and return
    # nothing for smoke; filtering must happen on sample(-1) first.
    ctx = _write_eval_ctx(tmp_path, TAGGED_EVAL)
    report = run(
        run_eval(str(ctx), acompletion=SingleShotFake("x"), tags=["smoke"], limit=1)
    )
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

    import julep.cli.evalrun as evalrun

    captured: dict[str, Any] = {}

    def fake_run_eval_sync(ctx_path: str, **kwargs: Any) -> EvalReport:
        captured.update(kwargs, ctx_path=ctx_path)
        return EvalReport(
            ctx="x",
            model="m",
            samples=0,
            scores=(),
            mean=1.0,
            threshold=0.5,
            passed=True,
        )

    monkeypatch.setattr(evalrun, "run_eval_sync", fake_run_eval_sync)
    main_module = import_module("julep.cli.main")
    monkeypatch.setattr(main_module, "_eval_env_vars", lambda env: {})
    result = CliRunner().invoke(
        app,
        ["eval", "some.ctx", "--tag", "prod", "--tag", "smoke", "--sample-name", "a"],
    )
    assert result.exit_code == 0, result.output
    assert captured["tags"] == ["prod", "smoke"]
    assert captured["sample_names"] == ["a"]


def test_tool_loop_scores_trace_derived_output() -> None:
    report = run(
        run_eval(
            str(FIXTURES / "execute_eval.ctx"),
            acompletion=ToolLoopFake("record_memory", '{"content": "hi"}'),
            limit=1,
        )
    )

    reasoner = load_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    assert bool(reasoner.tools) is True
    assert report.samples == 1
    assert report.scores[0].id == "records_ok"
    assert report.scores[0].score == 1.0
    assert report.scores[0].passed is True


def test_eval_output_is_dict_with_memmcp_metadata() -> None:
    out = EvalOutput({"trace": [1]}, [{"id": "c1", "name": "t", "args": {}}], 2)
    assert isinstance(out, dict)
    assert out.get("trace") == [1]
    assert out["trace"] == [1]
    assert out._tool_calls == [{"id": "c1", "name": "t", "args": {}}]
    assert out._rounds == 2
    assert getattr(out, "content", None) is None


def test_tool_loop_empty_args_normalized_to_dict() -> None:
    """mem-mcp parity: tool-call ``args`` is ALWAYS a dict, so a scorer doing
    ``call.get("args", {}).get(...)`` never raises on empty/malformed arguments."""
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    sample = Sample(
        name="empty_args",
        input={"task": "store"},
        expected=None,
        mock_tools={"record_memory": {"ok": True}},
        stop_on=stop_after_turns(3),
    )
    out = run(_run_tool_loop(rich, sample, ToolLoopFake("record_memory", "")))
    assert out._tool_calls
    assert all(isinstance(call["args"], dict) for call in out._tool_calls)
    # The real mem-mcp scorer access pattern must not raise on empty args.
    assert out._tool_calls[0]["args"].get("content") is None


def test_extract_llm_content_reaches_tool_loop_final_text() -> None:
    """mem-mcp OutputWithMetadata parity: extract_llm_content(output) returns the
    tool loop's final assistant text via the ``__dict__['output']`` hop (not None),
    while ``getattr(output, "content")`` stays None as it does in mem-mcp."""
    out = EvalOutput(
        {"status": "done", "output": {"content": "final text"}, "trace": []},
        [{"id": "c1", "name": "t", "args": {}}],
        2,
    )
    assert extract_llm_content(out) == "final text"
    assert getattr(out, "content", None) is None


def test_tool_loop_output_carries_memmcp_metadata(tmp_path: Path) -> None:
    ctx = _write_tool_eval_ctx(tmp_path, META_SCORER_EVAL)
    report = run(
        run_eval(str(ctx), acompletion=ToolLoopFake("record_memory", '{"content": "hi"}'))
    )
    assert report.scores[0].id == "meta_ok"
    assert report.scores[0].score == 1.0
    assert report.passed is True


def test_tool_loop_unmocked_tool_scored_failure() -> None:
    report = run(
        run_eval(
            str(FIXTURES / "execute_eval.ctx"),
            acompletion=ToolLoopFake("record_memory", '{"content":"x"}'),
            limit=None,
        )
    )

    by_id = {score.id: score for score in report.scores}
    assert by_id["records_ok"].score == 1.0
    assert by_id["records_ok"].passed is True
    assert by_id["unmocked_fails"].score == 0.0
    assert by_id["unmocked_fails"].passed is False


def test_baseline_regression_exit_via_diff_reports() -> None:
    good = run(
        run_eval(
            str(FIXTURES / "episode_summary.ctx"),
            acompletion=SingleShotFake(_good_summary_json()),
        )
    )
    bad = run(
        run_eval(
            str(FIXTURES / "episode_summary.ctx"),
            acompletion=SingleShotFake("not json"),
        )
    )

    regressed_ids, mean_regressed = diff_reports(good.to_json(), bad.to_json())
    assert set(regressed_ids) == {"meeting_with_context", "empty_background"}
    assert mean_regressed is True
    assert diff_reports(good.to_json(), good.to_json()) == ([], False)


def test_diff_reports_duplicate_id_regresses() -> None:
    baseline = {
        "mean": 0.5,
        "scores": [
            {"id": "dup", "passed": True, "score": 1.0},
            {"id": "dup", "passed": False, "score": 0.0},
        ],
    }
    current = {"mean": 0.5, "scores": [{"id": "dup", "passed": False, "score": 0.0}]}

    regressed_ids, mean_regressed = diff_reports(baseline, current)

    assert "dup" in regressed_ids
    assert mean_regressed is False


def test_diff_reports_disappeared_passing_sample_regresses() -> None:
    baseline = {
        "mean": 1.0,
        "scores": [
            {"id": "a", "passed": True, "score": 1.0},
            {"id": "b", "passed": True, "score": 1.0},
        ],
    }
    current = {"mean": 1.0, "scores": [{"id": "a", "passed": True, "score": 1.0}]}

    regressed_ids, mean_regressed = diff_reports(baseline, current)

    assert "b" in regressed_ids
    assert mean_regressed is False


def test_diff_reports_unique_id_path_unchanged() -> None:
    report = {
        "mean": 1.0,
        "scores": [
            {"id": "a", "passed": True, "score": 1.0},
            {"id": "b", "passed": True, "score": 1.0},
        ],
    }

    assert diff_reports(report, report) == ([], False)


def test_run_eval_deduplicates_duplicate_sample_names(tmp_path: Path) -> None:
    ctx = _write_eval_ctx(
        tmp_path,
        "from dotctx.eval_types import Sample\n\n"
        "def sample(limit: int = -1):\n"
        "    return [Sample(name='dup', input={'task': 'a'}), Sample(name='dup', input={'task': 'b'})]\n\n"
        "def score(_input, _output, _expected):\n"
        "    return 1.0\n",
    )

    report = run(run_eval(str(ctx), acompletion=SingleShotFake('{"x": 1}')))

    assert [s.id for s in report.scores] == ["dup", "dup#1"]


def test_concurrency_bounded(tmp_path: Path) -> None:
    ctx = tmp_path / "parallel.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text(
        'model: "openai/gpt-eval@low"\n',
        encoding="utf-8",
    )
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\n"
        "Reply with JSON.\n\n"
        "<<< role:user >>>\n"
        'Task: {{ task | default("", true) }}\n',
        encoding="utf-8",
    )
    (ctx / "eval.yaml").write_text(
        "threshold: 0.0\n"
        "concurrency: 2\n\n"
        "datasets:\n"
        "  - file: eval.py\n"
        "    format: py\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(
        "from dotctx.eval_types import Sample\n\n"
        "def sample(limit: int = -1):\n"
        "    samples = [\n"
        "        Sample(name=f's{i}', input={'task': f'task-{i}'})\n"
        "        for i in range(6)\n"
        "    ]\n"
        "    return samples if limit is None or limit < 0 else samples[:limit]\n\n"
        "def score(_input, output, expected):\n"
        "    return 1.0\n",
        encoding="utf-8",
    )
    fake = SingleShotFake(content='{"ok": 1}', delay=0.02)

    report = run(run_eval(str(ctx), acompletion=fake))

    assert fake.max_in_flight <= 2
    assert report.samples == 6


def test_cli_exit_codes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda a: SingleShotFake(_good_summary_json()),
    )
    assert main(["eval", str(FIXTURES / "episode_summary.ctx")]) == 0

    json_path = tmp_path / "report.json"
    assert main(["eval", str(FIXTURES / "episode_summary.ctx"), "--json", str(json_path)]) == 0
    assert set(json.loads(json_path.read_text(encoding="utf-8"))) == {
        "ctx",
        "model",
        "samples",
        "scores",
        "mean",
        "threshold",
        "passed",
    }

    good = run(
        run_eval(
            str(FIXTURES / "episode_summary.ctx"),
            acompletion=SingleShotFake(_good_summary_json()),
        )
    )
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(good.to_json()), encoding="utf-8")

    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda a: SingleShotFake("not json"),
    )
    assert main(["eval", str(FIXTURES / "episode_summary.ctx")]) == 2
    assert (
        main(
            [
                "eval",
                str(FIXTURES / "episode_summary.ctx"),
                "--baseline",
                str(baseline_path),
            ]
        )
        == 3
    )


def test_missing_eval_py_is_teaching_error() -> None:
    with pytest.raises(ValueError, match="eval.py"):
        run_eval_sync(str(FIXTURES / "cluster_label.ctx"))

    assert main(["eval", str(FIXTURES / "cluster_label.ctx")]) == 4


@pytest.mark.parametrize(
    ("sample_return", "message"),
    [
        ("None", "got NoneType"),
        ("[{'input': {'task': 'x'}}]", "raw dicts"),
        ("5", "got int"),
    ],
)
def test_run_eval_malformed_sample_return_is_value_error(
    tmp_path: Path, sample_return: str, message: str
) -> None:
    ctx = _write_eval_ctx(
        tmp_path,
        "def sample(limit: int = -1):\n"
        f"    return {sample_return}\n\n"
        "def score(_input, _output, _expected):\n"
        "    return 1.0\n",
    )

    with pytest.raises(ValueError, match=message):
        run(run_eval(str(ctx), acompletion=SingleShotFake('{"x": 1}')))


def test_tool_descriptions_flow_to_provider_defs() -> None:
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})

    assert rich.expected_tool_descriptions["record_memory"] == "Store one memory."
    tool_defs = _provider_tool_defs(
        rich.expected_tool_schemas,
        rich.expected_tool_descriptions,
    )
    by_name = {d["function"]["name"]: d["function"] for d in tool_defs}
    assert by_name["record_memory"]["description"] == "Store one memory."


def test_tool_loop_recovers_from_raising_tool() -> None:
    # `search` is granted (tools.pyi) but unmocked in this sample -> it RAISES,
    # the loop turns it into an error observation, and the controller recovers by
    # calling the mocked `record_memory`. This is the Phase 3 acceptance case.
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    sample = Sample(
        name="recovers",
        input={"task": "store it"},
        mock_tools={"record_memory": {"ok": True}},
        stop_on=stop_after_turns(5),
    )
    result = run(_run_tool_loop(rich, sample, RecoveringFake()))

    assert result["status"] == "done"
    calls = [(e["ref"], bool(e.get("error"))) for e in result["trace"] if e["decision"] == "call"]
    assert ("search", True) in calls  # the raising tool became an error observation
    assert ("record_memory", False) in calls  # controller recovered on the next round


def test_tool_loop_chains_prior_tool_result() -> None:
    # search -> ["alice"]; the model must READ that observation out of the threaded
    # transcript and record "alice". The record_memory mock only returns ok:True
    # when it actually receives content=="alice", so a blind runner (finding #1)
    # would record "none" and get ok:False.
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    sample = Sample(
        name="chains",
        input={"task": "find and store the person"},
        mock_tools={
            "search": ["alice"],
            "record_memory": MockToolConfig(
                match=[({"content": "alice"}, {"ok": True, "stored": "alice"})],
                default={"ok": False},
            ),
        },
        stop_on=stop_when_terminal_tool("record_memory"),
    )
    result = run(_run_tool_loop(rich, sample, SearchThenRecordFake()))

    assert result["status"] == "done"
    # StopFn 'done' output is the post-tool observation, not the tool_calls dict.
    observations = result["output"]
    assert isinstance(observations, list)
    assert observations[0]["tool"] == "record_memory"
    assert observations[0]["output"] == {"ok": True, "stored": "alice"}


def test_stop_when_terminal_tool_output_is_the_observation() -> None:
    # finding #4: the clean StopFn 'done' output must be the tool result, never the
    # assistant tool-call reply dict.
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    sample = Sample(
        name="terminal",
        input={"task": "search"},
        mock_tools={"search": ["hit"]},
        stop_on=stop_when_terminal_tool("search"),
    )
    result = run(_run_tool_loop(rich, sample, AlwaysCallsFake("search", '{"query": "q"}')))

    assert result["status"] == "done"
    assert result["rounds"] == 1
    assert result["output"] == [{"id": "c1", "tool": "search", "output": ["hit"]}]


def test_stop_after_turns_collision_is_clean_done() -> None:
    # finding #4: execute_eval.ctx has max_rounds=4; stop_after_turns(4) collides
    # with it. The runner overrides max_rounds off the StopFn so the loop stops
    # cleanly as 'done' at 4 turns instead of tripping the hard cap as 'max_rounds'.
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    assert rich.reasoner.max_rounds == 4
    sample = Sample(
        name="collision",
        input={"task": "loop"},
        mock_tools={"record_memory": {"ok": True}},
        stop_on=stop_after_turns(4),
    )
    result = run(_run_tool_loop(rich, sample, AlwaysCallsFake("record_memory")))

    assert result["status"] == "done"
    assert result["rounds"] == 4


def test_cli_unknown_env_teaches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # finding #2: inside a project a misspelled --env is a loud teaching error
    # (exit 4), never a silent fallback to {}.
    (tmp_path / "julep.toml").write_text(
        '[env.staging]\n[env.staging.vars]\nSUMMARY_MODEL = "anthropic/x"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    code = main(["eval", str(FIXTURES / "episode_summary.ctx"), "--env", "stagng"])
    assert code == 4
    err = capsys.readouterr().err
    assert "unknown env" in err
    assert "stagng" in err


def test_cli_broken_eval_yaml_is_exit_4(tmp_path: Path) -> None:
    # finding #3: a broken eval config exits 4 (setup error), not 2 (below
    # threshold) — CI can tell a broken eval from a model regression.
    ctx = tmp_path / "broken.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text('model: "openai/gpt-eval@low"\n', encoding="utf-8")
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\nHi.\n\n<<< role:user >>>\nT: {{ task | default('', true) }}\n",
        encoding="utf-8",
    )
    (ctx / "eval.yaml").write_text(
        "threshold: 0.5\nbogus_key: 1\n\ndatasets:\n  - file: eval.py\n    format: py\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(
        "from dotctx.eval_types import Sample\n\n"
        "def sample(limit: int = -1):\n"
        "    return [Sample(name='s', input={'task': 'x'})]\n\n"
        "def score(_input, _output, _expected):\n"
        "    return 1.0\n",
        encoding="utf-8",
    )
    assert main(["eval", str(ctx)]) == 4


def test_tool_loop_finishes_on_natural_language_reply() -> None:
    # finding #1: a native-tools loop whose model finishes with a text message must
    # FINISH (status 'done'), not halt as 'controller_error'. The final content is
    # normalized to the single-shot {"content": ...} shape so a content scorer reads it.
    rich = load_rich_dotctx(str(FIXTURES / "execute_eval.ctx"), env={})
    sample = Sample(
        name="text_finish",
        input={"task": "store then answer"},
        mock_tools={"record_memory": {"ok": True}},
        stop_on=stop_when_non_tool(),
    )
    result = run(_run_tool_loop(rich, sample, CallThenTextFake()))

    assert result["status"] == "done"
    assert result["output"] == {"content": "all done, stored it"}
    calls = [e["ref"] for e in result["trace"] if e["decision"] == "call"]
    assert "record_memory" in calls  # the tool call really happened first


def test_resolve_mock_default_beats_responses_when_match_defined() -> None:
    # finding #2: when `match` is defined but nothing matches, the documented
    # `default` wins — `responses` is used ONLY when no `match` is defined.
    from julep.cli.evalrun import _resolve_mock

    counters: dict[str, int] = {}
    cfg = MockToolConfig(
        match=[({"query": "hits"}, ["a", "b"])],
        responses=[["SEQ"]],
        default=["DEF"],
    )
    assert _resolve_mock(cfg, {"query": "hits"}, counters, "search") == ["a", "b"]
    assert _resolve_mock(cfg, {"query": "miss"}, counters, "search") == ["DEF"]

    # responses cycle only when NO match is defined
    seq = MockToolConfig(responses=[["one"], ["two"]], default=["DEF"])
    assert _resolve_mock(seq, {"x": 1}, counters, "seq") == ["one"]
    assert _resolve_mock(seq, {"x": 1}, counters, "seq") == ["two"]
    assert _resolve_mock(seq, {"x": 1}, counters, "seq") == ["one"]


def test_cli_user_score_error_is_exit_4(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # finding #3: an exception from user score()/sample() code is a SETUP error
    # (exit 4), not a crash and not a below-threshold (exit 2) result.
    ctx = tmp_path / "scoreboom.ctx"
    ctx.mkdir()
    (ctx / "settings.yaml").write_text('model: "openai/gpt-eval@low"\n', encoding="utf-8")
    (ctx / "prompt.j2").write_text(
        "<<< role:system >>>\nHi.\n\n<<< role:user >>>\nT: {{ task | default('', true) }}\n",
        encoding="utf-8",
    )
    (ctx / "eval.yaml").write_text(
        "threshold: 0.5\n\ndatasets:\n  - file: eval.py\n    format: py\n",
        encoding="utf-8",
    )
    (ctx / "eval.py").write_text(
        "from dotctx.eval_types import Sample\n\n"
        "def sample(limit: int = -1):\n"
        "    return [Sample(name='s', input={'task': 'x'})]\n\n"
        "def score(_input, _output, _expected):\n"
        "    raise KeyError('boom')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "julep.cli.evalrun._resolve_acompletion",
        lambda a: SingleShotFake('{"x": 1}'),
    )
    assert main(["eval", str(ctx)]) == 4
