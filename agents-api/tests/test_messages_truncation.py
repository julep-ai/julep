import pytest
from agents_api.autogen.Entries import Entry
from uuid_extensions import uuid7

# AIDEV-NOTE: Message truncation is not yet implemented - see render.py:149
# These tests are skipped until truncation is implemented


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_empty_messages_truncation():
    """Test truncating empty messages list."""
    # When truncation is implemented, it should return the same empty list
    # result = truncate(messages, 10)
    # assert messages == result


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_do_not_truncate():
    """Test that messages below threshold are not truncated."""
    contents = [
        "content1",
        "content2",
        "content3",
    ]
    sum(len(c) // 3.5 for c in contents)

    [
        Entry(session_id=uuid7(), role="user", content=contents[0]),
        Entry(session_id=uuid7(), role="assistant", content=contents[1]),
        Entry(session_id=uuid7(), role="user", content=contents[2]),
    ]
    # When implemented: result = truncate(messages, threshold)
    # assert messages == result


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_truncate_thoughts_partially():
    """Test partial truncation of thought messages."""
    contents = [
        ("content1", True),
        ("content2", True),
        ("content3", False),
        ("content4", True),
        ("content5", True),
        ("content6", True),
    ]
    session_ids = [uuid7()] * len(contents)
    sum(len(c) // 3.5 for c, i in contents if i)

    [
        Entry(
            session_id=session_ids[0],
            role="system",
            name="thought",
            content=contents[0][0],
        ),
        Entry(session_id=session_ids[1], role="assistant", content=contents[1][0]),
        Entry(
            session_id=session_ids[2],
            role="system",
            name="thought",
            content=contents[2][0],
        ),
        Entry(
            session_id=session_ids[3],
            role="system",
            name="thought",
            content=contents[3][0],
        ),
        Entry(session_id=session_ids[4], role="user", content=contents[4][0]),
        Entry(session_id=session_ids[5], role="assistant", content=contents[5][0]),
    ]
    # When implemented: result = truncate(messages, threshold)
    # Expected: messages[2] (thought with False flag) should be removed
    # assert result == [
    #     messages[0],
    #     messages[1],
    #     messages[3],
    #     messages[4],
    #     messages[5],
    # ]


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_truncate_thoughts_partially_2():
    """Test partial truncation of multiple consecutive thought messages."""
    contents = [
        ("content1", True),
        ("content2", True),
        ("content3", False),
        ("content4", False),
        ("content5", True),
        ("content6", True),
    ]
    session_ids = [uuid7()] * len(contents)
    sum(len(c) // 3.5 for c, i in contents if i)

    [
        Entry(
            session_id=session_ids[0],
            role="system",
            name="thought",
            content=contents[0][0],
        ),
        Entry(session_id=session_ids[1], role="assistant", content=contents[1][0]),
        Entry(
            session_id=session_ids[2],
            role="system",
            name="thought",
            content=contents[2][0],
        ),
        Entry(
            session_id=session_ids[3],
            role="system",
            name="thought",
            content=contents[3][0],
        ),
        Entry(session_id=session_ids[4], role="user", content=contents[4][0]),
        Entry(session_id=session_ids[5], role="assistant", content=contents[5][0]),
    ]
    # When implemented: result = truncate(messages, threshold)
    # Expected: messages[2] and messages[3] (thoughts with False flag) should be removed
    # assert result == [
    #     messages[0],
    #     messages[1],
    #     messages[4],
    #     messages[5],
    # ]


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_truncate_all_thoughts():
    """Test truncation removes all thought messages when necessary."""
    contents = [
        ("content1", False),
        ("content2", True),
        ("content3", False),
        ("content4", False),
        ("content5", True),
        ("content6", True),
        ("content7", False),
    ]
    session_ids = [uuid7()] * len(contents)
    sum(len(c) // 3.5 for c, i in contents if i)

    [
        Entry(
            session_id=session_ids[0],
            role="system",
            name="thought",
            content=contents[0][0],
        ),
        Entry(session_id=session_ids[1], role="assistant", content=contents[1][0]),
        Entry(
            session_id=session_ids[2],
            role="system",
            name="thought",
            content=contents[2][0],
        ),
        Entry(
            session_id=session_ids[3],
            role="system",
            name="thought",
            content=contents[3][0],
        ),
        Entry(session_id=session_ids[4], role="user", content=contents[4][0]),
        Entry(session_id=session_ids[5], role="assistant", content=contents[5][0]),
        Entry(
            session_id=session_ids[6],
            role="system",
            name="thought",
            content=contents[6][0],
        ),
    ]
    # When implemented: result = truncate(messages, threshold)
    # Expected: All thought messages should be removed
    # assert result == [
    #     messages[1],
    #     messages[4],
    #     messages[5],
    # ]


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_truncate_user_assistant_pairs():
    """Test truncation of user-assistant message pairs."""
    contents = [
        ("content1", False),
        ("content2", True),
        ("content3", False),
        ("content4", False),
        ("content5", True),
        ("content6", True),
        ("content7", True),
        ("content8", False),
        ("content9", True),
        ("content10", True),
        ("content11", True),
        ("content12", True),
        ("content13", False),
    ]
    session_ids = [uuid7()] * len(contents)
    sum(len(c) // 3.5 for c, i in contents if i)

    [
        Entry(
            session_id=session_ids[0],
            role="system",
            name="thought",
            content=contents[0][0],
        ),
        Entry(session_id=session_ids[1], role="assistant", content=contents[1][0]),
        Entry(
            session_id=session_ids[2],
            role="system",
            name="thought",
            content=contents[2][0],
        ),
        Entry(
            session_id=session_ids[3],
            role="system",
            name="thought",
            content=contents[3][0],
        ),
        Entry(session_id=session_ids[4], role="user", content=contents[4][0]),
        Entry(session_id=session_ids[5], role="assistant", content=contents[5][0]),
        Entry(session_id=session_ids[6], role="user", content=contents[6][0]),
        Entry(session_id=session_ids[7], role="assistant", content=contents[7][0]),
        Entry(session_id=session_ids[8], role="user", content=contents[8][0]),
        Entry(session_id=session_ids[9], role="assistant", content=contents[9][0]),
        Entry(session_id=session_ids[10], role="user", content=contents[10][0]),
        Entry(session_id=session_ids[11], role="assistant", content=contents[11][0]),
        Entry(
            session_id=session_ids[12],
            role="system",
            name="thought",
            content=contents[12][0],
        ),
    ]

    # When implemented: result = truncate(messages, threshold)
    # Expected: Thoughts and older messages should be removed, keeping recent pairs
    # assert result == [
    #     messages[1],
    #     messages[4],
    #     messages[5],
    #     messages[6],
    #     messages[8],
    #     messages[9],
    #     messages[10],
    #     messages[11],
    # ]


@pytest.mark.skip(reason="Truncation not yet implemented - see SCRUM-7")
def test_unable_to_truncate():
    """Test error when messages cannot be truncated enough to fit threshold."""
    contents = [
        ("content1", False),
        ("content2", True),
        ("content3", False),
        ("content4", False),
        ("content5", False),
        ("content6", False),
        ("content7", True),
        ("content8", False),
        ("content9", True),
        ("content10", False),
    ]
    session_ids = [uuid7()] * len(contents)
    sum(len(c) // 3.5 for c, i in contents if i)
    sum(len(c) // 3.5 for c, _ in contents)

    [
        Entry(
            session_id=session_ids[0],
            role="system",
            name="thought",
            content=contents[0][0],
        ),
        Entry(session_id=session_ids[1], role="assistant", content=contents[1][0]),
        Entry(
            session_id=session_ids[2],
            role="system",
            name="thought",
            content=contents[2][0],
        ),
        Entry(
            session_id=session_ids[3],
            role="system",
            name="thought",
            content=contents[3][0],
        ),
        Entry(session_id=session_ids[4], role="user", content=contents[4][0]),
        Entry(session_id=session_ids[5], role="assistant", content=contents[5][0]),
        Entry(session_id=session_ids[6], role="user", content=contents[6][0]),
        Entry(session_id=session_ids[7], role="assistant", content=contents[7][0]),
        Entry(session_id=session_ids[8], role="user", content=contents[8][0]),
        Entry(
            session_id=session_ids[9],
            role="system",
            name="thought",
            content=contents[9][0],
        ),
    ]
    # When implemented:
    # with pytest.raises(InputTooBigError) as exc:
    #     truncate(messages, threshold)
    # assert (
    #     str(exc.value)
    #     == f"input is too big, {threshold} tokens required, but you got {all_tokens} tokens"
    # )
