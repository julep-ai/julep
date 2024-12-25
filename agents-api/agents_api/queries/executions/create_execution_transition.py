from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    CreateTransitionRequest,
    Transition,
)
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    wrap_in_class,
)

sql_query = """
INSERT INTO transitions
(
    execution_id,
    transition_id,
    type,
    step_definition,
    step_label,
    current_step,
    next_step,
    output,
    task_token,
    metadata
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9,
    $10
)
"""


def validate_transition_targets(data: CreateTransitionRequest) -> None:
    # Make sure the current/next targets are valid
    match data.type:
        case "finish_branch":
            pass  # TODO: Implement
        case "finish" | "error" | "cancelled":
            pass

            ### FIXME: HACK: Fix this and uncomment

            ### assert (
            ###     data.next is None
            ### ), "Next target must be None for finish/finish_branch/error/cancelled"

        case "init_branch" | "init":
            assert (
                data.next and data.current.step == data.next.step == 0
            ), "Next target must be same as current for init_branch/init and step 0"

        case "wait":
            assert data.next is None, "Next target must be None for wait"

        case "resume" | "step":
            assert data.next is not None, "Next target must be provided for resume/step"

            if data.next.workflow == data.current.workflow:
                assert (
                    data.next.step > data.current.step
                ), "Next step must be greater than current"

        case _:
            raise ValueError(f"Invalid transition type: {data.type}")


# rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
wrap_in_class(
    Transition,
    transform=lambda d: {
        **d,
        "id": d["transition_id"],
        "current": {"workflow": d["current"][0], "step": d["current"][1]},
        "next": d["next"] and {"workflow": d["next"][0], "step": d["next"][1]},
    },
    one=True,
)


@pg_query
@increase_counter("create_execution_transition")
@beartype
async def create_execution_transition(
    *,
    developer_id: UUID,
    execution_id: UUID,
    data: CreateTransitionRequest,
    # Only one of these needed
    transition_id: UUID | None = None,
    task_token: str | None = None,
) -> tuple[list[str | None], dict]:
    transition_id = transition_id or uuid7()
    data.metadata = data.metadata or {}
    data.execution_id = execution_id

    # Dump to json
    if isinstance(data.output, list):
        data.output = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in data.output
        ]

    elif hasattr(data.output, "model_dump"):
        data.output = data.output.model_dump(mode="json")

    # Prepare the transition data
    transition_data = data.model_dump(exclude_unset=True, exclude={"id"})

    # Parse the current and next targets
    validate_transition_targets(data)
    current_target = transition_data.pop("current")
    next_target = transition_data.pop("next")

    transition_data["current"] = (current_target["workflow"], current_target["step"])
    transition_data["next"] = next_target and (
        next_target["workflow"],
        next_target["step"],
    )

    return (
        sql_query,
        [
            execution_id,
            transition_id,
            data.type,
            {},
            None,
            transition_data["current"],
            transition_data["next"],
            data.output,
            task_token,
            data.metadata,
        ],
    )
