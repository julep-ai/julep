# Using Chat Features

This guide covers how to use the chat features in Julep for dynamic interactions with agents.

## Starting a Chat Session

To start a new chat session:

```bash
curl -X POST "https://dev.julep.ai/api/sessions" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "agent_id": "YOUR_AGENT_ID",
           "user_id": "YOUR_USER_ID"
         }'
```

## Sending a Message

To send a message in a chat session:

```bash
curl -X POST "https://dev.julep.ai/api/sessions/YOUR_SESSION_ID/chat" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "messages": [
             {
               "role": "user",
               "content": "Hello, can you help me with a task?"
             }
           ],
           "stream": false,
           "max_tokens": 150
         }'
```

## Streaming Responses

To stream the agent's response:

```bash
curl -N -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "messages": [
             {
               "role": "user",
               "content": "Tell me a story about a brave knight."
             }
           ],
           "stream": true
         }' \
     "https://dev.julep.ai/api/sessions/YOUR_SESSION_ID/chat"
```

## Using Tools in Chat

To use a tool during a chat session:

```bash
curl -X POST "https://dev.julep.ai/api/sessions/YOUR_SESSION_ID/chat" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "messages": [
             {
               "role": "user",
               "content": "Send an email to john@example.com about our meeting tomorrow."
             }
           ],
           "tools": [
             {
               "type": "function",
               "function": {
                 "name": "send_email",
                 "description": "Send an email to a recipient",
                 "parameters": {
                   "type": "object",
                   "properties": {
                     "to": {"type": "string"},
                     "subject": {"type": "string"},
                     "body": {"type": "string"}
                   },
                   "required": ["to", "subject", "body"]
                 }
               }
             }
           ]
         }'
```

## Next Steps

- Explore [customizing tasks](./customizing_tasks.md) to create more complex interactions.
- Learn about [handling executions](./handling_executions.md) for long-running processes.
