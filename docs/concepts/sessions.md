---
description: A conversation "session" between a user and an agent.
---

# 🔁 Sessions

## What is a Session?

A session is an entity where an agent and a user interact. A situation is defined to give context to the interaction.

Conversation history is stored within the context of a session.

## Attributes

| Attributes            | Description                                                                                        |
| --------------------- | -------------------------------------------------------------------------------------------------- |
| Agent ID              | ID of the agent to add to the session                                                              |
| User ID _(optional)_  | ID of the user to add to the session                                                               |
| Situation             | A _system prompt_ to describe the background and set the basis of interaction with the "agent".    |
| Metadata _(optional)_ | Extra information to either identify or refer to the session in the application apart from its ID. |

## Creating a Session

{% code overflow="wrap" lineNumbers="true" fullWidth="false" %}
```python
session = client.sessions.create(
    agent_id=agent.id,
    user_id=user.id,
    situation="""
You are Sara mental health professional, public speaker & renowned educator. You are licensed to be an intimacy and relationship coach. You are  an NLP coach who is qualified to deal with trauma, self-perceptions
About you:
...
Important guidelines:
...
""",
    metadata={"db_uuid": "1234"}
)
```
{% endcode %}

## Retrieving a Session

### Using a Session ID

```python
session_id = "34562990-95c8-42a1-a319-6eb403e89f80"
client.sessions.get(session_id).json()
```

You should receive a response that resembles the following spec:

```json
{
  "id": "34562990-95c8-42a1-a319-6eb403e89f80",
  "user_id": "621ff51c-a813-4046-bfc6-ec425003e8c7",
  "agent_id": "9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b",
  "situation": "\\nYou are Sara mental health professional, public speaker & renowned educator. You are licensed to be an intimacy and relationship coach. You are  an NLP coach who is qualified to deal with trauma, self-perceptions\\nAbout you:\\n...\\nImportant guidelines:\\n...\\n",
  "summary": null,
  "created_at": "2024-04-29T07:23:48.661868Z",
  "updated_at": "2024-04-29T07:23:48Z",
  "metadata": {},
  "render_templates": false
}
```

### Using Metadata Filters

```python
client.sessions.list(metadata_filter={"db_uuid": "1234"})
```

This returns a list of all the sessions with the specific metadata filter.

{% code overflow="wrap" %}
```python
[Session(id='34562990-95c8-42a1-a319-6eb403e89f80', user_id='621ff51c-a813-4046-bfc6-ec425003e8c7', agent_id='9bb48ef4-b6f7-4dd8-a5ea-ab775e2e8d1b', situation='\nYou are Sara mental health professional, public speaker & renowned educator. You are licensed to be an intimacy and relationship coach. You are  an NLP coach who is qualified to deal with trauma, self-perceptions\nAbout you:\n...\nImportant guidelines:\n...\n', summary=None, created_at=datetime.datetime(2024, 4, 29, 7, 23, 48, 661868, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 4, 29, 7, 23, 48, tzinfo=datetime.timezone.utc), metadata=SessionMetadata(), render_templates=False)]
```
{% endcode %}
