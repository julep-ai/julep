# Integrating Tools

This tutorial will show you how to integrate tools with your Julep agents.

## Creating a User-Defined Function Tool

Here's how to create a simple tool for sending emails:

```bash
curl -X POST "https://api.julep.ai/api/agents/YOUR_AGENT_ID/tools" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "send_email",
           "type": "function",
           "function": {
             "description": "Send an email to a recipient",
             "parameters": {
               "type": "object",
               "properties": {
                 "to": {
                   "type": "string",
                   "description": "Recipient email address"
                 },
                 "subject": {
                   "type": "string",
                   "description": "Email subject"
                 },
                 "body": {
                   "type": "string",
                   "description": "Email body"
                 }
               },
               "required": ["to", "subject", "body"]
             }
           }
         }'
```

## Using Tools in Sessions

When creating or updating a session, you can specify which tools to use:

```bash
curl -X POST "https://api.julep.ai/api/sessions" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "agent_id": "YOUR_AGENT_ID",
           "user_id": "YOUR_USER_ID",
           "tools": ["send_email"]
         }'
```

## Next Steps

- Learn about [customizing tasks](../how-to-guides/customizing_tasks.md) to create complex workflows using tools.
- Explore [handling executions](../how-to-guides/handling_executions.md) to manage tool usage in tasks.