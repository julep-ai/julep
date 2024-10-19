# Chat Features in Julep

Julep provides a robust chat system with various features for dynamic interaction with agents. Here's an overview of the key components and functionalities:

## Chat Input

When sending a request to the chat endpoint, you can include:

1. **Messages**: An array of input messages representing the conversation so far.
2. **Tools**: (Advanced) Additional tools provided for this specific interaction.
3. **Tool Choice**: Specifies which tool the agent should use.
4. **Memory Access Options**: Controls how the session accesses history and memories.
5. **Chat Settings**: Various settings to control the behavior of the chat.

## Chat Settings

Chat settings allow fine-grained control over the generation process:

- `model`: Identifier of the model to be used.
- `stream`: Indicates if the server should stream the response as it's generated.
- `stop`: Up to 4 sequences where the API will stop generating further tokens.
- `seed`: For deterministic sampling.
- `max_tokens`: The maximum number of tokens to generate.
- `logit_bias`: Modify the likelihood of specified tokens appearing in the completion.
- `response_format`: Control the format of the response (e.g., JSON object).
- `agent`: Agent ID to use (for multi-agent sessions).

Additional settings include `temperature`, `top_p`, `frequency_penalty`, and `presence_penalty`.

## Chat Response

The chat response can be either streamed or returned as a complete message:

1. **Streamed Response**: 
   - Content-Type: `text/event-stream`
   - Body: A stream of `ChatOutputChunk` objects.

2. **Complete Response**:
   - Content-Type: `application/json`
   - Body: A `MessageChatResponse` object containing the full generated message(s).

Both response types include:
- `usage`: Token usage statistics.
- `jobs`: Background job IDs spawned from this interaction.
- `docs`: Documents referenced for this request (for citation purposes).

## Finish Reasons

The API provides information about why the model stopped generating tokens:

- `stop`: Natural stop point or provided stop sequence reached.
- `length`: Maximum number of tokens specified in the request was reached.
- `content_filter`: Content was omitted due to a flag from content filters.
- `tool_calls`: The model called a tool.

## Advanced Features

1. **Tool Integration**: The chat API allows for the use of tools, enabling the agent to perform actions or retrieve information during the conversation.

2. **Multi-agent Sessions**: You can specify different agents within the same session using the `agent` parameter in the chat settings.

3. **Response Formatting**: Control the output format, including options for JSON responses with specific schemas.

4. **Memory and Recall**: Configure how the session accesses and stores conversation history and memories.

5. **Document References**: The API returns information about documents referenced during the interaction, useful for providing citations or sources.

These features provide developers with a powerful and flexible system for creating sophisticated, context-aware chat interactions that integrate seamlessly with other Julep components.