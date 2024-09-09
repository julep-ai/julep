<!-- Hidden 
# TODO: Add coming soon announcement to README
# SCRUM-32
-->

<sup>English | [中文翻译](/README-CN.md)</sup>

<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Open-source%20platform%20for%20building%20stateful%20AI%20apps&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

<h2 align="center">
Build powerful AI applications with stateful agents, complex workflows, and integrated tools.
</h2>

  <p align="center">
    <br />
    <a href="https://docs.julep.ai" rel="dofollow"><strong>Explore the docs »</strong></a>
    <br />
  <br/>
    <a href="https://github.com/julep-ai/julep/issues/new">Report Bug</a>
    ·
    <a href="https://github.com/julep-ai/julep/discussions/293">Request Feature</a>
    ·
    <a href="https://discord.com/invite/JTSBGRZrzj">Join Our Discord</a>
    ·
    <a href="https://x.com/julep_ai">X</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai">LinkedIn</a>

</p>


<p align="center">
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License"></a>
</p>

---

## 🚀 Upcoming Release: v0.4 Alpha

<div align="center">
  <img src=".github/i-have-an-announcement.gif" alt="Announcing v0.4 Alpha">
</div>

We're excited to announce that v0.4 is currently in alpha! This release brings significant improvements and new features. Stay tuned for the official release.

For a comprehensive overview of Julep's core concepts and upcoming features, check out our [detailed concepts guide](docs/julep-concepts.md).

Looking for the previous version? You can find the [v0.3 README here](v0.3_README.md).

---

## Why Julep?
We've built a lot of AI apps and understand the challenges in creating complex, stateful applications with multiple agents and workflows.

**The Problems**
1. Building AI applications with memory, knowledge, and tools is complex and time-consuming.
2. Managing long-running tasks and complex workflows in AI applications is challenging.
3. Integrating multiple tools and services into AI applications requires significant development effort.

---
## Features
- **Stateful Agents**: Create and manage agents with built-in conversation history and memory.
- **Complex Workflows**: Define and execute multi-step tasks with branching, parallel execution, and error handling.
- **Integrated Tools**: Easily incorporate a wide range of tools and external services into your AI applications.
- **Flexible Session Management**: Support for various interaction patterns like one-to-many and many-to-one between agents and users.
- **Built-in RAG**: Add, delete & update documents to provide context to your agents.
- **Asynchronous Task Execution**: Run long-running tasks in the background with state management and resumability.
- **Multi-Model Support**: Switch between different language models (OpenAI, Anthropic, Ollama) while preserving state.
- **Task System**: Define and execute complex, multi-step workflows with parallel processing and error handling.

---
## Quickstart
### Option 1: Use the Julep Cloud
Our hosted platform is in Beta! 

To get access:
- Head over to https://platform.julep.ai
- Generate and add your `JULEP_API_KEY` in `.env`

### Option 2: Install and run Julep locally
Head over to docs on [self-hosting](https://docs.julep.ai/guides/self-hosting) to see how to run Julep locally!

### Installation

```bash
pip install julep
```

### Setting up the `client`

```python
from julep import Client
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

### Create an agent
Agent is the object to which LLM settings like model, temperature along with tools are scoped to.

```python
agent = client.agents.create(
    name="Jessica",
    model="gpt-4",
    tools=[],    # Tools defined here
    about="A helpful AI assistant",
    instructions=["Be polite", "Be concise"]
)
```

### Create a user
User is the object which represents the user of the application.

Memories are formed and saved for each user and many users can talk to one agent.

```python
user = client.users.create(
    name="Anon",
    about="Average nerdy techbro/girl spending 8 hours a day on a laptop",
)
```

### Create a session
A "user" and an "agent" communicate in a "session". System prompt goes here.

```python
situation_prompt = """You are Jessica, a helpful AI assistant. 
You're here to assist the user with any questions or tasks they might have."""
session = client.sessions.create(
    user_id=user.id,
    agent_id=agent.id,
    situation=situation_prompt
)
```

### Start a stateful conversation
`session.chat` controls the communication between the "agent" and the "user".

It has two important arguments;
- `recall`: Retrieves the previous conversations and memories.
- `remember`: Saves the current conversation turn into the memory store.

To keep the session stateful, both need to be `True`

```python
user_msg = "Hey Jessica, can you help me with a task?"
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

print(response.response[0][0].content)
```

---

## Core Concepts

### Agent
An Agent in Julep is the main orchestrator of your application. It's backed by foundation models like GPT-4 or Claude and can use tools, documents, and execute complex tasks.

### User
Users in Julep represent the end-users of your application. They can be associated with sessions and have their own documents and metadata.

### Session
Sessions manage the interaction between users and agents. They maintain conversation history and context.

### Tool
Tools are functions that agents can use to perform specific actions or retrieve information.

### Doc
Docs are collections of text snippets that can be associated with agents or users and are used for context retrieval.

### Task
Tasks are complex, multi-step workflows that can be defined and executed by agents.

### Execution
An Execution is an instance of a Task that has been started with some input. It goes through various states as it progresses.

---

## API and SDKs

To use the API directly or to take a look at request & response formats, authentication, available endpoints and more, please refer to the [API Documentation](https://docs.julep.ai/api-reference/agents-api/agents-api)

### Python SDK

To install the Python SDK, run:

```bash
pip install julep
```

For more information on using the Python SDK, please refer to the [Python SDK documentation](https://docs.julep.ai/api-reference/python-sdk-docs).

### TypeScript SDK
To install the TypeScript SDK using `npm`, run:

```bash
npm install @julep/sdk
```

For more information on using the TypeScript SDK, please refer to the [TypeScript SDK documentation](https://docs.julep.ai/api-reference/js-sdk-docs).

---

## Deployment
Check out the [self-hosting guide](https://docs.julep.ai/agents/self-hosting) to host the platform yourself.

If you want to deploy Julep to production, [let's hop on a call](https://cal.com/ishitaj/15min)!

We'll help you customise the platform and help you get set up with:
- Multi-tenancy
- Reverse proxy along with authentication and authorisation
- Self-hosted LLMs
- & more

---
## Contributing
We welcome contributions from the community to help improve and expand the Julep AI platform. Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information on how to get started.

---
## License
Julep AI is released under the Apache 2.0 License. See the [LICENSE](LICENSE) file for more details.

---
## Contact and Support
If you have any questions, need assistance, or want to get in touch with the Julep AI team, please use the following channels:

- [Discord](https://discord.com/invite/JTSBGRZrzj): Join our community forum to discuss ideas, ask questions, and get help from other Julep AI users and the development team.
- GitHub Issues: For technical issues, bug reports, and feature requests, please open an issue on the Julep AI GitHub repository.
- Email Support: If you need direct assistance from our support team, send an email to hey@julep.ai, and we'll get back to you as soon as possible.
- Follow for updates on [X](https://twitter.com/julep_ai) & [LinkedIn](https://www.linkedin.com/company/julep-ai/)
- [Hop on a call](https://cal.com/ishitaj/15min): We wanna know what you're building and how we can tweak and tune Julep to help you build your next AI app.
