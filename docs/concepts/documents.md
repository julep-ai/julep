---
description: Documents to be added for Retrieval Augmented Generation
---

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


# 📖 Documents

A typical RAG application has the following components:

1. Chunking
2. Storing
3. Retrieval
4. Generation

Julep offers a pre-built RAG pipeline out of the box. You can specify data sources scoped to an agent or a user.

## Adding Documents

### While creating agents/users

{% code overflow="wrap" %}
```python
docs = [
    {
        "title": "Computer Scientists Invent an Efficient New Way to Count",
        "content": """In a recent paper, computer scientists have described a new way to approximate the number of distinct entries in a long list...""",
        "metadata": {"page": 1},
    },
    {
        "title": "Computer Scientists Invent an Efficient New Way to Count",
        "metadata": {"page": 2},
        "content": """The CVM algorithm, named for its creators — Sourav Chakraborty of the Indian Statistical Institute, Vinodchandran Variyam of the University of Nebraska, Lincoln, and Kuldeep Meel of the University of Toronto ...""",
    },
]
```
{% endcode %}

Docs can be scoped to agents or users directly.

```python
client.agents.create(
    name="Computer Scientist",
    model="gpt-4-turbo",
    docs=docs
)
```

> Useful for scenarios where an agent needs to have more context about private data or specific topic that needs to be available to all users.

```python
client.users.create(
    name="Anon",
    docs=docs
)
```

> Useful for scenarios where each user has a different persona, documentation.

### Using \`docs.create\`

Docs can also be added to an agent/user ad-hoc.

```python
client.docs.create(
    agent_id=agent.id,
    # user_id=user.id,
    doc={
        "title": "Good and Bad Procrastination",
        "metadata": {"chunk": 1},
        "content": """The most impressive people I know are all terrible procrastinators. So could it be that procrastination isn't always bad? Most people who write about procrastination write about how to cure it. But this is, strictly speaking, impossible. There are an infinite number of things you could be doing. No matter what you work on, you're not working on everything else. So the question is not how to avoid procrastination, but how to procrastinate well.""",
    },
)
```

