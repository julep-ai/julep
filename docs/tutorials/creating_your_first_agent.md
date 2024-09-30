# Creating Your First Agent

This tutorial will guide you through the process of creating your first agent using the Julep API.

## Step 1: Prepare the Agent Data

Decide on the basic properties of your agent:

```json
{
  "name": "MyFirstAgent",
  "about": "A helpful assistant for general tasks",
  "model": "gpt-4-turbo",
  "instructions": ["Be helpful", "Be concise"]
}
```

## Step 2: Create the Agent

Use the following curl command to create your agent:

```bash
curl -X POST "https://api.julep.ai/api/agents" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "MyFirstAgent",
           "about": "A helpful assistant for general tasks",
           "model": "gpt-4-turbo",
           "instructions": ["Be helpful", "Be concise"]
         }'
```

## Step 3: Verify the Agent Creation

Check if your agent was created successfully:

```bash
curl -X GET "https://api.julep.ai/api/agents" \
     -H "Authorization: Bearer $JULEP_API_KEY"
```

You should see your newly created agent in the list.

## Next Steps

- Learn how to [manage sessions](./managing_sessions.md) with your new agent.
- Explore [integrating tools](./integrating_tools.md) to enhance your agent's capabilities.