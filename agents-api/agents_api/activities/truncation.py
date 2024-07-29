from uuid import UUID

from temporalio import activity

from agents_api.autogen.openapi_model import Role
from agents_api.common.protocol.entries import Entry
from agents_api.models.entry.delete_entries import delete_entries
from agents_api.models.entry.entries_summarization import get_toplevel_entries_query


def get_extra_entries(messages: list[Entry], token_count_threshold: int) -> list[UUID]:
    if not len(messages):
        return messages

    result: list[UUID] = []
    token_cnt, offset = 0, 0
    if messages[0].role == Role.system:
        token_cnt, offset = messages[0].token_count, 1

    for m in reversed(messages[offset:]):
        token_cnt += m.token_count
        if token_cnt < token_count_threshold:
            continue
        else:
            result.append(m.id)

    return result


@activity.defn
async def truncation(session_id: str, token_count_threshold: int) -> None:
    session_id = UUID(session_id)

    delete_entries(
        get_extra_entries(
            [
                Entry(
                    entry_id=row["entry_id"],
                    session_id=session_id,
                    source=row["source"],
                    role=Role(row["role"]),
                    name=row["name"],
                    content=row["content"],
                    created_at=row["created_at"],
                    timestamp=row["timestamp"],
                )
                for _, row in get_toplevel_entries_query(
                    session_id=session_id
                ).iterrows()
            ],
            token_count_threshold,
        ),
    )
