<sup><div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  [Deutsch](https://www.readme-i18n.com/julep-ai/julep?lang=de) | 
  [Español](https://www.readme-i18n.com/julep-ai/julep?lang=es) | 
  [français](https://www.readme-i18n.com/julep-ai/julep?lang=fr) | 
  [日本語](https://www.readme-i18n.com/julep-ai/julep?lang=ja) | 
  [한국어](https://www.readme-i18n.com/julep-ai/julep?lang=ko) | 
  [Português](https://www.readme-i18n.com/julep-ai/julep?lang=pt) | 
  [Русский](https://www.readme-i18n.com/julep-ai/julep?lang=ru) | 
  [中文](https://www.readme-i18n.com/julep-ai/julep?lang=zh)
</div></sup>

<div align="center" id="top">
<img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Serverless%20AI%20Workflows%20for%20Data%20%26%20ML%20Teams&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" height=300 />

<br>
  <p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="Get API Key" height="28">
    </a>
    <span>&nbsp;</span>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=logo=gitbook&logoColor=white" alt="Documentation" height="28">
    </a>
  </p>
  <p>
   <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License" height="28"></a>
  </p>
  
  <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3>
</div>

<div align="center">
  <h3><i>Serverless AI Workflows for Data & ML Teams</i></h3>
</div>

## 🎉 Announcing: Julep Open Responses API (Alpha)

<div style="padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">

We're excited to announce the launch of our Open Responses API! This new API offers:

1. **OpenAI-compatible interface** - A drop-in replacement for your existing code
2. **Self-hosted, open-source implementation** - Works with any LLM backend
3. **Model Provider Agnostic** - Connect to any LLM provider (OpenAI, Anthropic, etc.)

The Open Responses API makes it easy to integrate with your existing applications while adding powerful new capabilities.

Ready to try it out? Check out our [Open Responses API documentation](https://docs.julep.ai/responses/quickstart) to get started!
</div>

Julep is a serverless platform that helps data and ML teams build sophisticated AI workflows. It provides a robust foundation for orchestrating complex AI operations, managing state across interactions, and integrating with your existing data infrastructure and tools.

Whether you're building data pipelines or creating AI workflows, Julep makes it easy to compose and scale LLM-powered workflows without managing infrastructure. Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in. Our platform handles the heavy lifting so you can focus on building intelligent solutions for your business.

💡 To learn more about Julep, check out the **[Documentation](https://docs.julep.ai/docs/introduction/overview)**.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table of Contents</h3>

- [✨ Key Features](#-key-features)
- [🧠 Mental Model](#-mental-model)
- [📦 Installation](#-installation)
  - [🛠️ Julep SDKs](#-julep-sdks)
  - [🛠️ Julep CLI](#-julep-cli)
- [🚀 Quick Start](#-quick-start)
  - [What's Next?](#whats-next)
- [🔍 Reference](#-reference)
  - [📚 SDK Reference](#-sdk-reference)
  - [🛠️ API Reference](#-api-reference)
- [💻 Local Setup](#-local-setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Navigate to the Root Directory](#2-navigate-to-the-root-directory)
  - [3. Set Up Environment Variables](#3-set-up-environment-variables)
  - [4. Create a Docker Volume for Backup](#4-create-a-docker-volume-for-backup)
  - [5. Run the Project using Docker Compose](#5-run-the-project-using-docker-compose)
  - [6. Interaction](#6-interaction)
  - [7. Troubleshooting](#7-troubleshooting)
- [👥 Contributors](#-contributors)
  - [Join Our Community! 🌟](#join-our-community-)
- [📄 License](#-license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

---

## ✨ Key Features

<div align="left">
  <table>
    <tr>
      <td>🧠</td>
      <td><b>Smart Memory</b></td>
      <td>Agents that remember context and learn from past interactions</td>
    </tr>
    <tr>
      <td>🔄</td>
      <td><b>Workflow Engine</b></td>
      <td>Build complex, multi-step processes with branching and loops</td>
    </tr>
    <tr>
      <td>⚡</td>
      <td><b>Parallel Processing</b></td>
      <td>Run multiple operations simultaneously for maximum efficiency</td>
    </tr>
    <tr>
      <td>🛠️</td>
      <td><b>Tool Integration</b></td>
      <td>Seamlessly connect with external APIs and services</td>
    </tr>
    <tr>
      <td>🔌</td>
      <td><b>Easy Setup</b></td>
      <td>Get started quickly with Python and Node.js SDKs</td>
    </tr>
    <tr>
      <td>🔒</td>
      <td><b>Reliable & Secure</b></td>
      <td>Built-in error handling, retries, and security features</td>
    </tr>
    <tr>
      <td>📊</td>
      <td><b>Monitoring</b></td>
      <td>Track task progress and performance in real-time</td>
    </tr>
  </table>
</div>

💡 To learn more about Julep, check out the **[Documentation](https://docs.julep.ai/docs/introduction/overview)**.

---

## 🧠 Mental Model

<p align="justify">
Julep is made up of the following components:

- **Julep Platform**: The Julep platform is a cloud service that runs your workflows. It includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform.
- **Julep SDKs**: Julep SDKs are a set of libraries for building workflows. There are SDKs for Python and JavaScript, with more on the way.
- **Julep CLI**: The Julep CLI is a command-line tool that allows you to interact with the Julep platform directly from your terminal.
- **Julep API**: The Julep API is a RESTful API that you can use to interact with the Julep platform.
</p>

<div align="center">
  <img src="https://github.com/user-attachments/assets/38420b5d-9342-4c8d-bae9-b47c28ae45af" height="360"/>
</div>

<p align="justify">
Think of Julep as a platform that combines both client-side and server-side components to help you build advanced AI agents. Here's how to visualize it:

1. **Your Application Code:**

   - You can use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.
   - You can use the Julep CLI to interact with the Julep platform directly from your terminal.

2. **Julep Backend Service:**

   - The SDK communicates with the Julep backend over the network.
   - The CLI communicates with the Julep backend via the SDK.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.
</p>

---

## 📦 Installation

<div align="left">
  <h3>🛠️ Julep SDKs</h3>

  To get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):

  <h4>Node.js</h4>

  ```bash
  npm install @julep/sdk

  # or

  bun add @julep/sdk
  ```

  <h4>Python</h4>

  ```bash
  pip install julep
  ```

  > [!NOTE]
  > 🔑 Get your API key [here](https://dashboard.julep.ai).
  >
  > Reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get to know more about Julep.
</div>

### 🛠️ Julep CLI

<p align="justify">
Julep CLI is a command-line tool that allows you to interact with the Julep platform directly from your terminal. It provides a convenient way to manage your AI workflows, tasks, and agents without needing to write code.
</p>

```bash
pip install julep-cli
```

For more details, check out the **[Julep CLI Documentation](https://docs.julep.ai/docs/julepcli/introduction)**.

> [!NOTE]
> The CLI is currently in beta and available for Python only. Node.js support coming soon!

---

## 🚀 Quick Start

<p align="justify">

Imagine a Research AI agent that can do the following:

1. **Take a topic**,
2. **Come up with 30 search queries** for that topic,
3. Perform those web **searches in parallel**,
4. **Summarize** the results,
5. Send the **summary to Discord**.
   
</p>

> [!NOTE]
> In Julep, this would be a single task under <b>80 lines of code</b> and run <b>fully managed</b> all on its own. All of the steps are executed on Julep's own servers and you don't need to lift a finger.

Here's a complete example of a task definition:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/julep-ai/julep/refs/heads/dev/schemas/create_task_request.json
name: Research Agent
description: A research assistant that can search the web and send the summary to Discord
########################################################
####################### INPUT ##########################
########################################################

# Define the input schema for the task
input_schema:
  type: object
  properties:
    topic:
      type: string
      description: The main topic to research
    num_questions:
      type: integer
      description: The number of search queries to generate

########################################################
####################### TOOLS ##########################
########################################################

# Define the tools that the agent can use
tools:
  - name: web_search
    type: integration
    integration:
      provider: brave
      setup:
        api_key: "<your-brave-api-key>"

  - name: discord_webhook
    type: api_call
    api_call:
      url: https://discord.com/api/webhooks/<your-webhook-id>/<your-webhook-token>
      method: POST
      headers:
        Content-Type: application/json

########################################################
####################### MAIN WORKFLOW #################
########################################################

# Special variables:
# - steps[index].input: for accessing the input to the step at that index
# - steps[index].output: for accessing the output of the step at that index
# - _: for accessing the output of the previous step

# Define the main workflow
main:
# Step 0: Generate search queries
- prompt:
    - role: system
      content: >-
        $ f"""
        You are a research assistant.
        Generate {{steps[0].input.num_questions|default(30, true)}} diverse search queries related to the topic:
        {steps[0].input.topic}

        Write one query per line.
        """
  unwrap: true

# Step 1: Evaluate the search queries using a simple python expression
- evaluate:
    search_queries: $ _.split(NEWLINE)

# Step 2: Run the web search in parallel for each query
- over: $ _.search_queries
  map:
    tool: web_search
    arguments:
      query: $ _
  parallelism: 5

# Step 3: Collect the results from the web search
- evaluate:
    search_results: $ _

# Step 4: Summarize the results
- prompt:
    - role: system
      content: >
        $ f"""
        You are a research summarizer. Create a comprehensive summary of the following research results on the topic {steps[0].input.topic}.
        The summary should be well-structured, informative, and highlight key findings and insights. Keep the summary concise and to the point.
        The length of the summary should be less than 150 words.
        Here are the search results:
        {_.search_results}
        """
  unwrap: true
  settings:
    model: gpt-4o-mini

# Step 5: Send the summary to Discord
- evaluate:
    discord_message: |-
      $ f'''
      **Research Summary for {steps[0].input.topic}**
      {_}
      '''

# Step 6: Send the summary to Discord
- tool: discord_webhook
  arguments:
    json_: 
      content: $ _.discord_message[:2000] # Discord has a 2000 character limit
```

Here you can execute the above workflow using the Julep SDK:

<details>
<summary><b>Python</b> <i>(Click to expand)</i></summary>

```python
from julep import Client
import yaml
import time

# Initialize the client
client = Client(api_key=JULEP_API_KEY)

# Create the agent
agent = client.agents.create(
  name="Julep Browser Use Agent",
  description="A Julep agent that can use the computer tool to interact with the browser.",
)

# Load the task definition
with open('./research_agent.yaml', 'r') as file:
  task_definition = yaml.safe_load(file)

# Create the task
task = client.tasks.create(
  agent_id=agent.id,
  **task_definition
)

# Create the execution
execution = client.executions.create(
    task_id=task.id,
    input={
        "topic": "artificial intelligence",
        "num_questions": 30
    }
)

# Wait for the execution to complete
while (result := client.executions.get(execution.id)).status not in ['succeeded', 'failed']:
    print(result.status)
    time.sleep(1)

# Print the result
if result.status == "succeeded":
    print(result.output)
else:
    print(f"Error: {result.error}")

```
</details>

</br>
<details>
<summary><b>Node.js</b> <i>(Click to expand)</i></summary>

```js
import { Julep } from '@julep/sdk';
import yaml from 'yaml';
import fs from 'fs';

// Initialize the client
const client = new Julep({
  apiKey: 'your_julep_api_key'
});

// Create the agent
const agent = await client.agents.create({
  name: "Julep Browser Use Agent",
  description: "A Julep agent that can use the computer tool to interact with the browser.",
});

// Parse the task definition
const taskDefinition = yaml.parse(fs.readFileSync('./research_agent.yaml', 'utf8'));

// Create the task
const task = await client.tasks.create(
  agent.id,
  taskDefinition
);

// Create the execution
const execution = await client.executions.create(
  task.id,
  {
    input: { 
      "topic": "artificial intelligence",
      "num_questions": 30
    }
  }
);

// Wait for the execution to complete
let result;
while (true) {
  result = await client.executions.get(execution.id);
  if (result.status === 'succeeded' || result.status === 'failed') break;
  console.log(result.status);
  await new Promise(resolve => setTimeout(resolve, 1000));
}

// Print the result
if (result.status === 'succeeded') {
  console.log(result.output);
} else {
  console.error(`Error: ${result.error}`);
}
```
</details>
</br>

In this example, Julep will automatically manage parallel executions, retry failed steps, resend API requests, and keep the tasks running reliably until completion.

> This runs in under 30 seconds and returns the following output:

<p align="justify">

<details>
<summary><b>Research Summary for AI</b> <i>(Click to expand)</i></summary>

> **Research Summary for AI**
>
> ### Summary of Research Results on Artificial Intelligence (AI)
>
> #### Introduction
>
> The field of Artificial Intelligence (AI) has seen significant advancements in recent years, marked by the development of methods and technologies that enable machines to perceive their environment, learn from data, and make decisions. The primary focus of this summary is on the insights derived from various research findings related to AI.
>
> #### Key Findings
>
> 1. **Definition and Scope of AI**:
>
>    - AI is defined as a branch of computer science focused on creating systems that can perform tasks requiring human-like intelligence, including learning, reasoning, and problem-solving (Wikipedia).
>    - It encompasses various subfields, including machine learning, natural language processing, robotics, and computer vision.
>
> 2. **Impact and Applications**:
>
>    - AI technologies are being integrated into numerous sectors, improving efficiency and productivity. Applications range from autonomous vehicles and healthcare diagnostics to customer service automation and financial forecasting (OpenAI).
>    - Google's commitment to making AI beneficial for everyone highlights its potential to significantly improve daily life by enhancing user experiences across various platforms (Google AI).
>
> 3. **Ethical Considerations**:
>
>    - There is an ongoing discourse regarding the ethical implications of AI, including concerns about privacy, bias, and accountability in decision-making processes. The need for a framework that ensures the safe and responsible use of AI technologies is emphasized (OpenAI).
>
> 4. **Learning Mechanisms**:
>
>    - AI systems utilize different learning mechanisms, such as supervised learning, unsupervised learning, and reinforcement learning. These methods allow AI to improve performance over time by learning from past experiences and data (Wikipedia).
>    - The distinction between supervised and unsupervised learning is critical; supervised learning relies on labeled data, while unsupervised learning identifies patterns without predefined labels (Unsupervised).
>
> 5. **Future Directions**:
>    - Future AI developments are expected to focus on enhancing the interpretability and transparency of AI systems, ensuring that they can provide justifiable decisions and actions (OpenAI).
>    - There is also a push towards making AI systems more accessible and user-friendly, encouraging broader adoption across different demographics and industries (Google AI).
>
> #### Conclusion
>
> AI represents a transformative force across multiple domains, promising to reshape industries and improve quality of life. However, as its capabilities expand, it is crucial to address the ethical and societal implications that arise. Continued research and collaboration among technologists, ethicists, and policymakers will be essential in navigating the future landscape of AI.

</details>

### What's Next?

- 📚 Explore more examples in our [Cookbook](https://github.com/julep-ai/julep/tree/dev/cookbooks)
- 🔧 Learn about [Tool Integration](https://docs.julep.ai/docs/tools/overview)
- 🧠 Understand [Agent Memory](https://docs.julep.ai/docs/agents/memory)
- 🔄 Dive into [Complex Workflows](https://docs.julep.ai/docs/tasks/workflows)

> [!TIP]
> 💡 Checkout more tutorials in the [Tutorials](https://docs.julep.ai/docs/tutorials/) section of the documentation.
> 
> 💡 If you are a beginner, we recommend starting with the [Quickstart Guide](https://docs.julep.ai/docs/introduction/quickstart).
> 
> 💡 If you are looking for more ideas, check out the [Ideas](https://github.com/julep-ai/julep/blob/dev/cookbooks/IDEAS.md) section of the repository.
> 
> 💡 If you more into cookbook style recipes, check out the [Cookbook](https://github.com/julep-ai/julep/tree/dev/cookbooks) section of the repository.
---

## 🔍 Reference

### 📚 SDK Reference

- **Node.js** [SDK Reference](https://github.com/julep-ai/node-sdk/blob/main/api.md) | [NPM Package](https://www.npmjs.com/package/@julep/sdk)
- **Python** [SDK Reference](https://github.com/julep-ai/python-sdk/blob/main/api.md) | [PyPI Package](https://pypi.org/project/julep/)

### 🛠️ API Reference

Explore our API documentation to learn more about agents, tasks, tools, and the Julep CLI here: [API Reference](https://docs.julep.ai/api-reference/)

---

## 💻 Local Setup

### 1. Clone the Repository

Clone the repository from your preferred source:

```bash
git clone <repository_url>
```

### 2. Navigate to the Root Directory

Change to the root directory of the project:

```bash
cd <repository_root>
```

### 3. Set Up Environment Variables

- Create a `.env` file in the root directory.
- Refer to the `.env.example` file for a list of required variables.
- Ensure that all necessary variables are set in the `.env` file.

### 4. Create a Docker Volume for Backup

Create a Docker volume named `grafana_data`, `memory_store_data`, `temporal-db-data`, `prometheus_data`, `seaweedfs_data`:

```bash
docker volume create grafana_data
docker volume create memory_store_data
docker volume create temporal-db-data
docker volume create prometheus_data
docker volume create seaweedfs_data
```

### 5. Run the Project using Docker Compose

You can run the project in two different modes: **Single Tenant** or **Multi-Tenant**. Choose one of the following commands based on your requirement:

1. Single-Tenant Mode

Run the project in single-tenant mode:

```bash
docker compose --env-file .env --profile temporal-ui --profile single-tenant --profile self-hosted-db --profile blob-store --profile temporal-ui-public up --build --force-recreate --watch
```

> **Note:** In single-tenant mode, you can interact with the SDK directly without the need for the API KEY.

2. Multi-Tenant Mode

Run the project in multi-tenant mode:

```bash
docker compose --env-file .env --profile temporal-ui --profile multi-tenant --profile embedding-cpu --profile self-hosted-db --profile blob-store --profile temporal-ui-public up --force-recreate --build --watch
```

> **Note:** In multi-tenant mode, you need to generate a JWT token locally that act as an API KEY to interact with the SDK.

Generate a JWT Token (Only for Multi-Tenant Mode)

To generate a JWT token, `jwt-cli` is required. Kindly install the same before proceeding with the next steps.

Use the following command and replace `JWT_SHARED_KEY` with the corresponding key from your `.env` file to generate a JWT token:

```bash
jwt encode --secret JWT_SHARED_KEY --alg HS512 --exp=$(date -d '+10 days' +%s) --sub '00000000-0000-0000-0000-000000000000' '{}'
```

This command generates a JWT token that will be valid for 10 days.

### 6. Interaction

- **Temporal UI**: You can access the Temporal UI through the specified port in your `.env` file.
- **Julep SDK**: The Julep SDK is a Python/Node.js library that allows you to interact with the Julep API.

```python
from julep import Client

client = Client(api_key="your_jwt_token")
```

**Note:** SDK in Multi-Tenant mode, you need to generate a JWT token locally that acts as an API KEY to interact with the SDK. Furthermore, while initializing the client you will need to set the environment to `local_multi_tenant` and the api key to the JWT token you generated in the previous step. Whereas in Single-Tenant mode you can interact with the SDK directly without the need for the API KEY and set the environment to `local`.

### 7. Troubleshooting

- Ensure that all required Docker images are available.
- Check for missing environment variables in the `.env` file.
- Use the `docker compose logs` command to view detailed logs for debugging.

---

## 👥 Contributors

<h3>Join Our Community! 🌟</h3>

We're excited to welcome new contributors to the Julep project! We've created several "good first issues" to help you get started.

<h4>How to Contribute:</h4>

1. 📖 Check out our [CONTRIBUTING.md](https://github.com/julep-ai/julep/blob/dev/CONTRIBUTING.md) file for guidelines
2. 🔍 Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
3. 💬 Join our [Discord](https://discord.com/invite/JTSBGRZrzj) for help and discussions

<br/>

Your contributions, big or small, are valuable to us. Let's build something amazing together! 🚀

<h4>Our Amazing Contributors:</h4>

<a href="https://github.com/julep-ai/julep/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=julep-ai/julep" />
</a>

---

## 📄 License

Julep is licensed under the [Apache License 2.0](LICENSE). 

See the LICENSE file for more details.

---
