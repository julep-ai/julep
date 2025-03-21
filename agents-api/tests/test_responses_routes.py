from agents_api.autogen.openapi_model import (
    CreateEntryRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.entries import create_entries
from ward import skip, test

from .fixtures import (
    make_request,
    # mock_openai_client,
    patch_embed_acompletion,
    pg_dsn,
    test_developer_id,
    test_session,
)


@test("routes: check basic text message response")
async def _(
    # mock_openai_client=mock_openai_client,
    make_request=make_request,
    mocks=patch_embed_acompletion,
):
    """Test creating a basic text message response."""
    (_, acompletion) = mocks

    data = {
        "input": "What are the top 5 skincare products?",
        "model": "gpt-4o-mini",
    }

    # response = mock_openai_client.responses.create(
    #     **data,
    # )
    response = make_request(
        method="POST",
        url="/responses",
        json=data,
    )

    response.raise_for_status()
    result = response.json()
    # Ensure common response fields are present
    assert "id" in result
    assert "created_at" in result
    assert "status" in result
    assert "output" in result
    assert len(result["output"]) > 0
    assert result["output"][0]["type"] == "message"
    assert result["output"][0]["role"] == "assistant"
    # Ensure the model was called once
    acompletion.assert_called_once()


# @skip("Needs to be implemented")
@test("routes: check image URL processing")
async def _(
    # mock_openai_client=mock_openai_client,
    make_request=make_request,
    mocks=patch_embed_acompletion,
):
    """Test creating a response with image URL input."""

    (_, _acompletion) = mocks

    data = {
        "model": "gpt-4o-mini",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "What's in this image?"},
                    {"type": "input_image", "image_url": "https://example.com/image.jpg"},
                ],
            }
        ],
    }

    # Image URL message format
    # response = mock_openai_client.responses.create(
    #     **data,
    # )
    response = make_request(
        method="POST",
        url="/responses",
        json=data,
    )

    response.raise_for_status()
    data = response.json()
    # Ensure common response fields are present
    assert "created_at" in data
    assert "status" in data

    assert "id" in data
    assert "output" in data
    assert data["status"] == "completed"

    # # Verify model was called with image content
    # acompletion.assert_called_once()
    # call_args = acompletion.call_args[1]
    # assert "messages" in call_args

    # # Check that the image URL was passed correctly to the model
    # passed_messages = call_args["messages"]
    # user_messages = [msg for msg in passed_messages if msg.get("role") == "user"]
    # assert any(isinstance(msg.get("content"), list) for msg in user_messages)


@skip("Needs to be implemented")
@test("routes: check search tool execution")
async def _(
    # mock_openai_client=mock_openai_client,
    make_request=make_request,
    mocks=patch_embed_acompletion,
):
    """Test creating a response with search tool usage."""

    (_, _acompletion) = mocks

    data = {
        "model": "gpt-4o-mini",
        "input": "What are the latest news?",
        "tools": [{"type": "web_search_preview"}],
    }

    # Create a response with search tool
    # response = mock_openai_client.responses.create(
    #     **data,
    # )

    response = make_request(
        method="POST",
        url="/responses",
        json=data,
    )

    response.raise_for_status()
    data = response.json()
    # Common response fields check
    assert "created_at" in data
    assert "status" in data

    # Verify response structure
    assert "id" in data
    assert "output" in data

    # # Find web search tool in output
    # web_search_outputs = [out for out in data["output"] if out.get("type") == "web_search_preview"]
    # assert len(web_search_outputs) > 0

    # Verify model completion was called twice (initial + after tool call)
    # assert acompletion.call_count == 2


@skip("Needs to be fixed")
@test("routes: get response")
async def _(
    # mock_openai_client=mock_openai_client,
    make_request=make_request,
    dsn=pg_dsn,
    test_developer_id=test_developer_id,
    test_session=test_session,
):
    """
    Test the GET /responses/{response_id} endpoint using a history fixture.

    """

    pool = await create_db_pool(dsn=dsn)

    # Create a user entry request
    user_entry = CreateEntryRequest.from_model_input(
        model="gpt-4o-mini", role="user", source="api_request", content="What is the weather?"
    )

    # Create an assistant entry request
    assistant_entry = CreateEntryRequest.from_model_input(
        model="gpt-4o-mini",
        role="assistant",
        source="api_response",
        content="It is sunny today.",
    )

    # Actually create the entries in the database
    await create_entries(
        developer_id=test_developer_id,
        session_id=test_session.id,
        data=[user_entry, assistant_entry],
        connection_pool=pool,
    )

    # Call the mock GET endpoint
    # response = mock_openai_client.responses.get(
    #     response_id=str(test_session.id),  # Convert UUID to string
    # )
    response = make_request(
        method="GET",
        url=f"/responses/{test_session.id}",
    )
    response.raise_for_status()
    data = response.json()

    # Assert that response id matches and basic fields are returned as expected.
    assert data["id"] == str(test_session.id)
    assert data["object"] == "response"
    assert isinstance(data["created_at"], int)
    assert data["status"] == "completed"
    assert data["error"] is None
    assert data["incomplete_details"] is None
    assert data["instructions"] is None
    assert data["max_output_tokens"] is None
    assert data["model"] == "gpt-4o-mini"

    # Only the assistant's message should be returned (last_entries determined by the endpoint logic).
    assert "output" in data
    assert len(data["output"]) == 1
    out_msg = data["output"][0]
    assert out_msg["type"] == "message"
    assert out_msg["role"] == "assistant"
    assert isinstance(out_msg["content"], list)
    # The assistant's message content should be the last entry's content.
    assert out_msg["content"][0]["text"] == "It is sunny today."

    # Verify additional response fields.
    assert data["parallel_tool_calls"] is True
    assert data["previous_response_id"] is None
    assert data["store"] is True
    assert data["temperature"] == 1.0
    assert data["top_p"] == 1.0
    assert data["truncation"] == "disabled"

    # Check usage tokens.
    assert "usage" in data
    usage = data["usage"]
    assert usage["input_tokens"] == 0
    assert usage["output_tokens"] == 12
    assert usage["total_tokens"] == 12
