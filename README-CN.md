<sup>English | [中文翻译](https://github.com/julep-ai/julep/blob/dev/README-CN.md) | [日本語翻訳](https://github.com/julep-ai/julep/blob/dev/README-JP.md)</sup><div align="center">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20AI%20agents%20and%20multi-step%20tasks&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&theme=Auto" alt="julep" width="640" height="320" />
</div>
<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow"><strong>Explore Docs</strong></a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
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
[!NOTE]
👨‍💻 Here for the devfest.ai event? Join our [Discord](https://discord.com/invite/JTSBGRZrzj) and check out the details below.<details>
<summary><b>🌟 Contributors and DevFest.AI Participants</b> (Click to expand)</summary>
🌟 招募贡献者！我们很高兴欢迎新贡献者加入 Julep 项目！我们创建了几个“好的第一个问题”来帮助您入门。以下是您可以做出贡献的方式：Check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to find a task that interests you.If you have any questions or need help, don't hesitate to reach out on our [Discord](https://discord.com/invite/JTSBGRZrzj) channel.您的贡献，无论大小，对我们来说都是宝贵的。让我们一起创造一些了不起的东西！🚀🎉 DevFest.AI 2024 年 10 月令人兴奋的消息！我们将参加 2024 年 10 月的 DevFest.AI！🗓️在本次活动期间为 Julep 做出贡献，就有机会赢得超棒的 Julep 商品和赃物！🎁与来自世界各地的开发人员一起为 AI 资源库做出贡献并参与精彩的活动。非常感谢 DevFest.AI 组织这次精彩的活动！[!TIP]
Ready to join the fun? **[Tweet that you are participating](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** and let's get coding! 🖥️[!NOTE]
Get your API key [here](https://dashboard-dev.julep.ai).While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)</details>
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary><h3>📖 Table of Contents</h3></summary>

- [Optional: Define the input schema for the task](#optional-define-the-input-schema-for-the-task)
- [Define the tools that the agent can use](#define-the-tools-that-the-agent-can-use)
- [Special variables:](#special-variables)
- [- inputs: for accessing the input to the task](#--inputs-for-accessing-the-input-to-the-task)
- [- outputs: for accessing the output of previous steps](#--outputs-for-accessing-the-output-of-previous-steps)
- [- _: for accessing the output of the previous step](#--_-for-accessing-the-output-of-the-previous-step)
- [Define the main workflow](#define-the-main-workflow)
- [Evaluate the search queries using a simple python expression](#evaluate-the-search-queries-using-a-simple-python-expression)
- [Run the web search in parallel for each query](#run-the-web-search-in-parallel-for-each-query)
- [Collect the results from the web search](#collect-the-results-from-the-web-search)
- [Summarize the results](#summarize-the-results)
- [Send the summary to Discord](#send-the-summary-to-discord)
- [🛠️ Add an image generation tool (DALL·E) to the agent](#-add-an-image-generation-tool-dall%C2%B7e-to-the-agent)
- [Create a task that takes an idea and creates a story and a 4-panel comic strip](#create-a-task-that-takes-an-idea-and-creates-a-story-and-a-4-panel-comic-strip)
- [Step 1: Generate a story and outline into 4 panels](#step-1-generate-a-story-and-outline-into-4-panels)
- [Step 2: Extract the小组描述和故事evaluate:](#step-2-extract-the%E5%B0%8F%E7%BB%84%E6%8F%8F%E8%BF%B0%E5%92%8C%E6%95%85%E4%BA%8Bevaluate)
    - [Step 3: Execute the Task](#step-3-execute-the-task)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->
介绍Julep 是一个用于创建 AI 代理的平台，这些代理可以记住过去的互动并执行复杂的任务。它提供长期记忆并管理多步骤流程。Julep 支持创建多步骤任务，包括决策、循环、并行处理以及与众多外部工具和 API 的集成。虽然许多人工智能应用程序仅限于简单、线性的提示链和 API 调用，并且分支很少，但 Julep 可以处理更复杂的场景。它支持：复杂、多步骤的流程动态决策并行执行[!TIP]
Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in.快速示例想象一下一个可以执行以下操作的研究 AI 代理：选一个话题，针对该主题提出 100 个搜索查询，同时进行这些网页搜索，总结结果，将摘要发送至 DiscordIn Julep, this would be a single task under <b>80 lines of code</b> and run <b>fully managed</b> all on its own. All of the steps are executed on Julep's own servers and you don't need to lift a finger. Here's a working example:name: Research Agent

# Optional: Define the input schema for the task
input_schema:
  type: object
  properties:
    topic:
      type: string
      description: The main topic to research

# Define the tools that the agent can use
tools:
- name: web_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "YOUR_BRAVE_API_KEY"

- name: discord_webhook
  type: api_call
  api_call:
    url: "YOUR_DISCORD_WEBHOOK_URL"
    method: POST
    headers:
      Content-Type: application/json

# Special variables:
# - inputs: for accessing the input to the task
# - outputs: for accessing the output of previous steps
# - _: for accessing the output of the previous step

# Define the main workflow
main:
- prompt:
    - role: system
      content: >-
        You are a research assistant.
        Generate 100 diverse search queries related to the topic:
        {{inputs[0].topic}}

        Write one query per line.
  unwrap: true

# Evaluate the search queries using a simple python expression
- evaluate:
    search_queries: "_.split('\n')"

# Run the web search in parallel for each query
- over: "_.search_queries"
  map:
    tool: web_search
    arguments:
      query: "_"
  parallelism: 100

# Collect the results from the web search
- evaluate:
    results: "'\n'.join([item.result for item in _])"

# Summarize the results
- prompt:
    - role: system
      content: >
        You are a research summarizer. Create a comprehensive summary of the following research results on the topic {{inputs[0].topic}}.
        The summary should be well-structured, informative, and highlight key findings and insights:
        {{_.results}}
  unwrap: true

# Send the summary to Discord
- tool: discord_webhook
  arguments:
    content: >
      **Research Summary for {{inputs[0].topic}}**

      {{_}}
[!TIP]
Julep is really useful when you want to build AI agents that can maintain context and state over long-term interactions. It's great for designing complex, multi-step workflows and integrating various tools and APIs directly into your agent's processes.在这个例子中，Julep 将自动管理并行执行，重试失败的步骤，重新发送 API 请求，并保持任务可靠运行直到完成。主要特点🧠 **Persistent AI Agents**: Remember context and information over long-term interactions.💾 **Stateful Sessions**: Keep track of past interactions for personalized responses.🔄 **Multi-Step Tasks**: Build complex, multi-step processes with loops and decision-making.⏳ **Task Management**: Handle long-running tasks that can run indefinitely.🛠️ **Built-in Tools**: Use built-in tools and external APIs in your tasks.🔧 **Self-Healing**: Julep will automatically retry failed steps, resend messages, and generally keep your tasks running smoothly.📚 **RAG**: Use Julep's document store to build a system for retrievi并使用您自己的数据。Julep 非常适合需要超越简单的提示响应模型的 AI 用例的应用程序。为什么选择 Julep 而不是 LangChain？不同的用例可以将 LangChain 和 Julep 视为 AI 开发堆栈中具有不同重点的工具。LangChain 非常适合创建提示序列和管理与 AI 模型的交互。它拥有庞大的生态系统，包含大量预构建的集成，如果您想快速启动和运行某些功能，这会非常方便。LangChain 非常适合涉及线性提示链和 API 调用的简单用例。另一方面，Julep 更注重构建持久的 AI 代理，这些代理可以在长期交互​​中记住事物。当您需要涉及多个步骤、决策以及在代理流程中直接与各种工具或 API 集成的复杂任务时，它会大放异彩。它从头开始设计，以管理持久会话和复杂任务。如果您想构建一个需要执行以下操作的复杂 AI 助手，请使用 Julep：跟踪几天或几周内的用户互动。执行计划任务，例如发送每日摘要或监控数据源。根据之前的互动或存储的数据做出决策。作为其任务的一部分，与多个外部服务进行交互。然后 Julep 提供支持所有这些的基础设施，而无需您从头开始构建。不同的外形尺寸Julep is a **platform** that includes a language for describing tasks, a server for running those tasks, and an SDK for interacting with the platform. To build something with Julep, you write a description of the task in `YAML`, and then run the task in the cloud.Julep 专为繁重、多步骤和长时间运行的任务而设计，并且对任务的复杂程度没有限制。LangChain is a **library** that includes a few tools and a framework for building linear chains of prompts and tools. To build something with LangChain, you typically write Python code that configures and runs the model chains you want to use.对于涉及线性提示和 API 调用链的简单用例，LangChain 可能足够并且能够更快地实现。总之当您需要在无状态或短期环境中管理 AI 模型交互和提示序列时，请使用 LangChain。当您需要一个具有高级任务功能、持久会话和复杂任务管理的状态代理的强大框架时，请选择 Julep。安装To get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):npm install @julep/sdk
或者pip install julep
[!NOTE]
Get your API key [here](https://dashboard-dev.julep.ai).While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.[!TIP]
💻 Are you a _show me the code!™_ kind of person? We have created a ton of cookbooks for you to get started with. **Check out the [cookbooks](https://github.com/julep-ai/julep/tree/dev/cookbooks)** to browse through examples.💡 There's also lots of ideas that you can build on top of Julep. **Check out the [list of ideas](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** to get some inspiration.Python 快速入门🐍步骤 1：创建代理import yaml
from julep import Julep # or AsyncJulep

client = Julep(api_key="your_julep_api_key")

agent = client.agents.create(
    name="Storytelling Agent",
    model="gpt-4o",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)

# 🛠️ Add an image generation tool (DALL·E) to the agent
client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_openai_api_key",
        },
    },
)
步骤 2：创建生成故事和漫画的任务让我们定义一个多步骤任务来创建一个故事并根据输入的想法生成面板漫画：# 📋 Task
# Create a task that takes an idea and creates a story and a 4-panel comic strip
task_yaml = """
name: Story and Comic Creator
description: Create a story based on an idea and generate a 4-panel comic strip illustrating the story.

main:
  # Step 1: Generate a story and outline into 4 panels
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip.
          Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story.
    unwrap: true

  # Step 2: Extract the小组描述和故事evaluate:
  story: _.split('1. ')[0].strip()
  panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)步骤 3：使用图像生成器工具为每个面板生成图像foreach:
  in: _.panels
  do:
    tool: image_generator
    arguments:
      description: _步骤 4：为故事想一个吸引人的标题迅速的：role: system
content: You are {{agent.name}}. {{agent.about}}role: user
content: >
  Based on the story below, generate a catchy title.Story: {{outputs[1].story}}
unwrap: true步骤 5：返回故事、生成的图像和标题return:
  title: outputs[3]
  story: outputs[1].story
  comic_panels: "[output.image.url for output in outputs[2]]"
"""task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)
### Step 3: Execute the Task

```python
# 🚀 Execute the task with an input idea
execution = client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 Watch as the story and comic panels are generated
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)

# 📦 Once the execution is finished, retrieve the results
result = client.executions.get(execution_id=execution.id)
步骤 4：与代理聊天开始与代理进行交互式聊天会话：session = client.sessions.create(agent_id=agent.id)

# 💬 Send messages to the agent
while (message := input("Enter a message: ")) != "quit":
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )

    print(response)
[!TIP]
You can find the full python example [here](example.py).Node.js 快速入门🟩步骤 1：创建代理import { Julep } from '@julep/sdk';
import yaml from 'js-yaml';

const client = new Julep({ apiKey: 'your_julep_api_key' });

async function createAgent() {
  const agent = await client.agents.create({
    name: "Storytelling Agent",
    model: "gpt-4",
    about: "You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
  });

  // 🛠️ Add an image generation tool (DALL·E) to the agent
  await client.agents.tools.create(agent.id, {
    name: "image_generator",
    description: "Use this tool to generate images based on descriptions.",
    integration: {
      provider: "dalle",
      method: "generate_image",
      setup: {
        api_key: "your_openai_api_key",
      },
    },
  });

  return agent;
}
步骤 2：创建生成故事和漫画的任务const taskYaml = `
name: Story and Comic Creator
description: Create a story based on an idea and generate a 4-panel comic strip illustrating the story.

main:
  # Step 1: Generate a story and outline into 4 panels
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip.
          Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story.
    unwrap: true

  # Step 2: Extract the panel descriptions and story
  - evaluate:
      story: _.split('1. ')[0].trim()
      panels: _.match(/\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)/g)

  # Step 3: Generate images for each panel using the image generator tool
  - foreach:
      in: _.panels
      do:
        tool: image_generator
        arguments:
          description: _

  # Step 4: Generate a catchy title for the story
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the story below, generate a catchy title.

          Story: {{outputs[1].story}}
    unwrap: true

  # Step 5: Return the story, the generated images, and the title
  - return:
      title: outputs[3]
      story: outputs[1].story
      comic_panels: outputs[2].map(output => output.image.url)
`;

async function createTask(agent) {
  const task = await client.tasks.create(agent.id, yaml.load(taskYaml));
  return task;
}
步骤 3：执行任务async function executeTask(task) {
  const execution = await client.executions.create(task.id, {
    input: { idea: "A cat who learns to fly" }
  });

  // 🎉 Watch as the story and comic panels are generated
  for await (const transition of client.executions.transitions.stream(execution.id)) {
    console.log(transition);
  }

  // 📦 Once the execution is finished, retrieve the results
  const result = await client.executions.get(execution.id);
  return result;
}
步骤 4：与代理聊天async function chatWithAgent(agent) {
  const session = await client.sessions.create({ agent_id: agent.id });

  // 💬Send messages to the agent
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });const chat = async () => {
    rl.question("Enter a message (or 'quit' to exit): ", async (message) => {
      if (message.toLowerCase() === 'quit') {
        rl.close();
        return;
      }  const response = await client.sessions.chat(session.id, { message });
  console.log(response);
  chat();
});
};chat();
}// Run the example
async function runExample() {
  const agent = await createAgent();
  const task = await createTask(agent);
  const result = await executeTask(task);
  console.log("Task Result:", result);
  await chatWithAgent(agent);
}运行示例()。捕获(控制台.错误);
> [!TIP]
> You can find the full Node.js example [here](example.js).

## Components

Julep is made up of the following components:

- **Julep Platform**: The Julep platform is a cloud service that runs your workflows. It includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform.
- **Julep SDKs**: Julep SDKs are a set of libraries for building workflows. There are SDKs for Python and JavaScript, with more on the way.
- **Julep API**: The Julep API is a RESTful API that you can use to interact with the Julep platform.

### Mental Model

<div align="center">
  <img src="https://github.com/user-attachments/assets/38420b5d-9342-4c8d-bae9-b47c28ae45af" height="360" />
</div>

Think of Julep as a platform that combines both client-side and server-side components to help you build advanced AI agents. Here's how to visualize it:

1. **Your Application Code:**
   - You use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.

2. **Julep Backend Service:**
   - The SDK communicates with the Julep backend over the network.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.

In simpler terms:
- Julep is a platform for building stateful AI agents.
- You use the SDK (like a toolkit) in your code to define what your agents do.
- The backend service (which you can think of as the engine) runs these definitions, manages state, and handles complexity.

## Concepts

Julep is built on several key technical components that work together to create powerful AI workflows:

```mermaid
graph TD
    User[User] ==> Session[Session]
    Session --> Agent[Agent]
    Agent --> Tasks[Tasks]
    Agent --> LLM[Large Language Model]
    Tasks --> Tools[Tools]
    Agent --> Documents[Documents]
    Documents --> VectorDB[Vector Database]
    Tasks --> Executions[Executions]

    classDef client fill:#9ff,stroke:#333,stroke-width:1px;
    class User client;

    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    class Agent,Tasks,Session core;
**Agents**: AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users.**Users**: Entities that interact with agents through sessions.**Sessions**: Stateful interactions between agents and users, maintaining context across multiple exchanges.**Tasks**: Multi-step, programmatic workflows that agents can execute, including various types of steps like prompts, tool calls, and conditional logic.**Tools**: Integrations that extend an agent's capabilities, including user-defined functions, system tools, or third-party API integrations.**Documents**: Text or data objects associated with agents or users, vectorized and stored for semantic search and retrieval.**Executions**: Instances of tasks that have been initiated with specific inputs, with their own lifecycle and state machine.For a more detailed explanation of these concepts and their interactions, please refer to our [Concepts Documentation](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md).理解任务任务是 Julep 工作流系统的核心。它们允许您定义代理可以执行的复杂、多步骤 AI 工作流。以下是任务组件的简要概述：**Name and Description**: Each task has a unique name and description for easy identification.**Main Steps**: The core of a task, defining the sequence of actions to be performed.**Tools**: Optional integrations that extend the capabilities of your agent during task execution.工作流步骤的类型Julep 中的任务可以包含各种类型的步骤，让您可以创建复杂而强大的工作流程。以下是按类别组织的可用步骤类型的概述：常见步骤**Prompt**: Send向 AI 模型发送消息并接收响应。- prompt: "Analyze the following data: {{data}}"
**Tool Call**: Execute an integrated tool or API.- tool: web_search
  arguments:
    query: "Latest AI developments"
**Evaluate**: Perform calculations or manipulate data.- evaluate:
    average_score: "sum(scores) / len(scores)"
**Wait for Input**: Pause workflow until input is received.- wait_for_input:
    info:
      message: "Please provide additional information."
**Log**: Log a specified value or message.- log: "Processing completed for item {{item_id}}"
关键值步骤**Get**: Retrieve a value from a key-value store.- get: "user_preference"
**Set**: Assign a value to a key in a key-value store.- set:
    user_preference: "dark_mode"
迭代步骤**Foreach**: Iterate over a collection and perform steps for each item.- foreach:
    in: "data_list"
    do:
      - log: "Processing item {{_}}"
**Map-Reduce**: Map over a collection and reduce the results.- map_reduce:
    over: "numbers"
    map:
      - evaluate:
          squared: "_ ** 2"
    reduce: "sum(results)"
**Parallel**: Run multiple steps in parallel.- parallel:
    - tool: web_search
      arguments:
        query: "AI news"
    - tool: weather_check
      arguments:
        location: "New York"
条件步骤**If-Else**: Conditional execution of steps.- if: "score > 0.8"
  then:
    - log: "High score achieved"
  else:
    - log: "Score needs improvement"
**Switch**: Execute steps based on multiple conditions.- switch:
    - case: "category == 'A'"
      then:
        - log: "Category A processing"
    - case: "category == 'B'"
      then:
        - log: "Category B processing"
    - case: "_"  # Default case
      then:
        - log: "Unknown category"
其他控制流**Sleep**: Pause the workflow for a specified duration.- sleep:
    seconds: 30
**Return**: Return a value from the workflow.- return:
    result: "Task completed successfully"
**Yield**: Run a subworkflow and await its completion.- yield:
    workflow: "data_processing_subflow"
    arguments:
      input_data: "{{raw_data}}"
**Error**: Handle errors by specifying an error message.- error: "Invalid input provided"
每种步骤类型在构建复杂的 AI 工作流中都有特定的用途。此分类有助于理解 Julep 任务中可用的各种控制流程和操作。高级功能Julep 提供一系列高级功能来增强您的 AI 工作流程：为代理添加工具通过集成外部工具和 API 来扩展代理的功能：client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {"api_key": "your_brave_api_key"},
    },
)
管理会话和用户Julep 为持久交互提供了强大的会话管理：session = client.sessions.create(
    agent_id=agent.id,
    user_id=user.id,
    context_overflow="adaptive"
)

# Continue conversation in the same session
response = client.sessions.chat(
    session_id=session.id,
    messages=[
      {
        "role": "user",
        "content": "Follow up on the previous conversation."
      }
    ]
)
文档集成与搜索轻松管理和搜索代理的文档：# Upload a document
document = client.agents.docs.create(
    title="AI advancements",
    content="AI is changing the world...",
    metadata={"category": "research_paper"}
)

# Search documents
results = client.agents.docs.search(
    text="AI advancements",
    metadata_filter={"category": "research_paper"}
)
For more advanced features and detailed usage, please refer to our [Advanced Features Documentation](https://docs.julep.ai/advanced-features).集成Julep 支持各种集成，可以扩展您的 AI 代理的功能。以下是可用集成及其支持的参数的列表：勇敢搜索setup:
  api_key: string  # The API key for Brave Search

arguments:
  query: string  # The search query for searching with Brave

output:
  result: string  # The result of the Brave Search
浏览器基础setup:
  api_key: string       # The API key for BrowserBase
  project_id: string    # The project ID for BrowserBase
  session_id: string    # (Optional) The session ID for BrowserBasearguments:
  urls: list[string]    # The URLs for loading with BrowserBaseoutput:
  documents: list       # The documents loaded from the URLs
### Email

```yaml
setup:
  host: string      # The host of the email server
  port: integer     # The port of the email server
  user: string      # The username of the email server
  password: string  # The password of the email server

arguments:
  to: string        # The email address to send the email to
  from: string      # The email address to send the email from
  subject: string   # The subject of the email
  body: string      # The body of the email

output:
  success: boolean  # Whether the email was sent successfully
蜘蛛setup:
  spider_api_key: string  # The API key for Spider

arguments:
  url: string             # The URL for which to fetch data
  mode: string            # The type of crawlers (default: "scrape")
  params: dict            # (Optional) The parameters for the Spider API

output:
  documents: list         # The documents returned from the spider
天气setup:
  openweathermap_api_key: string  # The API key for OpenWeatherMap

arguments:
  location: string                # The location for which to fetch weather data

output:
  result: string                  # The weather data for the specified location
维基百科arguments:
  query: string           # The search query string
  load_max_docs: integer  # Maximum number of documents to load (default: 2)

output:
  documents: list         # The documents returned from the Wikipedia search
These integrations can be used within your tasks to extend the capabilities of your AI agents. For more detailed information on how to use these integrations in your workflows, please refer to our [Integrations Documentation](https://docs.julep.ai/integrations).SDK 参考[Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)[Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)API 参考浏览我们全面的 API 文档，以了解有关代理、任务和执行的更多信息：[Agents API](https://api.julep.ai/api/docs#tag/agents)[Tasks API](https://api.julep.ai/api/docs#tag/tasks)[Executions API](https://api.julep.ai/api/docs#tag/executions)->> Test <<-
A simple update to text the translation github action