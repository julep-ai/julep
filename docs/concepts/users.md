---
description: A real person or system that needs to interacts with the Agent in your app.
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# 🙎 Users

## What is a User?

Users are meant to represent the entity using the application. These can be real people or other systems that require automated responses from an agent.

Each application can have multiple distinct users interacting with a single agent.

Users are _optional_ but recommended for applications where:

* It is beneficial to create a user persona for each individual interacting with an Agent. Especially, in applications where capturing details about the user can enhance the personalization and effectiveness of the interaction.
* You want to opt in and form memories about the user.

> Memories are formed and saved for each user separately so that the agent can refer to them as and when needed.

### Attributes

| Attributes             | Description                                                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------------- |
| Name                   | The user's name                                                                                 |
| About                  | A description for the user                                                                      |
| Documents _(optional)_ | Important documents in text format scoped to the user.                                          |
| Metadata _(optional)_  | Extra information to either identify or refer to the user in the application apart from it's ID |

## Creating a User

{% code overflow="wrap" lineNumbers="true" fullWidth="false" %}
```python
user = client.users.create(
    name="Anon",
    about="A 25 year old man with acute recurring headache.",
    docs=[{"title": "Blood test report", "content": "...", "metadata": {"page": 1}}],
    metadata={"db_uuid": "1234"},
)
```
{% endcode %}

## Retrieving a User

### Using a User ID

```python
user_id = "621ff51c-a813-4046-bfc6-ec425003e8c7"
client.users.get(user_id).json()
```

You should receive a response that resembles the following spec:

```json
{
  "name": "Anon",
  "about": "A 25 year old man with acute recurring headache.",
  "created_at": "2024-04-29T06:18:48.173889Z",
  "updated_at": "2024-04-29T06:18:48.173890Z",
  "id": "621ff51c-a813-4046-bfc6-ec425003e8c7",
  "metadata": {}
}
```

### Using Metadata Filters

```python
client.users.list(metadata_filter={"db_uuid": "1234"})
```

This returns a list of all the users with the specific metadata filter.

{% code overflow="wrap" %}
```python
[User(name='Anon', about='A 25 year old man with acute recurring headache.', created_at=datetime.datetime(2024, 4, 29, 6, 18, 48, 173889, tzinfo=datetime.timezone.utc), updated_at=datetime.datetime(2024, 4, 29, 6, 18, 48, 173890, tzinfo=datetime.timezone.utc), id='621ff51c-a813-4046-bfc6-ec425003e8c7', metadata=UserMetadata())]
```
{% endcode %}

## Updating a User

A user can be updated using its User ID. You can update any of its parameters.

```python
user_id = "621ff51c-a813-4046-bfc6-ec425003e8c7"
client.users.update(user_id=user_id, metadata={"db_uuid": "12345"})
```
