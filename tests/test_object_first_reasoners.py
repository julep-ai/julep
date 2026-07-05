import subprocess
from typing import TypedDict

import pytest

from julep import Reasoner


class Reply(TypedDict):
    answer: str


def test_reply_accepts_typeddict() -> None:
    r = Reasoner(name="r1", model="anthropic:claude-haiku-4-5-20251001", reply=Reply)
    assert isinstance(r.reply_schema, dict) and r.reply_schema  # materialized schema


def test_reply_accepts_raw_schema_dict() -> None:
    schema = {"regime": "str", "confidence": "number"}
    r = Reasoner(name="r2", model="anthropic:claude-haiku-4-5-20251001", reply=schema)
    assert r.reply_schema == schema  # raw dict stored as-is


def test_reply_schema_kwarg_is_gone() -> None:
    with pytest.raises(TypeError):
        Reasoner(  # type: ignore[call-arg]
            name="r3", model="anthropic:claude-haiku-4-5-20251001",
            reply_schema={"answer": "str"},
        )


def test_deploy_registers_reasoner_object_and_wire_is_identical() -> None:
    from julep import Reasoner, deploy, flow, pure, think, tool

    @tool(effect="read", idempotent=True)
    def lookup(t: str) -> dict:
        return {"q": "billing"}

    @pure("ws5_prompt2")
    def prompt(hit: dict) -> dict:
        return {"q": hit["q"]}

    r = Reasoner(name="ws5_reply2", model="anthropic:claude-haiku-4-5-20251001",
                 system="x", reply={"reply": "str"})

    @flow
    def triage(t: str) -> dict:
        hit = lookup(t)
        return prompt(hit) | think(r, prompt(hit))

    # Object-first: no register_reasoner call anywhere.
    dep = deploy(triage, tools=[lookup], reasoners=[r])
    dep_by_name = deploy(triage, tools=[lookup], reasoners=[r.name])
    assert dep.artifact_hash  # froze successfully
    assert "ws5_reply2" in dep.artifact_components["reasoners"]  # name landed in the artifact
    assert dep.artifact_components == dep_by_name.artifact_components


def test_agent_accepts_reasoner_object() -> None:
    from julep import Agent, Reasoner

    r = Reasoner(name="ws5_ctrl", model="anthropic:claude-haiku-4-5-20251001", reply={"out": "str"})
    agent = Agent(reasoner=r)                 # object, not a string, no prior registration
    # the agent resolved the reasoner by name under the hood
    assert agent is not None


def test_agent_object_preserves_model_and_system() -> None:
    # Agent(reasoner=obj) must build a controller that USES the object's model and
    # system, not the object's *name*. Regression for the object-first path sending
    # `r.name` to the provider as if it were the model id (Codex PR#9, P1).
    from julep import Agent, Reasoner
    from julep.dotctx import get_reasoner

    r = Reasoner(
        name="ws5_ctrl_modelsys",
        model="anthropic:claude-haiku-4-5-20251001",
        system="be terse",
        reply={"out": "str"},
    )
    agent = Agent(reasoner=r)
    ctrl = get_reasoner(agent.name)  # the controller reasoner the loop actually calls
    assert ctrl.model == "anthropic:claude-haiku-4-5-20251001"  # NOT "ws5_ctrl_modelsys"
    assert ctrl.system == "be terse"  # the object's system is not dropped


def test_agent_replace_reasoner_object_preserves_model_and_system() -> None:
    # Agent.replace(reasoner=obj) must mirror __init__: use the object's model and
    # system, not its name. Regression for the second object-first conversion site
    # missed by the initial fix (Codex re-review of PR#9, P2).
    from julep import Agent, Reasoner
    from julep.dotctx import get_reasoner

    base = Agent(reasoner="anthropic:old-model", instructions="old")
    r2 = Reasoner(
        name="ws5_replace_obj",
        model="anthropic:model-new",
        system="new-sys",
        reply={"o": "str"},
    )
    agent2 = base.replace(reasoner=r2)
    ctrl = get_reasoner(agent2.name)
    assert ctrl.model == "anthropic:model-new"  # NOT "ws5_replace_obj"
    assert ctrl.system == "new-sys"  # the new object's system, not the stale "old"


def test_capability_models_enforced_for_object_reasoner() -> None:
    # think(obj) must register the object so an explicit CapabilityManifest can
    # enforce its model-id allow-list. Regression for the bypass where an
    # unregistered object reasoner made CAP_MODEL_ID_DENIED silently skip
    # (Codex PR#9, P1). deploy() forbids reasoners= with capabilities=, so the
    # object can only become resolvable via think(obj).
    from julep import CapabilityManifest, Reasoner, deploy, flow, think, tool
    from julep.errors import ValidationError

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"q": t}

    r = Reasoner(
        name="ws5_cap_obj",
        model="anthropic:claude-haiku-4-5-20251001",
        reply={"o": "str"},
    )

    @flow
    def f(t: str) -> dict:
        return think(r, lk(t))

    caps = CapabilityManifest.from_dict(
        {
            "tools": [{"name": "lk", "effect": "read", "idempotency": "native"}],
            "models": ["only-this-other-model"],  # r.model deliberately not granted
        }
    )
    with pytest.raises(ValidationError) as ei:
        deploy(f, tools=[lk], capabilities=caps)
    assert any(d.code == "CAP_MODEL_ID_DENIED" for d in ei.value.diagnostics)


def test_register_reasoner_not_public() -> None:
    import julep

    assert not hasattr(julep, "register_reasoner")
    assert "register_reasoner" not in julep.__all__


def test_think_accepts_object_at_authoring_time() -> None:
    from julep import Reasoner, flow, pure, think, tool

    @tool(effect="read", idempotent=True)
    def lk(t: str) -> dict:
        return {"q": "b"}

    @pure("ws5_p4")
    def pp(h: dict) -> dict:
        return {"q": h["q"]}

    r = Reasoner(name="ws5_think_obj", model="anthropic:claude-haiku-4-5-20251001", reply={"o": "str"})

    @flow
    def f(t: str) -> dict:
        return pp(lk(t)) | think(r, pp(lk(t)))

    assert f is not None  # @flow define-time accepted think(r, ...)


def test_no_public_register_reasoner_or_reply_schema_left() -> None:
    # register_reasoner must not appear as a public/import symbol; reply_schema must
    # not appear as a constructor kwarg anywhere in package, examples, docs, or the
    # user-facing README/CONTRIBUTING (the PyPI landing page included).
    out = subprocess.run(
        ["grep", "-rn", "register_reasoner\\|reply_schema=",
         "julep", "examples", "docs-site/content", "README.md", "CONTRIBUTING.md"],
        capture_output=True, text=True,
    ).stdout
    # Allowed hits are the internal Registry method: its definition and method
    # calls on a registry instance (``DEFAULT_REGISTRY.register_reasoner`` or a
    # supplied ``registry.register_reasoner``). The removed public module-level
    # ``register_reasoner`` function / import has no leading dot and is flagged.
    leftovers = [
        ln for ln in out.splitlines()
        if ".register_reasoner" not in ln
        and "def register_reasoner(self" not in ln
    ]
    assert not leftovers, "leftover register_reasoner/reply_schema=: \n" + "\n".join(leftovers)
