"""Email approval — Rung 2-3.

Shows combinators for an approval flow: draft an email, pass through
``human_gate()``, then call an approval-required ``send_email`` tool. The dry run
uses ``InMemoryEnv`` stubs, so it needs no API key, Temporal, network, clock, or
RNG.
"""

from __future__ import annotations

import asyncio
from typing import Any

from julep import (
    CapabilityManifest,
    Deployment,
    Effect,
    HUMAN_GATE_TOOL,
    Idempotency,
    InMemoryEnv,
    InMemoryProjection,
    NativeToolSpec,
    ProjectionEmitter,
    ToolContract,
    call,
    deploy,
    human_gate,
    interpret,
    seq,
)
from julep.freeze import McpSnapshot


TOOL_DRAFT_EMAIL = "draft_email"
TOOL_SEND_EMAIL = "send_email"

REQUEST = {
    "to": "customer@example.com",
    "topic": "duplicate billing charge",
}


def snapshot() -> McpSnapshot:
    return McpSnapshot(
        native={
            TOOL_DRAFT_EMAIL: NativeToolSpec(
                input_schema={},
                contract=ToolContract(Effect.READ, Idempotency.NATIVE),
            ),
            TOOL_SEND_EMAIL: NativeToolSpec(
                input_schema={},
                contract=ToolContract(Effect.DANGEROUS, Idempotency.NONE),
            ),
        }
    )


def capabilities() -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [
                {
                    "name": TOOL_DRAFT_EMAIL,
                    "effect": "read",
                    "idempotency": "native",
                },
                {
                    "name": HUMAN_GATE_TOOL,
                    "effect": "external",
                    "idempotency": "none",
                },
                {
                    "name": TOOL_SEND_EMAIL,
                    "effect": "dangerous",
                    "idempotency": "none",
                    "approval": "required",
                },
            ]
        }
    )


def build() -> Deployment:
    # Reversibility rule: every path to send_email is dominated by human_gate().
    flow = seq(call(TOOL_DRAFT_EMAIL), human_gate(prompt="Approve outbound email?"), call(TOOL_SEND_EMAIL))
    return deploy(flow, snapshot(), capabilities=capabilities())


async def run_demo(
    request: dict[str, str] | None = None,
    *,
    sent: list[dict[str, Any]] | None = None,
) -> Any:
    deployment = build()
    sent_log = sent if sent is not None else []

    def draft_email(value: dict[str, str]) -> dict[str, str]:
        return {
            "to": value["to"],
            "subject": "Update on your duplicate charge",
            "body": "We found the duplicate charge and will refund it today.",
        }

    def send_email(gate_result: dict[str, Any]) -> dict[str, Any]:
        assert gate_result["approved"] is True
        draft = gate_result["input"]
        receipt = {
            "status": "sent",
            "to": draft["to"],
            "subject": draft["subject"],
            "approved_by": gate_result["reviewed_by"],
        }
        sent_log.append(receipt)
        return receipt

    env = InMemoryEnv(
        deployment.manifest,
        ProjectionEmitter(InMemoryProjection()),
        tools={
            TOOL_DRAFT_EMAIL: draft_email,
            TOOL_SEND_EMAIL: send_email,
        },
        gate=lambda value: {
            "approved": True,
            "input": value,
            "reviewed_by": "cookbook-reviewer",
        },
        max_calls=deployment.capabilities.max_call_limits() if deployment.capabilities else {},
    )
    return await interpret(deployment.flow, request or REQUEST, env)


def main() -> None:
    result = asyncio.run(run_demo())
    print("Email approval result:")
    print(result.value)


if __name__ == "__main__":
    main()
