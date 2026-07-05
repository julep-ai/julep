from julep import deploy, flow, pure, switch_on
from julep.purity import is_registered


@pure("ws4_mark_review")
def mark_review(req: dict) -> dict:
    return {"decision": "review", "action": req["action"]}


@pure("ws4_mark_auto")
def mark_auto(req: dict) -> dict:
    return {"decision": "auto", "action": req["action"]}


@flow
def review(req: dict) -> dict:        # arm param label matches the subject handle label 'req'
    return mark_review(req)


@flow
def auto(req: dict) -> dict:
    return mark_auto(req)


@flow
def route(req: dict) -> dict:
    return switch_on(req, key="action", cases={"review": review, "auto": auto}, default=auto)


def test_switch_on_routes_by_field() -> None:
    dep = deploy(route, tools=[])
    assert dep.dry_run({"action": "review"}).value == {"decision": "review", "action": "review"}
    assert dep.dry_run({"action": "auto"}).value == {"decision": "auto", "action": "auto"}


def test_switch_on_selector_is_registered_and_source_pinned() -> None:
    # Defining `route` (above) must have minted + registered a deterministic selector pure.
    assert is_registered("switch_on.action")


def test_switch_on_rejects_conflicting_selector_name() -> None:
    # If some unrelated pure already squats on the auto-derived ``switch_on.<key>``
    # name, switch_on must NOT silently reuse it as the selector — it must surface
    # the source-hash conflict. Regression for the is_registered() skip
    # (Codex PR#9, P2).
    import pytest

    @pure("switch_on.kind")  # squats on the selector name with unrelated behavior
    def squatter(value: dict) -> str:
        return "always-review"

    with pytest.raises(ValueError, match="different source"):

        @flow
        def route_conflict(req: dict) -> dict:
            return switch_on(req, key="kind", cases={"review": review, "auto": auto})
