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
   <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License" height="28"></a>
  </p>
  
  <h3 align="center">
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294015-47144047-25ab-417c-af1b-6746820a20ff.gif" width="45"></a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow"><img src="https://raw.githubusercontent.com/gist/IgnaceMaes/744cd9cf41ec6acf46fc8f4e9f370f86/raw/d16658c2945d30c8a953b35cb17dd7085111b46c/x-logo.svg" width="32"></a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294012-0a55e343-37ad-4b0f-924f-c8431d9d2483.gif" width="45"></a>

  </h3>
</div>

**Try Julep Today:** Visit the **[Julep Website](https://julep.ai)** · Get started on the **[Julep Dashboard](https://dashboard.julep.ai)** (free API key) · Read the **[Documentation](https://docs.julep.ai/introduction/julep)**

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table of Contents</h3>

- [Why Julep?](#why-julep)
- [Getting Started](#getting-started)
- [Documentation and Examples](#documentation-and-examples)
- [Community and Contributions](#community-and-contributions)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->




## Why Julep?

Julep is an open-source platform for building **agent-based AI workflows** that go far beyond simple chains of prompts. It lets you orchestrate complex, multi-step processes with Large Language Models (LLMs) and tools **without managing any infrastructure**. With Julep, you can create AI agents that **remember past interactions** and handle sophisticated tasks with branching logic, loops, parallel execution, and integration of external APIs. In short, Julep acts like a *“Firebase for AI agents,”* providing a robust backend for intelligent workflows at scale.

**Key Features and Benefits:**

* **Persistent Memory:** Build AI agents that maintain context and long-term memory across conversations, so they can learn and improve over time.
* **Modular Workflows:** Define complex tasks as modular steps (in YAML or code) with conditional logic, loops, and error handling. Julep’s workflow engine manages multi-step processes and decisions automatically.
* **Tool Orchestration:** Easily integrate external tools and APIs (web search, databases, third-party services, etc.) as part of your agent’s toolkit. Julep’s agents can invoke these tools to augment their capabilities, enabling Retrieval-Augmented Generation and more.
* **Parallel & Scalable:** Run multiple operations in parallel for efficiency, and let Julep handle scaling and concurrency under the hood. The platform is serverless, so it seamlessly scales workflows without extra devops overhead.
* **Reliable Execution:** Don’t worry about glitches – Julep provides built-in retries, self-healing steps, and robust error handling to keep long-running tasks on track. You also get real-time monitoring and logging to track progress.
* **Easy Integration:** Get started quickly with our SDKs for **Python** and **Node.js**, or use the Julep CLI for scripting. Julep’s REST API is available if you want to integrate directly into other systems.

*Focus on your AI logic and creativity, while Julep takes care of the heavy lifting!* <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">



## Getting Started
<p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="Get API Key" height="28">
    </a>
    <span>&nbsp;</span>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=logo=gitbook&logoColor=white" alt="Documentation" height="28">
    </a>
  </p>
Getting up and running with Julep is simple:

1. **Sign Up & API Key:** First, sign up on the [Julep Dashboard](https://dashboard.julep.ai) to obtain your API key (needed for authenticating your SDK calls).
2. **Install the SDK:** Install the Julep SDK for your preferred language:

   * <img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="20"> **Python:** `pip install julep`
   * <img src="https://user-images.githubusercontent.com/74038190/212257454-16e3712e-945a-4ca2-b238-408ad0bf87e6.gif" width="20"> **Node.js:** `npm install @julep/sdk` (or `yarn add @julep/sdk`)
3. **Define Your Agent:** Use the SDK or YAML to define an agent and its task workflow. For example, you can specify the agent’s memory, tools it can use, and a step-by-step task logic. (See the **[Quick Start](https://docs.julep.ai/introduction/quick-start)** in our docs for a detailed walkthrough.)
4. **Run a Workflow:** Invoke your agent through the SDK to execute the task. The Julep platform will orchestrate the entire workflow in the cloud and manage the state, tool calls, and LLM interactions for you. You can check the agent’s output, monitor the execution on the dashboard, and iterate as needed.

That’s it! Your first AI agent can be up and running in minutes. For a complete tutorial, check out the **[Quick Start Guide](https://docs.julep.ai/introduction/quick-start)** in the documentation.

> **Note:** Julep also offers a command-line interface (CLI) (currently in beta for Python) to manage workflows and agents. If you prefer a no-code approach or want to script common tasks, see the [Julep CLI docs](https://docs.julep.ai/responses/quickstart#cli-installation) for details.



## Documentation and Examples


Looking to dive deeper? The **[Julep Documentation](https://docs.julep.ai)** covers everything you need to master the platform – from core concepts (Agents, Tasks, Sessions, Tools) to advanced topics like agent memory management and architecture internals. Key resources include:

* **[Concept Guides](https://docs.julep.ai/concepts/):** Learn about Julep’s architecture, how sessions and memory work, using tools, managing long conversations, and more.
* **[API & SDK Reference](https://docs.julep.ai/api-reference/):** Find detailed reference for all SDK methods and REST API endpoints to integrate Julep into your applications.
* **[Tutorials](https://docs.julep.ai/tutorials/):** Step-by-step guides for building real applications (e.g. a research agent that searches the web, a trip-planning assistant, or a chatbot with custom knowledge).
* **[Cookbook Recipes](https://github.com/julep-ai/julep/tree/dev/cookbooks):** Explore the **Julep Cookbook** for ready-made example workflows and agents. These recipes demonstrate common patterns and use cases – a great way to learn by example. *Browse the [`cookbooks/`](https://github.com/julep-ai/julep/tree/dev/cookbooks) directory in this repository for sample agent definitions.*
* **[IDE Integration](https://context7.com/julep-ai/julep):** Access Julep documentation directly in your IDE! Perfect for getting instant answers while coding.



## Community and Contributions

Join our growing community of developers and AI enthusiasts! Here are some ways to get involved and get support:

* **Discord Community:** Have questions or ideas? Join the conversation on our [official Discord server](https://discord.gg/7H5peSN9QP) to chat with the Julep team and other users. We’re happy to help with troubleshooting or brainstorm new use cases.
* **GitHub Discussions and Issues:** Feel free to use GitHub for reporting bugs, requesting features, or discussing implementation details. Check out the [**good first issues**](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) if you’d like to contribute – we welcome contributions of all kinds.
* **Contributing:** If you want to contribute code or improvements, please see our [Contributing Guide](CONTRIBUTING.md) for how to get started. We appreciate all PRs and feedback. By collaborating, we can make Julep even better!

*Pro tip: <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/e379a33a-b428-4385-b44f-3da16e7bac9f" width="35"> Star our repo to stay updated – we’re constantly adding new features and examples.*    

<br/>

Your contributions, big or small, are valuable to us. Let's build something amazing together!    <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">
 <img src="https://user-images.githubusercontent.com/74038190/216125640-2783ebd5-e63e-4ed1-b491-627a40b24850.png" width="20">

<h4>Our Amazing Contributors:</h4>

<a href="https://github.com/julep-ai/julep/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=julep-ai/julep" />
</a>

<br/>

## License

Julep is offered under the **Apache 2.0 License**, which means it’s free to use in your own projects. See the [LICENSE](LICENSE) file for details. Enjoy building with Julep!
