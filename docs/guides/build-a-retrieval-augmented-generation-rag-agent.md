---
description: >-
  Using Julep, you can create a RAG Agent without having to play around with
  vector databases like ChromaDB, Weaviate etc.
---

# Build a Retrieval Augmented Generation (RAG) Agent

Julep offers a pre-built RAG pipeline out of the box. You can specify data sources scoped to an agent or a user.

## Preview

We'll build an Agent in _<50 lines of code_ that has context over a blog post: [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) by Lilian Weng.

```python
from julep import Client
import os, bs4
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

api_key = os.environ['API_KEY']
base_url = os.environ['BASE_URL']

client = Client(api_key=api_key, base_url=base_url)

agent = client.agents.create(
    name="Archy",
    about="A self-aware agent who knows a lot about LLMs, autonomous and agentic apps.",
    model="gpt-4o",
    metadata={"name": "Archy"}
)

docs = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(parse_only=bs4.SoupStrainer(class_=("post-content", "post-title", "post-header")))
).load()

splits = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100).split_documents(docs)

for i, split in enumerate(splits):
    client.docs.create(
        agent_id=agent.id,
        doc={
            "title": "LLM Powered Autonomous Agents",
            "content": split.page_content,
            "metadata": {"chunk": i, **split.metadata},
        }
    )

session = client.sessions.create(
    agent_id=agent.id,
    situation="You are Ahti. You know all about AI and Agents",
    metadata={"agent_id": agent.id}
)

response = client.sessions.chat(
    session_id=session.id,
    messages=[{"role": "user", "content": "What are autonomous agents?"}],
    max_tokens=4096
)

(response_content,), doc_ids = response.response[0], response.doc_ids
print(f"{response_content.content}\n\nDocs used: {doc_ids}")
```

## Installation & Set-Up

```python
from julep import Client
from dotenv import load_dotenv
import os

load_dotenv()

client = Client(api_key=api_key, base_url=base_url)
```

## Creating an Agent

```python
agent = client.agents.create(
    name="Archy",
    about="A self aware agent who knows a lot about LLMs, autonomous and agentic apps.",
    model="gpt-4o",
    metadata={"name": "Ahti"},
)
```

## Chunking

You can also use your chunking strategy. We recommend playing with the chunking strategy for best results over your use case.

> Different chunk sizes, strategies have varied results over the accuracy of your RAG Agent!

```python
## Downloading and splitting a webpage to add to docs
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import bs4

loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
splits = text_splitter.split_documents(docs)
```

## Indexing/Adding Chunks

Here the document is scoped to the agent, so it's the agent that has the context about this blog.

It is also possible to scope a document to a user. This is particularly useful when there are different users and there's a document that needs to be added for each of them.

```python
for chunk_number, split in enumerate(splits):
    # Create a doc with the chunked content
    client.docs.create(
        agent_id=agent.id,
        doc={
            "title": "LLM Powered Autonomous Agents",
            "content": split.page_content,
            "metadata": {"chunk": chunk_number, **split.metadata},
        },
    )
```

## Create Session

```python
session = client.sessions.create(
    agent_id=agent.id,
    situation="You are Ahti. You know all about AI and Agents",
    metadata={"agent_id": agent.id},
)
```

## Invoke Agent

The `response` object also returns which `doc_ids` were used in generating a message.

```python
user_msg = "What are autonomous agents?"
response = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": user_msg,
        }
    ],
    max_tokens=4096,
    recall=True,
    remember=True,
)

# refer to doc_ids in the response
print(f"{response.response[0][0].content}\n\n Docs used:{response.doc_ids}")
```

