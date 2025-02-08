<sup>[English](README.md) | [中文翻译](README-CN.md) | [日本語翻訳](README-JA.md) | [French](README-FR.md)</sup>

<div align="center" id="top">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Rapidly%20build%20AI%20workflows%20and%20agents&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

<div align="center">
  <a href="https://docs.julep.ai"><img src="https://img.shields.io/badge/Documentation-000000?style=flat-square&logo=github&logoColor=white" alt="Documentation"></a>
  <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/@julep/sdk?style=flat-square&logo=npm" alt="NPM Version"></a>
  <a href="https://pypi.org/project/julep/"><img src="https://img.shields.io/pypi/v/julep?style=flat-square&logo=python" alt="PyPI Version"></a>
  <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&style=flat-square&logo=docker" alt="Docker Image Version"></a>
  <a href="https://github.com/julep-ai/julep/blob/main/LICENSE"><img src="https://img.shields.io/github/license/julep-ai/julep?style=flat-square" alt="License"></a>
  <br />
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
</div>

Empower your AI projects with persistent agents and multi-step workflows.

## 🚀 Quick Start

---

## 📖 Introduction

Julep is a platform for creating AI agents that remember past interactions and can perform complex tasks. It offers long-term memory and manages multi-step processes.

Julep enables the creation of multi-step tasks incorporating decision-making, loops, parallel processing, and integration with numerous external tools and APIs.

While many AI applications are limited to simple, linear chains of prompts and API calls with minimal branching, Julep is built to handle more complex scenarios which:

- have multiple steps,
- make decisions based on model outputs,
- spawn parallel branches,
- use lots of tools, and
- run for a long time.

> [!TIP]
> Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in. Read [Understanding Tasks](#understanding-tasks) to learn more.

## ✨ Key Features

---

1. 🧠 **Persistent AI Agents**: Remember context and information over long-term interactions.
2. 💾 **Stateful Sessions**: Keep track of past interactions for personalized responses.
3. 🔄 **Multi-Step Tasks**: Build complex, multi-step processes with loops and decision-making.
4. ⏳ **Task Management**: Handle long-running tasks that can run indefinitely.
5. 🛠️ **Built-in Tools**: Use built-in tools and external APIs in your tasks.
6. 🔧 **Self-Healing**: Julep will automatically retry failed steps, resend messages, and generally keep your tasks running smoothly.
7. 📚 **RAG**: Use Julep's document store to build a system for retrieving and using your own data.

![features](https://github.com/user-attachments/assets/4355cbae-fcbd-4510-ac0d-f8f77b73af70)

> [!TIP]
> Julep is ideal for applications that require AI use cases beyond simple prompt-response models.

## 🧠 Mental Model

---

Julep is made up of the following components:

- **Julep Platform**: The Julep platform is a cloud service that runs your workflows. It includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform.
- **Julep SDKs**: Julep SDKs are a set of libraries for building workflows. There are SDKs for Python and JavaScript, with more on the way.
- **Julep API**: The Julep API is a RESTful API that you can use to interact with the Julep platform.

<div align="center">
  <img src="https://github.com/user-attachments/assets/38420b5d-9342-4c8d-bae9-b47c28ae45af" height="360" />
</div>

Think of Julep as a platform that combines both client-side and server-side components to help you build advanced AI agents. Here's how to visualize it:

1. **Your Application Code:**

   - You can use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.

2. **Julep Backend Service:**

   - The SDK communicates with the Julep backend over the network.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.
  
## 🛠️ Julep CLI

---

Julep CLI is a command-line tool that allows you to interact with the Julep platform directly from your terminal. It provides a convenient way to manage your AI workflows, tasks, and agents without needing to write code.

### Key Features

- **Task Management**: Easily create, update, and delete tasks.
- **Agent Management**: Manage your AI agents and their configurations.
- **Workflow Execution**: Run and monitor workflows directly from the command line.

For more details, check out the [Julep CLI Documentation](https://docs.julep.ai/guides/julepcli/introduction).

## �� Installation

---

To get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):

**Node.js**:

```bash
npm install @julep/sdk

# or

bun add @julep/sdk
```

**Python**:

```bash
pip install julep
```

> [!NOTE]
> Get your API key [here](https://dashboard.julep.ai).
>
> While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.

## 🔍 Reference

---

### 📚 SDK Reference

- **Node.js** [SDK Reference](https://github.com/julep-ai/node-sdk/blob/main/api.md) | [NPM Package](https://www.npmjs.com/package/@julep/sdk)
- **Python** [SDK Reference](https://github.com/julep-ai/python-sdk/blob/main/api.md) | [PyPI Package](https://pypi.org/project/julep/)

### 🛠️ API Reference

Explore our API documentation to learn more about agents, tasks, tools, and the Julep CLI here: [API Reference](https://docs.julep.ai/api-reference/)

## 💻 Local Quickstart

---

For detailed setup instructions, see our [Contributing Guide](CONTRIBUTING.md#setup-instructions).

## ❓ What's the difference between Julep and LangChain etc?

---

### Different Use Cases

Think of LangChain and Julep as tools with different focuses within the AI development stack.

LangChain is great for creating sequences of prompts and managing interactions with LLMs. It has a large ecosystem with lots of pre-built integrations, which makes it convenient if you want to get something up and running quickly. LangChain fits well with simple use cases that involve a linear chain of prompts and API calls.

Julep, on the other hand, is more about building persistent AI agents that can maintain context over long-term interactions. It shines when you need complex workflows that involve multi-step tasks, conditional logic, and integration with various tools or APIs directly within the agent's process. It's designed from the ground up to manage persistent sessions and complex workflows.

Use Julep if you imagine building a complex AI assistant that needs to:

- Keep track of user interactions over days or weeks.
- Perform scheduled tasks, like sending daily summaries or monitoring data sources.
- Make decisions based on prior interactions or stored data.
- Interact with multiple external services as part of its workflow.

Then Julep provides the infrastructure to support all that without you having to build it from scratch.

### Different Form Factor

Julep is a **platform** that includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform. In order to build something with Julep, you write a description of the workflow in `YAML`, and then run the workflow in the cloud.

Julep is built for heavy-lifting, multi-step, and long-running workflows and there's no limit to how complex the workflow can be.

LangChain is a **library** that includes a few tools and a framework for building linear chains of prompts and tools. In order to build something with LangChain, you typically write Python code that configures and runs the model chains you want to use.

LangChain might be sufficient and quicker to implement for simple use cases that involve a linear chain of prompts and API calls.

### In Summary

Use LangChain when you need to manage LLM interactions and prompt sequences in a stateless or short-term context.

Choose Julep when you need a robust framework for stateful agents with advanced workflow capabilities, persistent sessions, and complex task orchestration.

## 👥 Contributors

---

We're excited to welcome new contributors to the Julep project! We've created several "good first issues" to help you get started. Here's how you can contribute:

1. Check out our [CONTRIBUTING.md](https://github.com/julep-ai/julep/blob/dev/CONTRIBUTING.md) file for guidelines on how to contribute.
2. Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to find a task that interests you.
3. If you have any questions or need help, don't hesitate to reach out on our [Discord](https://discord.com/invite/JTSBGRZrzj) channel.

Your contributions, big or small, are valuable to us. Let's build something amazing together! 🚀

Also thanks goes to these wonderful people who have contributed to the project:

<a href="https://github.com/julep-ai/julep/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=julep-ai/julep" />
</a>

## 📄 License

---

Julep is licensed under the [Apache License 2.0](LICENSE). See the LICENSE file for more details.

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
