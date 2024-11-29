# Customizing Tasks

This guide covers how to define and customize tasks for agents in Julep.

## Creating a Basic Task

Here's an example of creating a simple daily motivation task:

```bash
curl -X POST "https://dev.julep.ai/api/agents/YOUR_AGENT_ID/tasks" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Daily Motivation",
           "description": "Provides daily motivation based on user preferences",
           "input_schema": {
             "type": "object",
             "properties": {
               "about_user": {"type": "string"},
               "topics": {"type": "array", "items": {"type": "string"}},
               "user_email": {"type": "string", "format": "email"}
             },
             "required": ["about_user", "topics", "user_email"]
           },
           "main": [
             {
               "evaluate": {
                 "chosen_topic": "_[\"topics\"][randint(len(_[\"topics\"]))]"
               }
             },
             {
               "prompt": "You are a motivational coach and you are coaching someone who is {{inputs[0][\"about_user\"]}}. Think of the challenges they might be facing on the {{_[\"chosen_topic\"]}} topic and what to do about them. Write down your answer as a bulleted list."
             },
             {
               "prompt": "Write a short motivational poem about {{_[\"choices\"][0].content}}"
             },
             {
               "tool": {
                 "name": "send_email",
                 "arguments": {
                   "subject": "\"Daily Motivation\"",
                   "content": "_[\"choices\"][0].content",
                   "recipient": "inputs[\"user_email\"]"
                 }
               }
             },
             {
               "sleep": 86400
             },
             {
               "workflow": "main",
               "arguments": "inputs[0]"
             }
           ]
         }'
```

## Adding Conditional Logic

You can add conditional logic to your tasks using the `if-else` step:

```json
{
  "if": "inputs['user_mood'] == 'positive'",
  "then": {
    "prompt": "Great! Let's build on that positive energy. {{inputs['chosen_topic']}}"
  },
  "else": {
    "prompt": "I understand you're feeling down. Let's work on improving your mood through {{inputs['chosen_topic']}}."
  }
}
```

## Using Parallel Processing

For tasks that can benefit from parallel processing, use the `parallel` step:

```json
{
  "parallel": [
    {
      "prompt": "Generate a motivational quote about {{inputs['chosen_topic']}}."
    },
    {
      "tool": {
        "name": "get_weather",
        "arguments": {
          "location": "inputs['user_location']"
        }
      }
    }
  ]
}
```

## Next Steps

- Learn about [handling executions](./handling_executions.md) to manage and monitor your tasks.
- Explore [integrating tools](../tutorials/integrating_tools.md) to enhance your task capabilities.
