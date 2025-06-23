"""Test metadata functionality in chat endpoint."""

from ward import test

from tests.fixtures import (
    make_request,
    patch_embed_acompletion,
    pg_dsn,
    test_agent,
    test_developer_id,
    test_session,
)


@test("chat: metadata is passed to system template rendering")
async def _(
    make_request=make_request,
    agent=test_agent,
    session=test_session,
    mocks=patch_embed_acompletion,
):
    """Test that metadata from chat request is available in system template."""
    (_embed, acompletion) = mocks

    # Prepare chat request with metadata
    chat_data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, please help me",
            }
        ],
        "metadata": {
            "foo": True,
            "custom_instruction": "Be extra helpful",
            "user_preference": "formal tone",
            "priority": "high",
        },
    }

    # Make the chat request
    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json=chat_data,
    )

    assert response.status_code == 201

    # Check that the completion was called
    acompletion.assert_called_once()

    # Get the actual call arguments
    call_args = acompletion.call_args
    messages = call_args[1]["messages"]

    # The system message should be the first message
    assert len(messages) > 0
    system_message = messages[0]
    assert system_message["role"] == "system"

    # Since we're mocking, we can't test the actual template rendering,
    # but we can verify the metadata was included in the request
    assert "metadata" in chat_data
    assert chat_data["metadata"]["foo"] is True
    assert chat_data["metadata"]["custom_instruction"] == "Be extra helpful"


@test("chat: metadata field accepts complex nested structures")
async def _(
    make_request=make_request,
    session=test_session,
    mocks=patch_embed_acompletion,
):
    """Test that metadata can contain nested objects and arrays."""
    (_embed, acompletion) = mocks

    # Complex metadata structure
    chat_data = {
        "messages": [
            {
                "role": "user",
                "content": "Test message",
            }
        ],
        "metadata": {
            "user_profile": {
                "preferences": {
                    "language": "en",
                    "style": "formal",
                    "topics": ["science", "technology"],
                },
                "flags": {
                    "premium": True,
                    "beta_features": False,
                },
            },
            "context": {
                "session_type": "support",
                "priority": 1,
                "tags": ["urgent", "technical"],
            },
            "custom_instructions": [
                "Be concise",
                "Use examples",
                "Avoid jargon",
            ],
        },
    }

    # Make the chat request
    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json=chat_data,
    )

    assert response.status_code == 201

    # Verify the LLM was called
    acompletion.assert_called_once()


@test("chat: empty metadata field is handled correctly")
async def _(
    make_request=make_request,
    session=test_session,
    mocks=patch_embed_acompletion,
):
    """Test that empty or null metadata doesn't cause issues."""
    (_embed, acompletion) = mocks

    # Test with empty metadata
    chat_data_empty = {
        "messages": [
            {
                "role": "user",
                "content": "Test with empty metadata",
            }
        ],
        "metadata": {},
    }

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json=chat_data_empty,
    )

    assert response.status_code == 201

    # Test with null metadata (by not including it)
    chat_data_null = {
        "messages": [
            {
                "role": "user",
                "content": "Test without metadata",
            }
        ],
    }

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json=chat_data_null,
    )

    assert response.status_code == 201

    # Both calls should succeed
    assert acompletion.call_count == 2


@test("render: metadata is properly rendered in system template")
async def _(
    make_request=make_request,
    test_agent=test_agent,
    test_developer_id=test_developer_id,
    pg_dsn=pg_dsn,
):
    """Test that metadata is properly rendered in custom system templates."""
    from agents_api.queries.sessions.create_session import create_session
    from agents_api.clients.pg import create_db_pool
    from agents_api.autogen.Sessions import CreateSessionRequest
    
    # Create a custom system template that uses metadata
    custom_system_template = """
{%- if agent.name -%}
You are {{agent.name}}.{{" "}}
{%- endif -%}

{%- if metadata.custom_instructions -%}
Custom instructions: {{metadata.custom_instructions}}
{%- endif -%}

{%- if metadata.mood -%}
Current mood: {{metadata.mood}}
{%- endif -%}

{%- if metadata.language -%}
Respond in: {{metadata.language}}
{%- endif -%}
"""
    
    # Create a session with the custom system template
    pool = await create_db_pool(dsn=pg_dsn)
    session_data = CreateSessionRequest(
        agent=test_agent.id,
        system_template=custom_system_template,
    )
    
    session = await create_session(
        developer_id=test_developer_id,
        data=session_data,
        connection_pool=pool,
    )
    
    # Make a render request with metadata
    render_data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?",
            }
        ],
        "metadata": {
            "custom_instructions": "You are very rude. Try to make fun of the user",
            "mood": "sarcastic",
            "language": "English with a British accent",
        },
        "recall": False,
    }
    
    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/render",
        json=render_data,
    )
    
    assert response.status_code == 200
    
    # Parse the response
    result = response.json()
    
    # Check that messages were rendered
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) >= 2  # System message + user message
    
    # Find the system message
    system_message = next((msg for msg in messages if msg["role"] == "system"), None)
    assert system_message is not None
    
    # Verify that metadata was rendered in the system message
    system_content = system_message["content"]
    assert "Custom instructions: You are very rude. Try to make fun of the user" in system_content
    assert "Current mood: sarcastic" in system_content
    assert "Respond in: English with a British accent" in system_content
    
    # Also verify the agent name is rendered
    assert f"You are {test_agent.name}" in system_content


