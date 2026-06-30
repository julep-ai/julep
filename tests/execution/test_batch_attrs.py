import pytest

pytest.importorskip("temporalio")

from composable_agents.execution.reasoner_batch import batch_reply_attrs  # helper added in Step 3
from composable_agents.execution.batch_provider import BatchReply

def test_batch_reply_attrs_carry_usage():
    attrs = batch_reply_attrs(
        BatchReply(reply={"a": 1}, input_tokens=20, output_tokens=8),
        model="claude-x", provider="anthropic",
        submitted_at=100.0, completed_at=160.0,
    )
    assert attrs["llm.model"] == "claude-x"
    assert attrs["llm.usage"] == {"input": 20, "output": 8, "total": 28}
    assert attrs["llm.started_at"] == 100.0
    assert attrs["llm.ended_at"] == 160.0
