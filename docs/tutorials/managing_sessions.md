# Managing Sessions

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


This tutorial will guide you through creating and managing sessions with your Julep agents.

## Creating a Session

To create a new session with an agent:

```bash
curl -X POST "https://api.julep.ai/api/sessions" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "agent_id": "YOUR_AGENT_ID",
           "user_id": "YOUR_USER_ID",
           "situation": "Custom situation for this session"
         }'
```

## Interacting with a Session

To send a message in a session:

```bash
curl -X POST "https://api.julep.ai/api/sessions/YOUR_SESSION_ID/messages" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "role": "user",
           "content": "Hello, how can you help me today?"
         }'
```

## Managing Context Overflow

If you're dealing with long conversations, you may need to handle context overflow:

```bash
curl -X PUT "https://api.julep.ai/api/sessions/YOUR_SESSION_ID" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "token_budget": 4000,
           "context_overflow": "truncate"
         }'
```

## Next Steps

- Learn about [integrating tools](./integrating_tools.md) to enhance your sessions.
- Explore [customizing tasks](../how-to-guides/customizing_tasks.md) for more complex interactions.