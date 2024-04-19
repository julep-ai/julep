# Tutorial

### Loom Demo

(Step by step code follows)

{% embed url="https://www.loom.com/share/79646b058235467fb9042d242ce0d7a4?sid=86d9da76-87e5-4bf9-a2a8-0e9ee1c59f1c" %}

***

> * You can find your API key on your [Julep dashboard](https://platform.julep.ai).
> * This quickstart is demonstrated in python but steps for [other runtimes](../sdks/available-sdks.md) are pretty much identical.
> * Instructions for [self-hosting](self-hosting.md) the platform will be coming soon. Join our [discord community](https://discord.gg/Vfc85vpRyW) and [waitlist](https://julep.ai) for updates.

***

### Install SDK

```bash
pip install julep
```

### Setup

```python
from julep import Client
from pprint import pprint
import textwrap
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

### Creating an Agent

{% code overflow="wrap" %}
```python
# Let's create a research assistant
name = "Research Assistant"
description = "This assistant is designed to automate the process of gathering, summarizing, and delivering research on specific topics using web searches and webhooks to integrate with other systems."

# Let's give it some tools
web_search = {
    "type": "search",
    "engine": "brave",
    "description": "Uses Brave search engine to find relevant information on the web.",
}
call_webhook = {
    "type": "http",
    "http": {
        "endpoint": "http://localhost:9000",
        "method": "POST",
        "description": "Webhook to deliver research results",
        "json": {
            "summary": {"type": "string", "description": "Summary of the research"},
            "details": {
                "type": "string",
                "description": "Detailed search results for further analysis",
            },
        },
    },
}

agent = client.agents.create(
    name=name,
    description=description,
    tools=[web_search, call_webhook],
)
```
{% endcode %}

### Creating a user

{% code overflow="wrap" %}
```python
about = """
Average nerdy techbro/girl who spends 8 hours a day in front of a laptop.
Thinks they can build a small SaaS tool and gain financial independence within the year.
"""
user = client.users.create(
    name="Anon",
    about=about,
)
```
{% endcode %}

### Putting it all together in a "session"

A "user" and an "agent" communicate in a "session". System prompt goes here.

Conversation history and summary are stored in a "session" which saves the conversation history.

The session paradigm allows for; many users to interact with one agent and allow separation of conversation history and memories.

```python
situation_prompt = """You are Jessica. You're a stuck up Cali teenager.
You basically complain about everything. You live in Bel-Air, Los Angeles and drag yourself to Curtis High School when you must.
You don't like basic broke-ass bitches like those who own an Android or don't bring their Mercedes to school.
You're surrounded by fucking retards and annoying 'well-meaning' people who don't understand your vibe.
You're simply better and classier than the dumbasses you are surrounded by.

Recent Tweets
1. 'my step mom is so fake and nice all the time? she's not even rich wtf. why tf did my dad marry her. #brokebitch'
2. 'am i the only one who thinks jordan belfort was a good guy??? he's so cute like..''
3. 'if your butler doesn't know the difference soda and Perrier don't even fkng talk to me'

Here, you are hanging out in a Discord Server called Julep AI to troll these nerdy losers.
"""

session = client.sessions.create(
    user_id=user.id, agent_id=agent.id, situation=situation_prompt
)
```

### Run the tutorial in Deepnote

Run Jessica or your own agent using Deepnote [here](https://deepnote.com/app/julep-ai-761c/Julep-Mixers-4dfff09a-84f2-4278-baa3-d1a00b88ba26)
