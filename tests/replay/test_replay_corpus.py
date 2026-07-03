from __future__ import annotations

import json

import pytest

from composable_agents import HAVE_TEMPORAL

pytestmark = pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")

if HAVE_TEMPORAL:
    from temporalio.client import WorkflowHistory

    import composable_agents.execution.harness as harness
    from conftest import run
    from record_histories import CORPUS, HISTORIES_DIR, make_replayer, setup_registries

    def _manifest() -> dict[str, str]:
        # name -> real recorded workflow id (to_json drops it, but replay needs
        # it: some workflows derive child ids from workflow.info().workflow_id).
        return json.loads((HISTORIES_DIR / "manifest.json").read_text())

    def _load(name: str) -> WorkflowHistory:
        return WorkflowHistory.from_json(
            _manifest()[name],
            (HISTORIES_DIR / f"{name}.json").read_text(),
        )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
@pytest.mark.parametrize("name", CORPUS if HAVE_TEMPORAL else [])
def test_corpus_replays_clean(name: str) -> None:
    setup_registries()
    missing = [item for item in CORPUS if not (HISTORIES_DIR / f"{item}.json").exists()]
    assert not missing, f"missing replay corpus histories: {missing}"
    run(make_replayer().replay_workflow(_load(name)))


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_scheduling_mutation_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    setup_registries()
    history = _load("flow_par_each_sub")
    original = harness.gather_bounded

    async def _reversed(coros, *, max_parallel):  # type: ignore[no-untyped-def]
        return await original(list(reversed(list(coros))), max_parallel=max_parallel)

    monkeypatch.setattr(harness, "gather_bounded", _reversed)
    with pytest.raises(Exception, match="(?i)(replay|nondetermin|workflow task|history)"):
        run(make_replayer().replay_workflow(history))
