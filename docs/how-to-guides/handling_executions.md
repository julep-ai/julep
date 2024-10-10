# Handling Executions

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


This guide covers how to manage and monitor task executions in Julep.

## Starting an Execution

To start a new execution of a task:

```bash
curl -X POST "https://api.julep.ai/api/tasks/YOUR_TASK_ID/executions" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "input": {
             "about_user": "a software developer looking to improve work-life balance",
             "topics": ["time management", "stress reduction", "productivity"],
             "user_email": "user@example.com"
           }
         }'
```

## Monitoring Execution Status

To check the status of an execution:

```bash
curl -X GET "https://api.julep.ai/api/executions/YOUR_EXECUTION_ID" \
     -H "Authorization: Bearer $JULEP_API_KEY"
```

## Handling Awaiting Input State

If an execution is in the "awaiting_input" state, you can resume it with:

```bash
curl -X POST "https://api.julep.ai/api/executions/resume" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "task_token": "YOUR_TASK_TOKEN",
           "input": {
             "user_feedback": "The motivation was helpful, thank you!"
           }
         }'
```

## Cancelling an Execution

To cancel a running execution:

```bash
curl -X PUT "https://api.julep.ai/api/executions/YOUR_EXECUTION_ID" \
     -H "Authorization: Bearer $JULEP_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
           "status": "cancelled"
         }'
```

## Streaming Execution Events

To stream events from an execution in real-time:

```bash
curl -N -H "Authorization: Bearer $JULEP_API_KEY" \
     "https://api.julep.ai/api/executions/YOUR_EXECUTION_ID/transitions/stream"
```

## Next Steps

- Learn about [customizing tasks](./customizing_tasks.md) to create more complex workflows.
- Explore [using chat features](./using_chat_features.md) to interact with agents during task execution.