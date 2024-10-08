---
description: A fundamental building block of an AI app built using Julep.
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# 🤖 Agents

## What is an Agent?

Agents are conceptual entities that encapsulate all the configurations and settings of an LLM, enabling it to adopt unique personas and execute distinct tasks within an application.

### Attributes

| Attribute                 | Description                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Name                      | The agent's name                                                                                                       |
| About _(optional)_        | A description for the agent                                                                                            |
| Instructions _(optional)_ | A list of instructions for the agent to follow. Defaults to an empty list.                                             |
| Tools _(optional)_        | Set of functions that the agent can use to perform tasks. Defaults to an empty list.                                   |
| Model Name _(optional)_   | Represents the LLM that will run the agent.                                                                            |
| Settings _(optional)_     | Settings to control the LLM, like temperature, `top_p`, max tokens                                                     |
| Documents _(optional)_    | Important documents in text format scoped to and used by the agent. Helpful to enhance the persona given to the agent. |
| Metadata _(optional)_     | Extra information to either identify or refer to the agent in the application apart from its ID.                       |

## Creating an Agent

Here's a conceptual example of creating an agent with all the attributes

{% code lineNumbers="true" fullWidth="false" %}
```python
agent = client.agents.create(
    name="Ellipsis",
    about="Ellipsis is an AI powered code reviewer. It can review code, provide feedback, suggest improvements, and answer questions about code.",
    instructions=[
        "On every pull request, Review the changes made in the code. Summarize the changes made in the PR and add a comment",
        "Scrutinize the changes very deeply for potential bugs, errors, security vulnerabilities. Assume the worst case scenario and explain your reasoning for the same.",
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "github_comment",
                "description": "Posts a comment made on a GitHub Pull Request after every new commit. The tool will return a boolean value to indicate if the comment was successfully posted or not.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "comment": {
                            "type": "string",
                            "description": "The comment to be posted on the PR. It should be a summary of the changes made in the PR and the feedback on the same.",
                        },
                        "pr_number": {
                            "type": "number",
                            "description": "The PR number on which the comment is to be posted.",
                        },
                    },
                    "required": ["comment", "pr_number"],
                },
            },
        }
    ],
    model="gpt-4",
    default_settings={
        "temperature": 0.7,
        "top_p": 1,
        "min_p": 0.01,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "length_penalty": 1.0,
    },
    docs=[{"title": "API Reference", "content": "...", "metadata": {"page": 1}}],
    metadata={"db_uuid": "1234"}
)
```
{% endcode %}

### Tools Format

Here's a sample format of a "tool".

```bash
"tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g. San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"]
            }
          },
          "required": ["location"]
        }
      }
    }
  ],

```



## Retrieving an Agent

An agent can be referenced or returned using its Agent ID or Metadata Filters.

#### Using an Agent ID

```python
agent_id = "9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b"
client.agents.get(agent_id).json()
```

You should receive a response that resembles the following spec:

```json
{
  "name": "Ellipsis",
  "about": "Ellipsis is an AI powered code reviewer. It can review code, provide feedback, suggest improvements, and answer questions about code.",
  "created_at": "2024-04-29T05:45:30.091656Z",
  "updated_at": "2024-04-29T05:45:30.091657Z",
  "id": "9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b",
  "default_settings": {
    "frequency_penalty": 0,
    "length_penalty": 1,
    "presence_penalty": 0,
    "repetition_penalty": 1,
    "temperature": 0.7,
    "top_p": 1,
    "min_p": 0.01,
    "preset": null
  },
  "model": "gpt-4",
  "metadata": {"db_uuid": "1234"},
  "instructions": [
    "On every pull request, Review the changes made in the code. Summarize the changes made in the PR and add a comment",
    "Scrutinize the changes very deeply for potential bugs, errors, security vulnerabilities. Assume the worst case scenario and explain your reasoning for the same."
  ]
}
```

#### Using Metadata Filters

```python
client.agents.list(metadata_filter={"db_uuid": "1234"})
```

This returns a list of all the agents with the specific metadata filter.

{% code overflow="wrap" %}
```python
[Agent(name='Ellipsis', about='Ellipsis is an AI-powered code reviewer. It can review code, provide feedback, suggest improvements, and answer questions about code.', created_at=datetime.datetime(2024, 4, 29, 5, 45, 30, 91656, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 4, 29, 5, 45, 30, 91657, tzinfo=datetime.timezone.utc), id='9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b', default_settings=None, model='gpt-4', metadata=AgentMetadata(), instructions=['On every pull request, Review the changes made in the code. Summarize the changes made in the PR and add a comment', 'Scrutinize the changes very deeply for potential bugs, errors, and security vulnerabilities. Assume the worst-case scenario and explain your reasoning for the same.'])]

```
{% endcode %}



## Updating an Agent

An agent can be updated using its Agent ID. You can update any of its parameters. Updating tools and instructions will overwrite the previous ones.

```python
agent_id = "9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b"
client.agents.update(agent_id=agent_id, model="gpt-3.5-turbo")
```
