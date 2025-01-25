---
title: 'Tools'
description: 'Understanding tools in Julep'
icon: 'screwdriver-wrench'
---

## Overview

Agents can be given access to a number of "tools" -- any programmatic interface that a foundation model can "call" with a set of inputs to achieve a goal. For example, it might use a `web_search(query)` tool to search the Internet for some information.

Unlike agent frameworks, julep is a _backend_ that manages agent execution. Clients can interact with agents using our SDKs. julep takes care of executing tasks and running integrations.

## Components

Tools in Julep consist of three main components:

1. **Name**: A unique identifier for the tool.
2. **Type**: The category of the tool. In Julep, there are four types of tools:
   - **User-defined `functions`**: Function signatures provided to the model, similar to OpenAI's function-calling. These require client handling, and the workflow pauses until the client executes the function and returns the results to Julep. [Learn more](#user-defined-functions)
   - **`system` tools**: Built-in tools for calling Julep APIs, such as triggering task execution or appending to a metadata field. [Learn more](#system-tools)
   - **`integrations`**: Built-in third-party tools that enhance the capabilities of your agents. [Learn more](#integration-tools)
   - **`api_calls`**: Direct API calls executed during workflow processes as tool calls. [Learn more](#api-call-tools)
3. **Arguments**: The inputs required by the tool.

#### User-defined `functions`

These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. An example:

```yaml YAML
name: Example system tool task
description: List agents using system call

tools:
  - name: send_notification
    description: Send a notification to the user
    type: function
    function:
      parameters:
        type: object
        properties:
          text:
            type: string
            description: Content of the notification

main:
  - tool: send_notification
    arguments:
      content: '"hi"' # <-- python expression
```

<Note>
Whenever julep encounters a user-defined function, it pauses, giving control back to the client and waits for the client to run the function call and give the results back to julep.
</Note>

#### `System` Tools

Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.

`System` tools are built into the backend. They get executed automatically when needed. They do not require any action from the client-side. For example,

```yaml YAML
name: Example system tool task
description: List agents using system call

tools:
  - name: list_agent_docs
    description: List all docs for the given agent
    type: system
    system:
      resource: agent
      subresource: doc
      operation: list

main:
  - tool: list_agents
    arguments:
      limit: 10 # <-- python expression
```

<Accordion title="Available system resources and operations">
  <Accordion title="Agent">
    <ul>
      <li><strong>list</strong>: List all agents.</li>
      <li><strong>get</strong>: Get a single agent by id.</li>
      <li><strong>create</strong>: Create a new agent.</li>
      <li><strong>update</strong>: Update an existing agent.</li>
      <li><strong>delete</strong>: Delete an existing agent.</li>
    </ul>
  </Accordion>
  <Accordion title="User">
    <ul>
      <li><strong>list</strong>: List all users.</li>
      <li><strong>get</strong>: Get a single user by id.</li>
      <li><strong>create</strong>: Create a new user.</li>
      <li><strong>update</strong>: Update an existing user.</li>
      <li><strong>delete</strong>: Delete an existing user.</li>
    </ul>
  </Accordion>
  <Accordion title="Session">
    <ul>
      <li><strong>list</strong>: List all sessions.</li>
      <li><strong>get</strong>: Get a single session by id.</li>
      <li><strong>create</strong>: Create a new session.</li>
      <li><strong>update</strong>: Update an existing session.</li>
      <li><strong>delete</strong>: Delete an existing session.</li>
      <li><strong>chat</strong>: Chat with a session.</li>
      <li><strong>history</strong>: Get the chat history with a session.</li>
    </ul>
  </Accordion>
  <Accordion title="Task">
    <ul>
      <li><strong>list</strong>: List all tasks.</li>
      <li><strong>get</strong>: Get a single task by id.</li>
      <li><strong>create</strong>: Create a new task.</li>
      <li><strong>update</strong>: Update an existing task.</li>
      <li><strong>delete</strong>: Delete an existing task.</li>
    </ul>
  </Accordion>
  <Accordion title="Doc (subresource for agent and user)">
    <ul>
      <li><strong>list</strong>: List all documents.</li>
      <li><strong>create</strong>: Create a new document.</li>
      <li><strong>delete</strong>: Delete an existing document.</li>
      <li><strong>search</strong>: Search for documents.</li>
    </ul>
  </Accordion>
  <Accordion title="Additional Operations">
    <ul>
      <li><strong>embed</strong>: Embed a resource (specific resources not specified in the provided code).</li>
      <li><strong>change_status</strong>: Change the status of a resource (specific resources not specified in the provided code).</li>
      <li><strong>chat</strong>: Chat with a resource (specific resources not specified in the provided code).</li>
      <li><strong>history</strong>: Get the chat history with a resource (specific resources not specified in the provided code).</li>
      <li><strong>create_or_update</strong>: Create a new resource or update an existing one (specific resources not specified in the provided code).</li>
    </ul>
  </Accordion>
</Accordion>

#### `Integration` Tools

Julep comes with a number of built-in integrations (as described in the section below). `integration` tools are directly executed on the julep backend. Any additional parameters needed by them at runtime can be set in the agent/session/user's `metadata` fields.

An example of how to create a `integration` tool for an agent using the `wikipedia` integration:

```yaml YAML
name: Example integration tool task
description: Search wikipedia for a query

tools:
  - name: wikipedia_search
    description: Search wikipedia for a query
    type: integration
    integration:
      provider: wikipedia

main:
  - tool: wikipedia_search
    arguments:
      query: "'Julep'"
```

<Info>
Checkout the list of integrations that Julep supports [here](/docs/integrations).
</Info>

#### `API Call` Tools

Julep can also directly make api calls during workflow executions as tool calls. Same as `integration`s, additional runtime parameters are loaded from metadata fields. For example,

```yaml YAML
name: Example api_call task
tools:
  - type: api_call
    name: hello
    api_call:
      method: GET
      url: https://httpbin.org/get

main:
  - tool: hello
    arguments:
      json:
        test: _.input # <-- python expression
```

## How to Use Tools

### Create a Tool for an Agent

A tool can be created for an agent using the `client.agents.tools.create` method.

An example of how to create a `integration` tool for an agent using the `wikipedia` integration:

<CodeGroup>
```python Python
# Create an agent
agent = client.agents.create(name="My Agent")

# Associate a tool with the agent
client.agents.tools.create(
        agent_id=AGENT_UUID,
        **{
            "name": "wikipedia_search",
            "type": "integration",
            "integration": {
              "provider": "wikipedia",
            } 
          },
    )
```
```javascript Node.js
async function createAgent() {
  const agent = await client.agents.create({
    name: "My Agent",
  });

  const tool = await client.agents.tools.create(agent.id, {
    name: "wikipedia_search",
    type: "integration",
    integration: {
      provider: "wikipedia",
    },
  });
  return agent;
}
```
</CodeGroup>

<Tip>
    Check out the API reference [here](api-reference/agents/tools/create) or SDK reference (Python [here](/sdks/python/reference#Tools) or JavaScript [here](/sdks/nodejs/reference#Tools) for more details on different operations you can perform on agents.
</Tip>

### Execute a Tool for a Task

To create a tool for a task, you can use the `client.tasks.create` method and define the tool in that `task` definitions.

<CodeGroup>
  ```yaml YAML
name: Example integration tool task
description: Search wikipedia for a query

tools:
  - name: wikipedia_search
    description: Search wikipedia for a query
    type: integration
    integration:
      provider: wikipedia
main:
  - tool: wikipedia_search
    arguments:
      query: "'Julep'"
  ```

  ```python Python
  # Create a task
  import yaml
  task_yaml = """
  // ... task yaml here ...
  """
  task_def = yaml.safe_load(task_yaml)
  task = client.tasks.create(
      agent_id="agent_id",
      **task_def
  )

  execution = client.executions.create(
    task_id=task.id,
    input={
        "document_text": "This is a sample document"
    }
  )
  ```

  ```javascript Node.js
  // Create a task
  const taskYaml = `
  // ... task yaml here ...
  `
  async function createTask(agentId) {
    const task = await client.tasks.create(agentId, yaml.parse(taskYaml));
    return task;
  }
  // Execute a task
  async function executeTask(taskId) {
    const execution = await client.executions.create(taskId, {
      input: {
        document_text: "This is a sample document"
      }
    });
    return execution;
  }
  ``` 
</CodeGroup>
<Tip>
    Check out the API reference [here](api-reference/agents/tools/create) or SDK reference (Python [here](/sdks/python/reference#Tools) or JavaScript [here](/sdks/nodejs/reference#Tools) for more details on different operations you can perform on agents.
</Tip>

## Relationship to Other Concepts

This section will help you understand how tools relate to other concepts in Julep.

### Task

When a tool is associated with a task, it is meant to be used only for that task. It is not associated with other tasks. An agent associated with that task will have access to that tool, but the same agent associated with another task will not have that access. This ensures that tools are used in a context-specific manner, providing precise functionality tailored to the task's requirements.

### Agent

When a tool is associated with an agent, it is meant to be used across all tasks associated with that agent. This allows for greater flexibility and reuse of tools, as the agent can leverage the same tool in multiple tasks. It also simplifies the management of tools, as they only need to be defined once for the agent and can then be utilized in various tasks.

## Best Practices

<CardGroup cols={3}>
    <Card title="Consistent Naming" icon="tag">
        <ul>
            <li>**1. Naming Conventions**: Use clear and consistent naming conventions for tools to make them easily identifiable and understandable.</li>
        </ul>
    </Card>
    <Card title="Correct Usage" icon="check-double">
        <ul>
            <li>**1. Correct Usage**: Ensure that tools are used correctly and in the appropriate context. This includes providing the necessary arguments and ensuring that the tools are executed as intended.</li>
        </ul>
    </Card>
    <Card title="Type" icon="font">
        <ul>
            <li>**1. Type**: Ensure that the type is correct for the tool you are using. Checkout the Tool Types Definitions <a href="/docs/concepts/tools#tool-types-definitions">here</a> for further details.</li>
        </ul>
    </Card>
</CardGroup>

## Next Steps

- [Checkout the Integration](/docs/integrations) - Learn how to use executions in an integration
- [Checkout the Tutorial](/docs/tutorials/tool-usage) - Learn how to use tools in a task