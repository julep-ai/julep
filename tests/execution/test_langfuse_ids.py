from composable_agents.execution.langfuse import trace_id_for, span_id_for

def test_ids_are_stable_and_sized():
    assert trace_id_for("run-1") == trace_id_for("run-1")
    assert trace_id_for("run-1") != trace_id_for("run-2")
    assert 0 < trace_id_for("run-1") < (1 << 128)
    assert 0 < span_id_for("c0") < (1 << 64)
    assert span_id_for("c0") != span_id_for("c1")
