# Use Julep with Composio

Composio enables agents to execute tasks that require the interaction of agents with the world outside via APIs, RPCs, Shells, Filemanagers, and Browser.

It also natively integrates with Julep, reducing the complexity of writing your own integrations!

## Install & Set up Composio

```bash
## Set up Composio
pip install julep composio_julep
```

&#x20;Log in to Composio & Authenticate with GitHub

```bash
composio login
composio add github
```

## Preview

```python
import os
from julep import Client
from dotenv import load_dotenv
import json
from composio_julep import Action, ComposioToolSet

load_dotenv()

api_key = os.environ["JULEP_API_KEY"]
base_url = os.environ["JULEP_API_URL"]

client = Client(api_key=api_key, base_url=base_url)

toolset = ComposioToolSet()
composio_tools = toolset.get_actions(
    actions=[Action.GITHUB_ACTIVITY_STAR_REPO_FOR_AUTHENTICATED_USER]
)

agent = client.agents.create(
    name="Julius",
    about="GitHub Copilot Personified",
    model="gpt-4o",
    tools=composio_tools,
)
session = client.sessions.create(
    agent_id=agent.id,
    situation="You are a GitHub Copilot Agent. Follow instructions as specified. Use GitHub tools when needed.",
)
user_msg = "Hey. Can you star all julep-ai/julep and SamparkAI/composio for me?"
response = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": user_msg,
        }
    ],
    recall=True,
    remember=True,
)
output = toolset.handle_tool_calls(client, session.id, response)
```

## Initialise Julep & Composio

```python
import os
from julep import Client
from dotenv import load_dotenv
import json
from composio_julep import Action, ComposioToolSet
​
load_dotenv()
​
api_key = os.environ["JULEP_API_KEY"]
base_url = os.environ["JULEP_API_URL"]
​
client = Client(api_key=api_key, base_url=base_url)
​toolset = ComposioToolSet()
composio_tools = toolset.get_actions(
    actions=[Action.GITHUB_ACTIVITY_STAR_REPO_FOR_AUTHENTICATED_USER]
)
```

Read the Composio Docs to see how to filter tools and apps: [https://docs.composio.dev/framework/julep#use-specific-actions](https://docs.composio.dev/framework/julep#use-specific-actions)

## Setup and Invoke an Agent

Here, we create an agent and pass `composio_tools` instead of writing our tool spec.

```python
agent = client.agents.create(
    name="Julius",
    about="GitHub Copilot Personified",
    model="gpt-4o",
    tools=composio_tools,
)
session = client.sessions.create(
    agent_id=agent.id,
    situation="You are a GitHub Copilot Agent. Follow instructions as specified. Use GitHub tools when needed.",
)
user_msg = "Hey. Can you star all julep-ai/julep and SamparkAI/composio for me?"
response = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": user_msg,
        }
    ],
    recall=True,
    remember=True,
)
```

## Handle a Tool Call

Composio offers a nifty `handle_tool_calls` function which calls your authenticated tools if that's what the agent has returned.

If not, it just returns the `ChatResponse`

```python
output = toolset.handle_tool_calls(client, session.id, response)
print(output.response[0][0].content)
```
