# Julep AI
[![julep](https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Open%20platform%20for%20building%20AI%20agents&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&name=1&owner=1&stargazers=1&theme=Light)](https://github.com/julep-ai/julep)  

[![Discord](https://img.shields.io/discord/1172458124020547584?style=social&logo=discord&label=discord)](https://discord.gg/JzfVWsy9fY)
<span>&nbsp;</span>
[![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/julep_ai?style=social&logo=x)](https://twitter.com/julep_ai)
<span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
[![NPM Version](https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&logo=npm&link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk)](https://www.npmjs.com/package/@julep/sdk)
<span>&nbsp;</span>
[![PyPI - Version](https://img.shields.io/pypi/v/julep?style=social&logo=python&label=PyPI&link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep)](https://pypi.org/project/julep)
<span>&nbsp;</span>
[![Docker Image Version](https://img.shields.io/docker/v/julepai/agents-api?sort=semver&style=social&logo=docker&link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai)](https://hub.docker.com/u/julepai)<span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
[![GitHub License](https://img.shields.io/github/license/julep-ai/julep)](https://choosealicense.com/licenses/apache/)

Julep AI is an advanced platform for creating stateful AI agents that can reason, plan, and execute complex tasks by leveraging tools and maintaining context throughout interactions. With Julep AI, developers can build sophisticated AI-powered applications that deliver personalized and context-aware user experiences.

## Key Features

### Stateful AI Agents

At the core of Julep AI are stateful AI agents capable of breaking down complex requests into multiple steps, using different tools to accomplish each step, and maintaining state throughout the process. This allows agents to reason about a request, create a plan, execute the necessary actions, and dynamically adapt to the results of each step.

### Tools and Capabilities

Julep AI agents can access a variety of tools to enhance their capabilities and perform specific actions. These tools include:

- Function-calling: Agents can respond in a structured format, allowing applications to interpret and execute the requested functions.
- API calls: Agents can automatically make API calls based on a given OpenAPI specification, enabling them to retrieve data from external services (e.g., getting the weather for a specific place and time).
- Retrieval Augmented Generation (RAG): Agents can efficiently retrieve and utilize relevant information from a knowledge base to generate more accurate and contextually appropriate responses.

### Memory System

Julep AI features a sophisticated memory system that enables agents to store and recall information in three categories:

- Episodic Memory: Stores events that occur during an agent's interactions, such as a user asking for help with a specific task.
- Implicit Memory: Captures beliefs that the agent forms over time, particularly about users, such as their preferences or habits.
- Semantic Memory: Maintains a graph of known entities, their attributes, and relationships, allowing agents to reason about the world and provide more informed responses.

These memory types work together to enable agents to continuously learn from interactions, adapt to user needs, and provide personalized experiences.

### Sessions and Tasks

Julep AI supports two main interaction modes: sessions and tasks.

- Sessions are short-lived, direct interactions between a user and an agent, similar to a chat interface. During sessions, agents can use built-in tools like document retrieval or function-calling to provide immediate assistance.
- Tasks, on the other hand, are multi-step, long-running processes designed to accomplish complex goals. Tasks are defined as state machines, allowing agents to autonomously navigate through the necessary steps and execute actions using background tools and APIs.

While sessions cannot directly initiate long-term actions, they can start and monitor tasks defined for the same agent. Similarly, tasks can invoke other tasks, creating powerful abstractions and enabling agents to handle complex workflows seamlessly.

## Getting Started

### Prerequisites

To start using Julep AI, you'll need:

- A Julep AI account (sign up at [https://www.julep.ai/](https://www.julep.ai/))
- An API key (available in your Julep AI dashboard)
- Basic programming knowledge (Python or TypeScript)

### Installation

Julep AI provides language-agnostic APIs and SDKs for Python and TypeScript, making it easy to integrate into your projects.

#### Python SDK

To install the Python SDK, run the following command:

```bash
pip install julep
```

#### TypeScript SDK

To install the TypeScript SDK using npm, run the following command:

```bash
npm install @julep/sdk
```

### Usage Examples

Here's a simple example of how to create a stateful AI agent using the Julep AI Python SDK:

```python
from julep import Client

client = Client(api_key="YOUR_API_KEY")

# Create an agent
agent = client.agents.create(
    name="MyAgent",
    description="A sample AI agent",
    tools=[...],  # Define the tools your agent can use
)

# Create a user (optional)
user = client.users.create(
    name="John Doe",
    attributes={...},  # Add any relevant user attributes
)

# Start a session
session = client.sessions.create(
    agent_id=agent.id,
    user_id=user.id,   # optional
)

# Interact with the agent
response = client.sessions.send_message(
    session_id=session.id,
    message="Hello, how can you help me today?",
)

print(response.content)
```

For more detailed examples and usage instructions, please refer to the [documentation](https://docs.julep.ai/).

## API and SDKs

### Language-agnostic API

Julep AI offers a language-agnostic API that allows you to interact with the platform using any programming language that supports HTTP requests. The API endpoints are RESTful and return JSON responses.

To get started with the API, you'll need your API key, which you can find in your Julep AI dashboard. Include the API key in the `Authorization` header of your requests.

For detailed information on the available endpoints, request/response formats, and authentication, please refer to the [API documentation](https://docs.julep.ai/api).

### Python SDK

The Julep AI Python SDK provides a convenient way to interact with the platform using Python. It offers a set of high-level abstractions and methods to create and manage agents, users, sessions, and tasks.

To install the Python SDK, run:

```bash
pip install julep
```

For more information on using the Python SDK, please refer to the [Python SDK documentation](https://docs.julep.ai/sdks/python).

### TypeScript SDK

The Julep AI TypeScript SDK allows you to easily integrate Julep AI into your TypeScript projects. It provides type-safe methods and interfaces to interact with the platform.

To install the TypeScript SDK using npm, run:

```bash
npm install @julep/sdk
```

For more information on using the TypeScript SDK, please refer to the [TypeScript SDK documentation](https://docs.julep.ai/sdks/typescript).

## Deployment Options

### Cloud Platform

Julep AI offers a fully-managed cloud platform that allows you to quickly get started with building and deploying AI agents. The cloud platform provides a seamless experience, handling the infrastructure, scaling, and maintenance, so you can focus on creating powerful AI-driven applications.

To start using the Julep AI cloud platform:

1. Sign up for a Julep AI account at [https://www.julep.ai/](https://www.julep.ai/)
2. Retrieve your API key from the dashboard
3. Start building your AI agents using the API or SDKs

The cloud platform offers a range of features, including automatic scaling, monitoring, and secure data management.

### Self-Hosting (Open-Source)

For developers and enterprises who prefer to host and manage their own instances of Julep AI, we provide an open-source version of the platform. The open-source version gives you complete control over your deployment, allowing you to customize and extend the platform to suit your specific needs.

To self-host Julep AI:

1. Clone the Julep AI repository from [GitHub](https://github.com/julep-ai/julep)
2. Follow the installation and setup instructions in the repository's README
3. Configure your instance according to your requirements
4. Start building and deploying your AI agents

Self-hosting Julep AI allows you to run the platform on-premises, in your own cloud environment, or in any other infrastructure of your choice. It also enables you to contribute to the platform's development and propose enhancements that can benefit the entire community.

## Frequently Asked Questions (FAQs)

1. **What is the difference between a session and a task?**
   - A session is a short-lived, direct interaction between a user and an AI agent, similar to a chat interface. Sessions are designed for immediate, real-time assistance using built-in tools like document retrieval or function-calling.
   - A task, on the other hand, is a multi-step, long-running process designed to accomplish complex goals. Tasks are defined as state machines, allowing agents to autonomously navigate through the necessary steps and execute actions using background tools and APIs.

2. **Can I use Julep AI with my existing data sources or APIs?**
   Yes, you can integrate Julep AI with your existing data sources and APIs. Julep AI agents can make API calls based on OpenAPI specifications, allowing them to retrieve data from external services. Additionally, you can use the retrieval augmented generation (RAG) capabilities to enable agents to access and utilize your own knowledge bases.

3. **How does the memory system work in Julep AI?**
   The Julep AI memory system consists of three types of memory: episodic, implicit, and semantic. Episodic memory stores events that occur during an agent's interactions, implicit memory captures beliefs that the agent forms over time, and semantic memory maintains a graph of known entities, their attributes, and relationships. These memories are automatically stored and retrieved based on the context, allowing agents to provide personalized and contextually relevant responses.

4. **Can I customize and extend the Julep AI platform?**
   Yes, you can customize and extend the Julep AI platform to suit your specific needs. The open-source version of Julep AI allows you to modify the codebase, add new features, and integrate custom tools or services. You can also contribute your enhancements back to the community by submitting pull requests to the main repository.

5. **What programming languages can I use with Julep AI?**
   Julep AI provides a language-agnostic API, which means you can use any programming language that supports making HTTP requests to interact with the platform. However, for convenience, we offer SDKs for Python and TypeScript, which provide high-level abstractions and methods to simplify the integration process. If you prefer to use another language, you can still work with the API directly.


## Contributing

We welcome contributions from the community to help improve and expand the Julep AI platform. There are several ways you can contribute:

### Reporting Issues

If you encounter any bugs, have feature requests, or want to discuss potential improvements, please open an issue on the [Julep AI GitHub repository](https://github.com/julep-ai/julep/issues). When reporting issues, please provide as much detail as possible, including steps to reproduce the problem, expected behavior, and any relevant code snippets or screenshots.

### Submitting Pull Requests

If you want to contribute code changes or additions to the Julep AI platform, please follow these steps:

1. Fork the [Julep AI repository](https://github.com/julep-ai/julep) on GitHub
2. Create a new branch for your changes
3. Make your modifications and ensure that the code follows the project's coding conventions
4. Write appropriate tests to cover your changes
5. Commit your changes and push them to your forked repository
6. Submit a pull request to the main Julep AI repository, clearly describing your changes and their benefits

Our team will review your pull request and provide feedback. Once your changes are approved, they will be merged into the main repository and included in the next release.

### Documentation Improvements

Improving the documentation is another excellent way to contribute to the Julep AI project. If you find any errors, omissions, or areas that need clarification in the documentation, please submit a pull request with your proposed changes.

### Sharing Feedback and Ideas

We value your feedback and ideas! If you have any suggestions for improving Julep AI or have innovative use cases to share, please join our [community forum](https://community.julep.ai/) and start a discussion. Your input helps shape the future direction of the platform.

By contributing to Julep AI, you help create a more robust, feature-rich, and user-friendly platform for building AI-driven applications. We appreciate your support and look forward to collaborating with you!

## License

Julep AI is released under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). By using, contributing to, or distributing the Julep AI platform, you agree to the terms and conditions of this license.

## Contact and Support

If you have any questions, need assistance, or want to get in touch with the Julep AI team, please use the following channels:

- [Discord](https://discord.gg/JzfVWsy9fY): Join our community forum to discuss ideas, ask questions, and get help from other Julep AI users and the development team.
- [GitHub Issues](https://github.com/julep-ai/julep/issues): For technical issues, bug reports, and feature requests, please open an issue on the Julep AI GitHub repository.
- [Email Support](mailto:support@julep.ai): If you need direct assistance from our support team, send an email to support@julep.ai, and we'll get back to you as soon as possible.

Stay connected with Julep AI and get the latest updates by following us on [Twitter](https://twitter.com/JulepAI) and [LinkedIn](https://www.linkedin.com/company/julep-ai/).

We're excited to have you as part of the Julep AI community and look forward to seeing the amazing AI-driven applications you'll build with our platform!
