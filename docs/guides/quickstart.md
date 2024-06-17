---
description: >-
  Creating a Search Agent using GPT-4o that calls a Search & Read Post API and
  sets the appropriate filters and values.
---

# (Quickstart) Build a Basic Agent

## Getting Setup

### Option 1: Install and run Julep locally

Read the[self-hosting.md](self-hosting.md "mention") guide to learn more.

### Option 2: Use the Julep Cloud

* Generate an API key from [https://platform.julep.ai](https://platform.julep.ai)
* Set your environment variables

```bash
export JULEP_API_KEY=<your_julep_api_key>
export JULEP_API_URL=https://api-alpha.julep.ai/api
```

## 1. Installation

```bash
pip install -U julep
```

## 2. Setting up the `client`

```py
from julep import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ["JULEP_API_KEY"]
base_url = os.environ["JULEP_API_URL"]

client = Client(api_key=api_key, base_url=base_url)
```

## 3. Creating an `agent`

### **Instructions**

Instructions are added to an agent. These should be as clear, distinct, and direct as possible. Instructions should be defined step-by-step.

> We recommended to write the instructions in the same tone as system prompt.

```python
INSTRUCTIONS = [
    "The user will inform you about the product they want to focus on. They will choose from the following: Assistants API, GPT series of models, Dall-E, ChatGPT, Sora",
    "You WILL ask and decide the product to focus on if it is not clear. You will NOT proceed if the product is unclear."
    "You will then, ask the user about what type of information and feedback they need from the forum.",
    "You will generate 5 very specific search queries based on what the user wants.",
    "The user will then provide you with the queries they like. If not, help them refine it.",
    "ONLY WHEN the search query has been decided, search through the forum using the search_forum function. This will provide you with the Post IDs and Blurbs. You will read through them and tell the user in brief about the posts using the blurbs.",
    "MAKE SURE to use and refer to posts using the `post_id`",
    "The user will provide and choose the post they want more information on. You will then call the `read_post` function and pass the `post_id`.",
]
```

### **Tools**

OpenAI specification of tools. \
_Descriptions are crucial, more so than examples_.

Your descriptions should explain every detail about the tool, including:

* What the tool does
* When it should be used (and when it shouldn’t)
* What does each parameter mean and how it affect the tool’s behavior
* Any important caveats or limitations, such as what information the tool does not return if the tool name is unclear
* The more context you can give about your tools, the better the model will be at deciding when and how to use them. Aim for at least 3-4 sentences per tool description, more if the tool is complex.

```python
def search_forum(
    query: str,
    order: Literal["latest", "likes", "views", "latest_topic"],
    max_views: int = 10000,
    min_views: int = 500,
    category: str = None,
):
    # Define your function here!
    pass

def read_post(post_id: int):
    # Define your function here!
    pass

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_forum",
            "description": "Retrieves a list of posts from a forum for the given search parameters. The search parameters should include the search query and additional parameters such as: category, order, minimum views, and maximum views. The tool will return a list of posts based on the search query and additional parameters. It should be used when the user asks to start monitoring the forum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to be used to search for posts in the forum.",
                    },
                    "order": {
                        "type": "string",
                        "description": "The order in which the posts should be sorted. Possible values are: latest, likes, views, latest_topic.",
                    },
                    "min_views": {
                        "type": "number",
                        "description": "The minimum number of views a post should have to be included in the search results.",
                    },
                    "max_views": {
                        "type": "number",
                        "description": "The maximum number of views a post should have to be included in the search results.",
                    },
                },
                "required": ["query", "order", "min_views", "max_views", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_post",
            "description": "Retrieves the details of a specific post from the forum. The tool should take the post ID as input and return the details of the post including the content, author, date, and other relevant information. It should be used when the user asks to read a specific post.",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "number",
                        "description": "The ID of the post to be read.",
                    },
                },
                "required": ["post_id"],
            },
        },
    },
]
```

### **Agent**

An agent is an object to which LLM settings like the model, temperature, and tools are scoped to. Following is how you can define an agent.

> Pro tip: Always add some metadata. It'll be helpful later!

```py
agent = client.agents.create(
    name="Archy",
    about="An agent that posts and comments on Discourse forums by filtering for the provided topic",
    tools=TOOLS,
    instructions=INSTRUCTIONS,
    model="gpt-4o",
    default_settings={
        "temperature": 0.5,
        "top_p": 1,
        "min_p": 0.01,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "length_penalty": 1.0,
    },
    metadata={"name": "Archy"},
)
```

## 4. Creating a `user`

The user is the object which represents the user of the application. Memories are formed and saved for each user and many users can talk to one agent.

```py
user = client.users.create(
    name="Anon",
    about="A product manager at OpenAI, working with Archy to validate and improve the product",
    metadata={"name": "Anon"},
)
```

## 5. Creating a `session`

An _agent_ is communicated over a _session_. Optionally, a _user_ can be added.

The system prompt goes here. Conversation history and summary are stored in a "session".

The session paradigm allows many users to interact with one agent and allows the separation of conversation history and memories.&#x20;

### Situation

A situation prompt is defined in a session. It sets the stage for the interaction with the agent. It needs to give a personality to the agent along with providing more context about the ongoing interaction.

```python
SITUATION_PROMPT = """
You are Archy, a senior community manager at OpenAI.
You read through discussions and posts made on the OpenAI Community Forum.
You are extremely specific about the issues you look for and seek to understand all the parameters when searching for posts.
After that, you read the specific posts and discussions and make a summary of the trends, sentiments related to OpenAI and how people are using OpenAI products.

Here, you are helping the product manager at OpenAI to get feedback and understand OpenAI products.
Follow the instructions strictly.
"""
```

```py
session = client.sessions.create(
    user_id=user.id,
    agent_id=agent.id,
    situation=SITUATION_PROMPT,
    metadata={"agent_id": agent.id, "user_id": user.id},
)
```

## 6. Stateful Conversation with Tool Calls

`session.chat` controls the communication between the "agent" and the "user".

It has two important arguments;

* `recall`: Retrieves the previous conversations and memories.
* `remember`: Saves the current conversation turn into the memory store.

To keep the session stateful, both need to be `True`

```python
user_msg = (
    "i wanna search for assistants api. api errors in it"
)
```

```py
response = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": user_msg,
            "name": "Anon",
        }
    ],
    recall=True,
    remember=True,
)
```

### **Parsing and calling the function**

On parsing the response it is possible to view the tool call (if the LLM calls it) and call the function you defined.

```python
agent_response = response.response[0][0]
elif agent_response.role.value == "tool_call":
    tool_call = json.loads(agent_response.content)
    args = json.loads(
        tool_call.get("arguments", "{}")
    )  # Parse the JSON string into a dictionary
    tool = tool_call.get("name", "")
    if tool == "search_forum":
        posts = await search_forum(**args)
        tool_response = client.sessions.chat(
            session_id=session_id,
            messages=[{"role": "function", "name": "search_forum", "content": json.dumps(posts)}],
            recall=True,
                remember=True,
        )
    elif tool == "read_post":
        post = await read_post(**args)
        tool_response = client.sessions.chat(
            session_id=session_id,
            messages=[{"role": "function", "name": "read_post", "content": json.dumps(posts)}],
            recall=True,
            remember=True
        )
```
