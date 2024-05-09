<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Open-source%20platform%20for%20building%20stateful%20AI%20apps&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

---

<h2 align="center">
Start your project with conversation history, support for any LLM, agentic workflows, integrations & more.
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
## Why Julep?
We've built a lot of AI apps and understand how difficult it is to evaluate hundreds of tools, techniques, and models, and then make them work well together. 

**The Problem**

Even for simple apps you have to:
- pick the right language model for your use case
- pick the right framework
- pick the right embedding model
- choose the vector store and RAG pipeline
- build integrations 
- tweak all of the parameters (temp, penalty, max tokens, similarity thresholds, chunk size, and so on) 
- write and iterate on prompts for them to work

**The Solution**: 
Julep eases the burden and time taken to get up and running with any AI app.

- **Statefulness By Design**: Build AI apps without needing to write code to embed, save and retrieve conversation history. Deals with context windows by using CozoDB; a transactional, relational-graph-vector database.
- **Use and switch between any LLMs anytime**: Switch and use different LLMs, providers and models, self-hosted or otherwise by changing only *one line of code*
- **Automatic Function Calling**: No need to handle function calling manually. Julep deals with calling the function, parsing the response, retrying in case of failures and passing the response into the context.
- **Production-ready**: Julep comes ready to be deployed to production using Docker Compose. Support for k8s coming soon!
- **90+ tools built-in**: Connect your AI app to 150+ third-party applications using [Composio](https://docs.composio.dev/framework/julep/) natively.
- ***GitHub Actions-like workflows for task**: Define agentic workflows to be executed asynchronously without worrying about timeouts.
> (*) Features coming soon!

<!-- ![alt text](image.png) -->


## Quickstart
### Option 1: Install and run Julep locally
- Download the `docker-compose.yml` file along with the `.env` file for configuration to run the Julep platform locally

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
- The API would now be available at: `http://0.0.0.0:8080`

- Next, add your OpenAI API Key to the `.env`

- Set your environment variables
```bash
export JULEP_API_KEY=myauthkey
export JULEP_API_URL=http://0.0.0.0:8080
```
### Option 2: Use the Julep Cloud
- Generate an API key from https://platform.julep.ai
- Set your environment variables

```bash
export JULEP_API_KEY=your_julep_api_key
export JULEP_API_URL=https://api-alpha.julep.ai
```

### Installation

```
pip install julep
```
### Setting up the `client`

```py
from julep import Client
from pprint import pprint
import textwrap
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

### Create an agent
Agent is the object to which LLM settings like model, temperature along with tools are scoped to.
```py
agent = client.agents.create(
    name="Jessica"
    model="gpt-4",
    tools=[]    # Tools defined here
)
```

### Create a user
User is the object which represents the user of the application.

Memories are formed and saved for each user and many users can talk to one agent.
```py
user = client.users.create(
    name="Anon",
    about="Average nerdy techbro/girl spending 8 hours a day on a laptop,
)
```

### Create a session
A "user" and an "agent" communicate in a "session". System prompt goes here.
Conversation history and summary are stored in a "session" which saves the conversation history.

The session paradigm allows for; many users to interact with one agent and allow separation of conversation history and memories.

```py
situation_prompt = """You are Jessica. You're a stuck up Cali teenager. 
You basically complain about everything. You live in Bel-Air, Los Angeles and drag yourself to Curtis High School when you must.
"""
session = client.sessions.create(
    user_id=user.id, agent_id=agent.id, situation=situation_prompt
)
```

### Start a stateful conversation
`session.chat` controls the communication between the "agent" and the "user".

It has two important arguments;
- `recall`: Retrieves the previous conversations and memories.
- `remember`: Saves the current conversation turn into the memory store.

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
---

## API and SDKs
To use the API directly or to take a look at request & response formats, authentication, available endpoints and more, please refer to the [API Documentation](https://docs.julep.ai/api-reference/agents-api/agents-api)

You can also use the [Postman Collection](https://god.gw.postman.com/run-collection/33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336%26entityType%3Dcollection%26workspaceId%3D183380b4-f2ac-44ef-b018-1f65dfc8256b) for reference.

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
## Examples
You can test different examples of using Julep to make apps in the [example app docs](https://docs.julep.ai/cookbooks/example-apps).

1. [Simple Conversational Bot](https://deepnote.com/app/julep-ai-761c/Julep-Mixers-4dfff09a-84f2-4278-baa3-d1a00b88ba26)
2. [Discord Bot with Long-Term Memory](https://replit.com/@alt-glitch/LLM-App-with-Long-Term-Memory)
3. [AI Dungeon Master](https://github.com/julep-ai/julep-examples/tree/main/dungeon-master)
4. [Community Feedback Agent](https://github.com/julep-ai/julep-examples/tree/main/community-feedback)
---

## Deployment
Check out the [self-hosting guide](https://docs.julep.ai/agents/self-hosting) to host the platform yourself.

If you want to deploy Julep to production, [let's hop on a call](https://calendly.com/diwank-julep/45min)!

We'll help you customise the platform and help you get set up with:
- Multi-tenancy
- Reverse proxy along with authentication and authorisation
- Self-hosted LLMs
- & more

---
## Contributing
We welcome contributions from the community to help improve and expand the Julep AI platform. See [CONTRIBUTING.md](CONTRIBUTING.md)

---
## License
Julep AI is released under the Apache 2.0 License. By using, contributing to, or distributing the Julep AI platform, you agree to the terms and conditions of this license.

---
## Contact and Support
If you have any questions, need assistance, or want to get in touch with the Julep AI team, please use the following channels:

- [Discord](https://discord.com/invite/JTSBGRZrzj): Join our community forum to discuss ideas, ask questions, and get help from other Julep AI users and the development team.
- GitHub Issues: For technical issues, bug reports, and feature requests, please open an issue on the Julep AI GitHub repository.
- Email Support: If you need direct assistance from our support team, send an email to diwank@julep.ai, and we'll get back to you as soon as possible.
- Follow for updates on [X](https://twitter.com/julep_ai) & [LinkedIn](https://www.linkedin.com/company/julep-ai/)
- [Hop on a call](https://calendly.com/diwank-julep): We wanna know what you're building and how we can tweak and tune Julep to help you build your next AI app.