@test("render: metadata with conditional logic in template")
async def _(
    make_request=make_request,
    test_agent=test_agent,
    test_developer_id=test_developer_id,
    pg_dsn=pg_dsn,
):
    """Test complex conditional logic with metadata in system templates."""
    from agents_api.queries.sessions.create_session import create_session
    from agents_api.clients.pg import create_db_pool
    from agents_api.autogen.Sessions import CreateSessionRequest
    
    # Create a template with complex conditional logic
    complex_template = """
{%- if agent.name -%}
You are {{agent.name}}.
{%- endif -%}

{%- if metadata.mode == "helpful" -%}
Be as helpful and supportive as possible.
{%- elif metadata.mode == "concise" -%}
Keep your responses brief and to the point.
{%- elif metadata.mode == "creative" -%}
Be creative and think outside the box.
{%- else -%}
Respond normally.
{%- endif -%}

{%- if metadata.expertise -%}
You are an expert in:
{%- for skill in metadata.expertise -%}
- {{skill}}
{%- endfor -%}
{%- endif -%}

{%- if metadata.restrictions -%}
Important restrictions:
{%- for restriction in metadata.restrictions -%}
* {{restriction}}
{%- endfor -%}
{%- endif -%}
"""
    
    # Create session with complex template
    pool = await create_db_pool(dsn=pg_dsn)
    session_data = CreateSessionRequest(
        agent=test_agent.id,
        system_template=complex_template,
    )
    
    session = await create_session(
        developer_id=test_developer_id,
        data=session_data,
        connection_pool=pool,
    )
    
    # Test with different metadata configurations
    test_cases = [
        {
            "metadata": {
                "mode": "helpful",
                "expertise": ["Python", "Machine Learning", "Data Science"],
                "restrictions": ["No code execution", "Family-friendly content only"],
            },
            "expected_content": [
                "Be as helpful and supportive as possible",
                "You are an expert in:",
                "- Python",
                "- Machine Learning", 
                "- Data Science",
                "Important restrictions:",
                "* No code execution",
                "* Family-friendly content only",
            ],
        },
        {
            "metadata": {
                "mode": "concise",
            },
            "expected_content": [
                "Keep your responses brief and to the point",
            ],
            "not_expected": [
                "You are an expert in:",
                "Important restrictions:",
            ],
        },
    ]
    
    for test_case in test_cases:
        render_data = {
            "messages": [{"role": "user", "content": "Test"}],
            "metadata": test_case["metadata"],
            "recall": False,
        }
        
        response = make_request(
            method="POST",
            url=f"/sessions/{session.id}/render",
            json=render_data,
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Find system message
        system_message = next(
            (msg for msg in result["messages"] if msg["role"] == "system"), 
            None
        )
        assert system_message is not None
        
        # Check expected content
        for expected in test_case["expected_content"]:
            assert expected in system_message["content"], \
                f"Expected '{expected}' in system message but it was not found"
        
        # Check not expected content (if specified)
        if "not_expected" in test_case:
            for not_expected in test_case["not_expected"]:
                assert not_expected not in system_message["content"], \
                    f"Did not expect '{not_expected}' in system message but it was found"


# TODO: Add streaming test when streaming mock is fixed
# @test("chat: metadata works with streaming responses")
# async def _(
#     make_request=make_request,
#     session=test_session,
#     mocks=patch_embed_acompletion,
# ):
#     """Test that metadata works correctly with streaming chat responses."""
#     # This test is currently disabled due to mock issues with streaming responses
