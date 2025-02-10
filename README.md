<sup><div align="center">[English](README.md) | [中文翻译](README-CN.md) | [日本語翻訳](README-JA.md) | [French](README-FR.md)</div></sup>

<div align="center" id="top">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Rapidly%20build%20AI%20workflows%20and%20agents&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />

  <p>
    <a href="https://docs.julep.ai"><img src="https://img.shields.io/badge/Documentation-000000?style=for-the-badge&logo=github&logoColor=white" alt="Documentation"></a>
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/@julep/sdk?style=for-the-badge&logo=npm" alt="NPM Version"></a>
    <a href="https://pypi.org/project/julep/"><img src="https://img.shields.io/pypi/v/julep?style=for-the-badge&logo=python" alt="PyPI Version"></a>
  </p>
  <p>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&style=for-the-badge&logo=docker" alt="Docker Image Version"></a>
    <a href="https://github.com/julep-ai/julep/blob/main/LICENSE"><img src="https://img.shields.io/github/license/julep-ai/julep?style=for-the-badge" alt="License"></a>
  </p>
  
  <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3>
</div>


<p align="justify">
Julep is a platform for creating AI agents that remember past interactions and can perform complex tasks. It offers long-term memory and manages multi-step processes. Julep enables the creation of multi-step tasks incorporating decision-making, loops, parallel processing, and integration with numerous external tools and APIs. While many AI applications are limited to simple, linear chains of prompts and API calls with minimal branching, Julep is built to handle more complex scenarios which:

Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in. Read more about the Julep architecture and how it works in the [Documentation](https://docs.julep.ai/docs/advanced/architecture-deep-dive).
</p>


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table of Contents</h3>

- [✨ Key Features](#-key-features)
- [🧠 Mental Model](#-mental-model)
- [📦 Installation](#-installation)
  - [🛠️ Julep CLI](#️-julep-cli)
- [🚀 Quick Start](#-quick-start)
- [🔍 Reference](#-reference)
  - [📚 SDK Reference](#-sdk-reference)
  - [🛠️ API Reference](#️-api-reference)
- [💻 Local Setup](#-local-setup)
- [❓ What's the difference between Julep and LangChain etc?](#-whats-the-difference-between-julep-and-langchain-etc)
  - [Different Form Factor](#different-form-factor)
- [👥 Contributors](#-contributors)
- [📄 License](#-license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

---

## ✨ Key Features

<div align="left">
  <table>
    <tr>
      <td>🧠</td>
      <td><b>Persistent AI Agents</b></td>
      <td>Remember context and information over long-term interactions</td>
    </tr>
    <tr>
      <td>💾</td>
      <td><b>Stateful Sessions</b></td>
      <td>Keep track of past interactions for personalized responses</td>
    </tr>
    <tr>
      <td>🔄</td>
      <td><b>Multi-Step Tasks</b></td>
      <td>Build complex, multi-step processes with loops and decision-making</td>
    </tr>
    <tr>
      <td>⏳</td>
      <td><b>Task Management</b></td>
      <td>Handle long-running tasks that can run indefinitely</td>
    </tr>
    <tr>
      <td>🛠️</td>
      <td><b>Built-in Tools</b></td>
      <td>Use built-in tools and external APIs in your tasks</td>
    </tr>
    <tr>
      <td>🔧</td>
      <td><b>Self-Healing</b></td>
      <td>Julep will automatically retry failed steps, resend messages, and generally keep your tasks running smoothly</td>
    </tr>
    <tr>
      <td>📚</td>
      <td><b>RAG</b></td>
      <td>Use Julep's document store to build a system for retrieving and using your own data</td>
    </tr>
  </table>
</div>

<br/>

> [!TIP]
> 💡 Julep is ideal for applications that require AI use cases beyond simple prompt-response models.
> 
> 💡 To learn more about Julep, check out the [Documentation](https://docs.julep.ai/docs/introduction/overview).

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
  <img src="https://github.com/user-attachments/assets/38420b5d-9342-4c8d-bae9-b47c28ae45af" height="360" />
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

For more details, check out the [Julep CLI Documentation](https://docs.julep.ai/guides/julepcli/introduction).

> [!NOTE]
> Julep CLI is currently is still in early phase of development. Moreover, it's not yet available for Node.js.

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

```yaml YAML
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

In Python:
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

In Node.js:
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

</p>

<br/>

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

For detailed setup instructions, see our [Local Setup Guide](https://docs.julep.ai/docs/advanced/localsetup).

---

## ❓ What's the difference between Julep and LangChain etc?

<p align="justify">
Think of LangChain and Julep as tools with different focuses within the AI development stack.

LangChain is great for creating sequences of prompts and managing interactions with LLMs. It has a large ecosystem with lots of pre-built integrations, which makes it convenient if you want to get something up and running quickly. LangChain fits well with simple use cases that involve a linear chain of prompts and API calls.

Julep, on the other hand, is more about building persistent AI agents that can maintain context over long-term interactions. It shines when you need complex workflows that involve multi-step tasks, conditional logic, and integration with various tools or APIs directly within the agent's process. It's designed from the ground up to manage persistent sessions and complex workflows.

Use Julep if you imagine building a complex AI assistant that needs to:

- Keep track of user interactions over days or weeks.
- Perform scheduled tasks, like sending daily summaries or monitoring data sources.
- Make decisions based on prior interactions or stored data.
- Interact with multiple external services as part of its workflow.

Then Julep provides the infrastructure to support all that without you having to build it from scratch.
</p>

### Different Form Factor

<p align="justify">

Julep is a `platform` that includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform. In order to build something with Julep, you write a description of the workflow in `YAML`, and then run the workflow in the cloud.

Julep is built for heavy-lifting, multi-step, and long-running workflows and there's no limit to how complex the workflow can be.

LangChain is a `library` that includes a few tools and a framework for building linear chains of prompts and tools. In order to build something with LangChain, you typically write Python code that configures and runs the model chains you want to use.

LangChain might be sufficient and quicker to implement for simple use cases that involve a linear chain of prompts and API calls.
</p>

<p align="justify">
Use LangChain when you need to manage LLM interactions and prompt sequences in a stateless or short-term context.

Choose Julep when you need a robust framework for stateful agents with advanced workflow capabilities, persistent sessions, and complex task orchestration.
</p>

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

<div align="center">
  <a href="#top">
    <img src="https://img.shields.io/static/v1?label=&message=Back to Top&color=0366d6&style=for-the-badge&logo=github&logoColor=white" alt="Back to Top" />
  </a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="#-table-of-contents">
    <img src="https://img.shields.io/static/v1?label=&message=Table of Contents&color=0366d6&style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents" />
  </a>
</div>

<br/>
