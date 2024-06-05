import time
import uuid
from ward import test
from agents_api.common.protocol.entries import Entry
from agents_api.autogen.openapi_model import Role
from tests.fixtures import base_session


@test("truncate entries, do not strip system message")
def _(session=base_session):
    session_ids = [uuid.uuid4()] * 3
    entry_ids = [uuid.uuid4()] * 3
    now = time.time()
    messages = [
        Entry(
            entry_id=entry_ids[0],
            session_id=session_ids[0],
            role=Role.system,
            content="content 1",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[1],
            session_id=session_ids[1],
            role=Role.assistant,
            content="content 2",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[2],
            session_id=session_ids[2],
            role=Role.user,
            content="content 3",
            created_at=now,
            timestamp=now,
        ),
    ]

    expected_result = [
        Entry(
            entry_id=entry_ids[0],
            session_id=session_ids[0],
            role=Role.system,
            content="content 1",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[2],
            session_id=session_ids[2],
            role=Role.user,
            content="content 3",
            created_at=now,
            timestamp=now,
        ),
    ]
    threshold = sum([m.token_count for m in messages]) - 1
    result = session._truncate_entries(messages, threshold)

    assert result == expected_result


@test("truncate entries")
def _(session=base_session):
    session_ids = [uuid.uuid4()] * 3
    entry_ids = [uuid.uuid4()] * 3
    now = time.time()
    messages = [
        Entry(
            entry_id=entry_ids[0],
            session_id=session_ids[0],
            role=Role.user,
            content="content 1",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[1],
            session_id=session_ids[1],
            role=Role.assistant,
            content="content 2",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[2],
            session_id=session_ids[2],
            role=Role.user,
            content="content 3",
            created_at=now,
            timestamp=now,
        ),
    ]

    expected_result = [
        Entry(
            entry_id=entry_ids[1],
            session_id=session_ids[1],
            role=Role.assistant,
            content="content 2",
            created_at=now,
            timestamp=now,
        ),
        Entry(
            entry_id=entry_ids[2],
            session_id=session_ids[2],
            role=Role.user,
            content="content 3",
            created_at=now,
            timestamp=now,
        ),
    ]
    threshold = sum([m.token_count for m in messages]) - 1
    result = session._truncate_entries(messages, threshold)

    assert result == expected_result


@test("truncate entries, no change if empty")
def _(session=base_session):
    messages = []
    result = session._truncate_entries(messages, 1)

    assert result == []
