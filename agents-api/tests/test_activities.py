# import time
# import uuid

# from ward import test

# from agents_api.activities.truncation import get_extra_entries
# from agents_api.autogen.openapi_model import Role
# from agents_api.common.protocol.entries import Entry


# @test("get extra entries, do not strip system message")
# def _():
#     session_ids = [uuid.uuid4()] * 3
#     entry_ids = [uuid.uuid4()] * 3
#     now = time.time()
#     messages = [
#         Entry(
#             entry_id=entry_ids[0],
#             session_id=session_ids[0],
#             role=Role.system,
#             content="content 1",
#             created_at=now,
#             timestamp=now,
#         ),
#         Entry(
#             entry_id=entry_ids[1],
#             session_id=session_ids[1],
#             role=Role.assistant,
#             content="content 2",
#             created_at=now,
#             timestamp=now,
#         ),
#         Entry(
#             entry_id=entry_ids[2],
#             session_id=session_ids[2],
#             role=Role.user,
#             content="content 3",
#             created_at=now,
#             timestamp=now,
#         ),
#     ]

#     threshold = sum([m.token_count for m in messages]) - 1
#     result = get_extra_entries(messages, threshold)

#     assert result == [messages[1].id]


# @test("get extra entries")
# def _():
#     session_ids = [uuid.uuid4()] * 3
#     entry_ids = [uuid.uuid4()] * 3
#     now = time.time()
#     messages = [
#         Entry(
#             entry_id=entry_ids[0],
#             session_id=session_ids[0],
#             role=Role.user,
#             content="content 1",
#             created_at=now,
#             timestamp=now,
#         ),
#         Entry(
#             entry_id=entry_ids[1],
#             session_id=session_ids[1],
#             role=Role.assistant,
#             content="content 2",
#             created_at=now,
#             timestamp=now,
#         ),
#         Entry(
#             entry_id=entry_ids[2],
#             session_id=session_ids[2],
#             role=Role.user,
#             content="content 3",
#             created_at=now,
#             timestamp=now,
#         ),
#     ]

#     threshold = sum([m.token_count for m in messages]) - 1
#     result = get_extra_entries(messages, threshold)

#     assert result == [messages[0].id]


# @test("get extra entries, no change if empty")
# def _():
#     messages = []
#     result = get_extra_entries(messages, 1)

#     assert result == []
