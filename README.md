# Julep AI
[![julep](https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Open%20platform%20for%20building%20stateful%20AI%20apps&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&name=1&owner=1&theme=Light)](https://github.com/julep-ai/julep)  

<p align="center">
<img src="https://github.com/julep-ai/julep/blob/dev/.github/julep-meaning-banner.png?raw=true" alt="Julep: an alcoholic drink containing whisky, crushed ice, sugar, and pieces of mint" />
</p>

<p align="center">
    <a href="https://discord.gg/JzfVWsy9fY"><img src="https://img.shields.io/discord/1172458124020547584?style=social&amp;logo=discord&amp;label=discord" alt="Discord"></a>
    <span>&nbsp;</span>
    <a href="https://twitter.com/julep_ai"><img src="https://img.shields.io/twitter/follow/julep_ai?style=social&amp;logo=x" alt="X (formerly Twitter) Follow"></a>
    <span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version"></a>
    <span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License"></a>
</p>


[Julep AI](https://julep.ai) is an advanced platform for creating stateful AI agents that can reason, plan, and execute complex tasks by leveraging tools and maintaining context throughout interactions. In addition to this README, you can also read the [full documentation](https://docs.julep.ai).

## Key Features

- [**Stateful AI Agents**](/#features-in-detail): AI agents that can break down requests into multiple steps, use different tools, and maintain state throughout the process.
- [**Tools and Capabilities**](/#features-in-detail): Access to built-in tools (and via integrations) to perform actions including _function calling_, _API calls_, and _RAG_.
- [**Memory System**](/#features-in-detail): A sophisticated memory system that enables agents to store and recall information automatically.
- [**Sessions and Tasks**](/#features-in-detail): Julep AI supports two main interaction modes: sessions and tasks. Sessions are short-lived, direct interactions with an agent, similar to a chat. Tasks are multi-step, long-running processes designed to accomplish complex goals.

## Getting Started

### Prerequisites

To use Julep AI, you need:

- A Julep AI account ([sign up here](https://www.julep.ai/))
- An API key (found in your Julep AI dashboard)
- Basic Python or TypeScript knowledge

### Installation

Julep AI offers language-agnostic APIs and SDKs for Python and TypeScript, making integration easy.

#### Python SDK

To install the latest version of the Python SDK, run the following command:

```bash
pip install julep==0.1.2
```

#### TypeScript SDK

To install the latest version of the TypeScript SDK using npm, run the following command:

```bash
npm install @julep/sdk@0.2.1
```

### Usage Examples

Here's a simple example of how to create a stateful AI agent using the current Julep AI Python SDK:

```python
from julep import JulepClient

client = JulepClient(api_key="YOUR_API_KEY")

# Create an agent
agent = client.create_agent(
    name="MyAgent",
    description="A sample AI agent",
    tools=[...],  # Define the tools your agent can use
)

# Create a user (optional)
user = client.create_user(
    name="John Doe",
    attributes={...},  # Add any relevant user attributes
)

# Start a session
session = client.create_session(
    agent_id=agent.id,
    user_id=user.id,   # optional
)

# Interact with the agent
response = client.send_message(
    session_id=session.id,
    message="Hello, how can you help me today?",
)

print(response.content)
```

For more detailed instructions, see the [full getting started guide](https://docs.julep.ai/getting-started).

For more detailed examples and usage instructions, please refer to the [documentation](https://docs.julep.ai/).

## API and SDKs

### Language-agnostic API

Julep AI offers a language-agnostic API that allows you to interact with the platform using any programming language that supports HTTP requests. The API endpoints are RESTful and return JSON responses.

To get started with the API, you'll need your API key, which you can find in your Julep AI dashboard. Include the API key in the `Authorization` header of your requests like this:

```
Authorization: Bearer YOUR_API_KEY
```

Make sure to replace `YOUR_API_KEY` with your actual API key.

For detailed information on the available endpoints, request/response formats, and authentication, please refer to the [API documentation](https://docs.julep.ai/api).

### Python SDK

The Julep AI Python SDK provides a convenient way to interact with the platform using Python. It offers a set of high-level abstractions and methods to create and manage agents, users, sessions, and tasks.

To install the latest version of the Python SDK, run:

```bash
pip install julep==0.1.2
```

For more information on using the Python SDK, please refer to the [Python SDK documentation](https://docs.julep.ai/sdks/python).

### TypeScript SDK

The Julep AI TypeScript SDK allows you to easily integrate Julep AI into your TypeScript projects. It provides type-safe methods and interfaces to interact with the platform.

To install the latest version of the TypeScript SDK using npm, run:

```bash
npm install @julep/sdk@0.2.1
```

For more information on using the TypeScript SDK, please refer to the [TypeScript SDK documentation](https://docs.julep.ai/sdks/typescript).

## Features in Detail

### Stateful AI Agents

At the core of Julep AI are stateful AI agents capable of reasoning about complex requests, breaking them down into multiple steps, and creating a plan to accomplish the goal. These agents can use different tools to perform each step, while maintaining context and state throughout the entire process. 

Key features of Julep AI's stateful agents include:

- Reasoning: Agents analyze the request, identify relevant information, and determine the necessary steps to fulfill it.
- Planning: Based on the reasoning, agents create a structured plan consisting of the actions needed to complete the request.
- Maintaining State: Agents keep track of the conversation history, completed steps, and results, allowing them to provide coherent and contextually relevant responses.

This enables agents to handle complex, multi-step tasks, adapt to the results of each action, and provide a seamless, stateful interaction experience.

### Tools and Capabilities

Julep AI agents can access a variety of tools to enhance their capabilities and perform specific actions. The built-in tool types include:

- Function-calling: Agents can respond in a structured format, allowing applications to interpret and execute the requested functions.
- API calls: Agents can automatically make API calls based on a given OpenAPI specification, enabling them to retrieve data from external services (e.g., getting the weather for a specific place and time).
- Retrieval Augmented Generation (RAG): Agents can efficiently retrieve and utilize relevant information from a knowledge base to generate more accurate and contextually appropriate responses.
- Web Browsing: Agents can navigate and interact with web pages, extract information, and perform actions like filling forms and clicking buttons.
- Database Queries: Agents can connect to databases, execute SQL queries, and retrieve structured data to use in their responses.
- External Integrations: Agents can integrate with third-party services and APIs to access additional functionality and data sources.

### Memory System

Julep AI features a sophisticated memory system that enables agents to store and recall information in three distinct but interconnected categories:

- Episodic Memory: Stores the history of an agent's interactions, including user messages, agent responses, and actions taken. This allows agents to maintain context and provide coherent responses throughout a conversation.
- Implicit Memory: Captures patterns and beliefs that the agent forms over time, such as user preferences, habits, or frequently asked questions. This enables agents to adapt their behavior and provide personalized experiences.
- Semantic Memory: Maintains a structured representation of knowledge, including entities, their attributes, and relationships. This allows agents to reason about the world, draw connections, and provide informed responses based on their understanding of concepts and facts.

While episodic memory focuses on specific events, implicit memory deals with generalized patterns, and semantic memory handles structured knowledge. These memory types work together to enable agents to continuously learn, adapt, and provide contextually relevant and personalized interactions.

### Sessions and Tasks

Julep AI supports two main interaction modes: sessions and tasks, each designed for different types of user interactions and agent behaviors.

Sessions are lightweight, real-time exchanges between a user and an agent, similar to a conversation. They are ideal for quick queries, clarifications, or simple requests that can be handled using the agent's built-in tools and knowledge. Sessions maintain short-term context but do not persist long-term state.

On the other hand, tasks are multi-step, asynchronous processes that can span minutes, hours, or even days. They are suitable for complex objectives that require planning, coordination, and the use of external tools and APIs. Tasks are defined using state machines, allowing agents to autonomously progress through the necessary steps, adapt to results, and maintain long-term state.

While sessions and tasks serve different purposes, they can work together seamlessly. A session can start a task, provide input or feedback, and monitor its progress. Conversely, a task can initiate sessions to gather additional information or deliver updates to the user. Tasks can also invoke other tasks as subtasks, enabling modular and reusable workflows.

This combination of sessions and tasks allows Julep AI agents to handle a wide range of user needs, from quick answers to complex, long-running projects, all within a unified and coherent interaction model.

## Deployment Options

### Cloud Platform

Julep AI offers a fully-managed cloud platform that allows you to quickly build, deploy, and scale AI agents without worrying about infrastructure. The cloud platform provides a seamless development experience and handles all the operational complexities, so you can focus on creating powerful AI-driven applications.

To get started with the Julep AI cloud platform:

1. Sign up for a Julep AI account at [https://www.julep.ai/](https://www.julep.ai/)
2. Create a new project and retrieve your API key from the dashboard
3. Install the Julep AI SDK for your preferred language (Python or TypeScript)
4. Start building your AI agents using the SDK and deploy them with a single command

Key benefits of the Julep AI cloud platform include:

- Fully managed infrastructure: No need to provision or manage servers, databases, or other resources
- Automatic scaling: Your agents can automatically scale up or down based on usage, ensuring optimal performance and cost-efficiency
- Built-in monitoring and logging: Keep track of your agents' performance and debug issues with ease
- Secure by default: All data is encrypted in transit and at rest, and access is strictly controlled through API keys and user roles
- Seamless integration: The platform integrates with popular tools and services, making it easy to extend your agents' capabilities

### Self-Hosting (Open-Source)

For developers and enterprises who prefer to host and manage their own instances of Julep AI, we provide an open-source version of the platform. The open-source version gives you complete control and flexibility over your deployment, allowing you to customize and extend the platform to suit your specific needs.

To self-host Julep AI:

1. Ensure you have the necessary prerequisites installed, such as Docker and Docker Compose.
2. Clone the Julep AI repository from [GitHub](https://github.com/julep-ai/julep).
3. Navigate to the `julep` directory and run `docker-compose up -d` to start the Julep AI services.
4. Access the Julep AI web interface at `http://localhost:3000` and follow the setup wizard to create your admin account and configure your instance.
5. Start building and deploying your AI agents using the self-hosted instance.

Self-hosting Julep AI provides several benefits:

- Full control: You have complete control over your instance, including data storage, security policies, and system configurations.
- Customization: You can customize and extend the platform by modifying the source code, adding new features, or integrating with your existing systems.
- Privacy: Self-hosting ensures that your data remains within your own infrastructure, providing enhanced privacy and data sovereignty.
- Offline access: You can run Julep AI in an offline or air-gapped environment, without requiring internet connectivity.

By self-hosting Julep AI, you can run the platform on-premises, in your own cloud environment, or in any other infrastructure that meets your requirements. You can also contribute to the platform's development and propose enhancements that can benefit the entire community.

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

We welcome contributions from the community to help improve and expand the Julep AI platform. See [CONTRIBUTING.md](/CONTRIBUTING.md)

## License

Julep AI is released under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). By using, contributing to, or distributing the Julep AI platform, you agree to the terms and conditions of this license.

## Contact and Support

If you have any questions, need assistance, or want to get in touch with the Julep AI team, please use the following channels:

- [Discord](https://discord.gg/JzfVWsy9fY): Join our community forum to discuss ideas, ask questions, and get help from other Julep AI users and the development team.
- [GitHub Issues](https://github.com/julep-ai/julep/issues): For technical issues, bug reports, and feature requests, please open an issue on the Julep AI GitHub repository.
- [Email Support](mailto:support@julep.ai): If you need direct assistance from our support team, send an email to support@julep.ai, and we'll get back to you as soon as possible.

Stay connected with Julep AI and get the latest updates by following us on [Twitter](https://twitter.com/julep_ai) and [LinkedIn](https://www.linkedin.com/company/julep-ai/).

We're excited to have you as part of the Julep AI community and look forward to seeing the amazing AI-driven applications you'll build with our platform!
