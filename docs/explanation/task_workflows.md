# Task Workflows in Julep


Tasks in Julep are powerful, Github Actions-style workflows that define long-running, multi-step actions. They allow for complex operations by defining steps and have access to all Julep integrations.

## Task Structure

A Task consists of:

- `name`: The name of the task (required for creation)
- `description`: A description of the task
- `main`: The main workflow steps (required, minimum 1 item)
- `input_schema`: JSON schema to validate input when executing the task
- `tools`: Additional tools specific to this task
- `inherit_tools`: Whether to inherit tools from the parent agent

## Workflow Steps

Tasks can include various types of workflow steps:

1. **Tool Call**: Runs a specified tool with given arguments
2. **Prompt**: Runs a prompt using a model
3. **Evaluate**: Runs Python expressions and uses the result as output
4. **Wait for Input**: Suspends execution and waits for user input
5. **Log**: Logs information during workflow execution
6. **Embed**: Embeds text for semantic operations
7. **Search**: Searches for documents in the agent's doc store
8. **Set**: Sets a value in the workflow's key-value store
9. **Get**: Retrieves a value from the workflow's key-value store
10. **Foreach**: Runs a step for every value from a list in serial order
11. **Map-reduce**: Runs a step for every value of the input list in parallel
12. **Parallel**: Executes multiple steps in parallel
13. **Switch**: Executes different steps based on a condition
14. **If-else**: Conditional step with then and else branches
15. **Sleep**: Pauses the workflow execution for a specified time
16. **Return**: Ends the current workflow and optionally returns a value
17. **Yield**: Switches to another named workflow
18. **Error**: Throws an error and exits the workflow

## Example Task

Here's an example of a daily motivation task:

```yaml
name: Daily Motivation
description: Provides daily motivation based on user preferences
input_schema:
  type: object
  properties:
    about_user:
      type: string
    topics:
      type: array
      items:
        type: string
    user_email:
      type: string
      format: email
  required: ["about_user", "topics", "user_email"]

tools:
- function:
    name: send_email
    description: Sends an email to the user
    parameters:
      type: object
      properties:
        subject:
          type: string
        content:
          type: string
        recipient:
          type: string
      required: ["subject", "content", "recipient"]

main:
- evaluate:
    chosen_topic: _["topics"][randint(len(_["topics"]))]
    
- prompt: You are a motivational coach and you are coaching someone who is {{inputs[0]["about_user"]}}. Think of the challenges they might be facing on the {{_["chosen_topic"]}} topic and what to do about them. Write down your answer as a bulleted list.

- prompt: Write a short motivational poem about {{_["choices"][0].content}}

- tool:
    name: send_email
    arguments:
      subject: '"Daily Motivation"'
      content: _["choices"][0].content
      
- sleep: 24*3600  

- workflow: main  
  arguments: inputs[0]
```

This task demonstrates the power and flexibility of Julep's workflow system, allowing for complex, multi-step processes that can interact with various tools and models to achieve sophisticated outcomes.