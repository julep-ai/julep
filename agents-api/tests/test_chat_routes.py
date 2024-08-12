# Tests for session queries

from ward import test

from agents_api.clients import embed, litellm
from agents_api.models.session.prepare_chat_context import prepare_chat_context
from agents_api.routers.sessions.chat import get_messages
from tests.fixtures import (
    cozo_client,
    make_request,
    patch_embed_acompletion,
    test_agent,
    test_developer,
    test_developer_id,
    test_session,
    test_tool,
    test_user,
)


@test("chat: check that patching libs works")
async def _(
    _=patch_embed_acompletion,
):
    assert (await litellm.acompletion(model="gpt-4o", messages=[])).id == "fake_id"
    assert (await embed.embed())[0][0] == 1.0


@test("chat: check that get_messages works")
async def _(
    developer=test_developer,
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
    session=test_session,
    tool=test_tool,
    user=test_user,
    mocks=patch_embed_acompletion,
):
    (embed, _) = mocks

    chat_context = prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        client=client,
    )

    session_id = session.id

    new_raw_messages = [{"role": "user", "content": "hello"}]

    past_messages, doc_references = await get_messages(
        developer=developer,
        session_id=session_id,
        new_raw_messages=new_raw_messages,
        chat_context=chat_context,
    )

    assert isinstance(past_messages, list)
    assert isinstance(doc_references, list)

    # Check that embed was called at least once
    embed.assert_called()


@test("chat: check that chat route calls both mocks")
async def _(
    make_request=make_request,
    session=test_session,
    mocks=patch_embed_acompletion,
):
    (embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response.raise_for_status()

    # Check that both mocks were called at least once
    embed.assert_called()
    acompletion.assert_called()
