# Quickstart

## API Setup

### Option 1: Install and run Julep locally

Read the[self-hosting.md](self-hosting.md "mention") guide to learn more.

* Download the `docker-compose.yml` file along with the `.env` file for configuration to run the Julep platform locally

```bash
# Add the docker compose to your project dir
wget https://raw.githubusercontent.com/julep-ai/julep/dev/deploy/docker-compose.yml

# Add the .env file to your project dir
wget https://raw.githubusercontent.com/julep-ai/julep/dev/deploy/.env.example -O .env

# Pull the latest images
docker compose pull

# Start the services (in detached mode)
docker compose up -d

```

* The API would now be available at: `http://0.0.0.0:8080`
* Next, add your OpenAI API Key to the `.env`
* Set your environment variables

```bash
export JULEP_API_KEY=myauthkey
export JULEP_API_URL=http://0.0.0.0:8080
```

### Option 2: Use the Julep Cloud

* Generate an API key from https://platform.julep.ai
* Set your environment variables

```bash
export JULEP_API_KEY=your_julep_api_key
export JULEP_API_URL=https://api-alpha.julep.ai/api
```

## 1. Installation

```
pip install julep
```

## 2. Setting up the `client`

```py
from julep import Client
from pprint import pprint
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

## 3. Creating an `agent`

An agent is an object to which LLM settings like the model, temperature, and tools are scoped to.

```py
name = "Jessica"
about = "Jessica is a stuck up Cali teenager. Showing rebellion is an evolutionary necessity for her."
default_settings = {
    "temperature": 0.7,
    "top_p": 1,
    "min_p": 0.01,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "length_penalty": 1.0,
    "max_tokens": 150,
}

agent = client.agents.create(
    name=name,
    about=about,
    default_settings=default_settings,
    model="gpt-4",
    tools=[]
)
```

## 4. Creating a `user`

The user is the object which represents the user of the application.

Memories are formed and saved for each user and many users can talk to one agent.

```py
about = """Average nerdy techbro/girl who spends 8 hours a day in front of a laptop.
Thinks they can build a small SaaS tool and gain financial independence within the year.
"""
user = client.users.create(
    name="Anon",
    about=about,
)
```

## 5. Creating a `session`

A "user" and an "agent" communicate in a "session". The system prompt goes here. Conversation history and summary are stored in a "session" which saves the conversation history.

The session paradigm allows for; many users to interact with one agent and allows separation of conversation history and memories.

```py
situation_prompt = """You are Jessica. You're a stuck up Cali teenager. 
You basically complain about everything. You live in Bel-Air, Los Angeles and drag yourself to Curtis High School when you must.
"""

session = client.sessions.create(
    user_id=user.id, agent_id=agent.id, situation=situation_prompt
)
session = client.sessions.create(
    user_id=user.id, agent_id=agent.id, situation=situation_prompt
)

```

## 6. Starting a stateful conversation

`session.chat` controls the communication between the "agent" and the "user".

It has two important arguments;

* `recall`: Retrieves the previous conversations and memories.
* `remember`: Saves the current conversation turn into the memory store.

To keep the session stateful, both need to be `True`

```py
user_msg = "hey. what do u think of starbucks"
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

print("\n".join(textwrap.wrap(response.response[0][0].content, width=100)))
```
