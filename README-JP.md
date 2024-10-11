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
🌟 寄稿者を募集します!Julep プロジェクトに新しい貢献者を迎えられることを嬉しく思います。プロジェクトを始めるのに役立つ「最初の良い問題」をいくつか作成しました。貢献する方法は次のとおりです。Check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to find a task that interests you.If you have any questions or need help, don't hesitate to reach out on our [Discord](https://discord.com/invite/JTSBGRZrzj) channel.あなたの貢献は、大小を問わず私たちにとって貴重です。一緒に素晴らしいものを作りましょう！🚀🎉 DevFest.AI 2024年10月嬉しいニュースです！2024 年 10 月を通して DevFest.AI に参加します！🗓️このイベント中に Julep に貢献すると、素晴らしい Julep のグッズや景品を獲得するチャンスが得られます! 🎁世界中の開発者とともに AI リポジトリに貢献し、素晴らしいイベントに参加しましょう。この素晴らしい取り組みを企画してくださった DevFest.AI に心から感謝します。[!TIP]
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
- [Step 2: Extract theパネルの説明とストーリーevaluate:](#step-2-extract-the%E3%83%91%E3%83%8D%E3%83%AB%E3%81%AE%E8%AA%AC%E6%98%8E%E3%81%A8%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AA%E3%83%BCevaluate)
    - [Step 3: Execute the Task](#step-3-execute-the-task)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->
導入Julep は、過去のやり取りを記憶し、複雑なタスクを実行できる AI エージェントを作成するためのプラットフォームです。長期記憶を提供し、複数ステップのプロセスを管理します。Julep を使用すると、意思決定、ループ、並列処理、多数の外部ツールや API との統合を組み込んだ複数ステップのタスクを作成できます。多くの AI アプリケーションは、分岐が最小限の、プロンプトと API 呼び出しの単純な線形チェーンに制限されていますが、Julep はより複雑なシナリオを処理できるように構築されています。サポート対象:複雑で多段階のプロセス動的な意思決定並列実行[!TIP]
Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in.簡単な例次のことができる研究 AI エージェントを想像してください。トピックを取り上げ、そのトピックについて100個の検索クエリを考えてみましょう。これらのウェブ検索を並行して実行すると、結果をまとめると、要約をDiscordに送信するIn Julep, this would be a single task under <b>80 lines of code</b> and run <b>fully managed</b> all on its own. All of the steps are executed on Julep's own servers and you don't need to lift a finger. Here's a working example:name: Research Agent

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
Julep is really useful when you want to build AI agents that can maintain context and state over long-term interactions. It's great for designing complex, multi-step workflows and integrating various tools and APIs directly into your agent's processes.この例では、Julep は並列実行を自動的に管理し、失敗したステップを再試行し、API リクエストを再送信し、タスクが完了するまで確実に実行し続けます。主な特徴🧠 **Persistent AI Agents**: Remember context and information over long-term interactions.💾 **Stateful Sessions**: Keep track of past interactions for personalized responses.🔄 **Multi-Step Tasks**: Build complex, multi-step processes with loops and decision-making.⏳ **Task Management**: Handle long-running tasks that can run indefinitely.🛠️ **Built-in Tools**: Use built-in tools and external APIs in your tasks.🔧 **Self-Healing**: Julep will automatically retry failed steps, resend messages, and generally keep your tasks running smoothly.📚 **RAG**: Use Julep's document store to build a system for retrieving と独自のデータを使用します。Julep は、単純なプロンプト応答モデルを超えた AI ユースケースを必要とするアプリケーションに最適です。Julep と LangChain を比較する理由さまざまなユースケースLangChain と Julep は、AI 開発スタック内で異なる重点を置いたツールと考えてください。LangChain は、プロンプトのシーケンスを作成し、AI モデルとのやり取りを管理するのに最適です。多数の事前構築された統合を備えた大規模なエコシステムを備えているため、何かをすぐに立ち上げて実行したい場合に便利です。LangChain は、プロンプトと API 呼び出しの線形チェーンを含む単純なユースケースに適しています。一方、Julep は、長期的なインタラクションを通じて物事を記憶できる永続的な AI エージェントの構築に重点を置いています。エージェントのプロセス内で複数のステップ、意思決定、さまざまなツールや API との直接統合を伴う複雑なタスクが必要な場合に効果を発揮します。永続的なセッションと複雑なタスクを管理するために、ゼロから設計されています。以下のことを必要とする複雑な AI アシスタントの構築を考えている場合には、Julep を使用してください。数日または数週間にわたってユーザーのインタラクションを追跡します。毎日のサマリーの送信やデータ ソースの監視などのスケジュールされたタスクを実行します。以前のやり取りや保存されたデータに基づいて決定を下します。タスクの一部として複数の外部サービスと対話します。そして、Julep は、ゼロから構築する必要なく、これらすべてをサポートするインフラストラクチャを提供します。異なるフォームファクタJulep is a **platform** that includes a language for describing tasks, a server for running those tasks, and an SDK for interacting with the platform. To build something with Julep, you write a description of the task in `YAML`, and then run the task in the cloud.Julep は、負荷の高い、複数のステップから成る、長時間実行されるタスク向けに構築されており、タスクの複雑さに制限はありません。LangChain is a **library** that includes a few tools and a framework for building linear chains of prompts and tools. To build something with LangChain, you typically write Python code that configures and runs the model chains you want to use.LangChain は、プロンプトと API 呼び出しの線形チェーンを含む単純なユースケースでは十分であり、実装も迅速です。要約すればステートレスまたは短期的なコンテキストで AI モデルのインタラクションとプロンプト シーケンスを管理する必要がある場合は、LangChain を使用します。高度なタスク機能、永続的なセッション、複雑なタスク管理を備えたステートフル エージェント用の堅牢なフレームワークが必要な場合は、Julep を選択してください。インストールTo get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):npm install @julep/sdk
またはpip install julep
[!NOTE]
Get your API key [here](https://dashboard-dev.julep.ai).While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.[!TIP]
💻 Are you a _show me the code!™_ kind of person? We have created a ton of cookbooks for you to get started with. **Check out the [cookbooks](https://github.com/julep-ai/julep/tree/dev/cookbooks)** to browse through examples.💡 There's also lots of ideas that you can build on top of Julep. **Check out the [list of ideas](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** to get some inspiration.Python クイックスタート 🐍ステップ1: エージェントを作成するimport yaml
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
ステップ2: ストーリーと漫画を生成するタスクを作成する入力されたアイデアに基づいてストーリーを作成し、パネル化された漫画を生成するためのマルチステップタスクを定義しましょう。# 📋 Task
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

  # Step 2: Extract theパネルの説明とストーリーevaluate:
  story: _.split('1. ')[0].strip()
  panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)ステップ3: 画像生成ツールを使用して各パネルの画像を生成するforeach:
  in: _.panels
  do:
    tool: image_generator
    arguments:
      description: _ステップ4: ストーリーのキャッチーなタイトルを作成するプロンプト：role: system
content: You are {{agent.name}}. {{agent.about}}role: user
content: >
  Based on the story below, generate a catchy title.Story: {{outputs[1].story}}
unwrap: trueステップ5: ストーリー、生成された画像、タイトルを返すreturn:
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
ステップ4: エージェントとチャットするエージェントとの対話型チャット セッションを開始します。session = client.sessions.create(agent_id=agent.id)

# 💬 Send messages to the agent
while (message := input("Enter a message: ")) != "quit":
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )

    print(response)
[!TIP]
You can find the full python example [here](example.py).Node.js クイックスタート 🟩ステップ1: エージェントを作成するimport { Julep } from '@julep/sdk';
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
ステップ2: ストーリーと漫画を生成するタスクを作成するconst taskYaml = `
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
ステップ3: タスクを実行するasync function executeTask(task) {
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
ステップ4: エージェントとチャットするasync function chatWithAgent(agent) {
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
}実行例()。コンソールのエラーをキャッチします。
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
**Agents**: AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users.**Users**: Entities that interact with agents through sessions.**Sessions**: Stateful interactions between agents and users, maintaining context across multiple exchanges.**Tasks**: Multi-step, programmatic workflows that agents can execute, including various types of steps like prompts, tool calls, and conditional logic.**Tools**: Integrations that extend an agent's capabilities, including user-defined functions, system tools, or third-party API integrations.**Documents**: Text or data objects associated with agents or users, vectorized and stored for semantic search and retrieval.**Executions**: Instances of tasks that have been initiated with specific inputs, with their own lifecycle and state machine.For a more detailed explanation of these concepts and their interactions, please refer to our [Concepts Documentation](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md).タスクを理解するタスクは Julep のワークフロー システムの中核です。タスクを使用すると、エージェントが実行できる複雑な複数ステップの AI ワークフローを定義できます。タスク コンポーネントの概要は次のとおりです。**Name and Description**: Each task has a unique name and description for easy identification.**Main Steps**: The core of a task, defining the sequence of actions to be performed.**Tools**: Optional integrations that extend the capabilities of your agent during task execution.ワークフローステップの種類Julep のタスクにはさまざまな種類のステップを含めることができるため、複雑で強力なワークフローを作成できます。利用可能なステップの種類の概要をカテゴリ別にまとめると次のようになります。一般的な手順**Prompt**: SendAI モデルにメッセージを送信し、応答を受け取ります。- prompt: "Analyze the following data: {{data}}"
**Tool Call**: Execute an integrated tool or API.- tool: web_search
  arguments:
    query: "Latest AI developments"
**Evaluate**: Perform calculations or manipulate data.- evaluate:
    average_score: "sum(scores) / len(scores)"
**Wait for Input**: Pause workflow until input is received.- wait_for_input:
    info:
      message: "Please provide additional information."
**Log**: Log a specified value or message.- log: "Processing completed for item {{item_id}}"
キーバリューステップ**Get**: Retrieve a value from a key-value store.- get: "user_preference"
**Set**: Assign a value to a key in a key-value store.- set:
    user_preference: "dark_mode"
反復ステップ**Foreach**: Iterate over a collection and perform steps for each item.- foreach:
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
条件付きステップ**If-Else**: Conditional execution of steps.- if: "score > 0.8"
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
その他の制御フロー**Sleep**: Pause the workflow for a specified duration.- sleep:
    seconds: 30
**Return**: Return a value from the workflow.- return:
    result: "Task completed successfully"
**Yield**: Run a subworkflow and await its completion.- yield:
    workflow: "data_processing_subflow"
    arguments:
      input_data: "{{raw_data}}"
**Error**: Handle errors by specifying an error message.- error: "Invalid input provided"
各ステップ タイプは、高度な AI ワークフローを構築する上で特定の目的を果たします。この分類は、Julep タスクで使用できるさまざまな制御フローと操作を理解するのに役立ちます。高度な機能Julep は、AI ワークフローを強化するためのさまざまな高度な機能を提供します。エージェントへのツールの追加外部ツールと API を統合してエージェントの機能を拡張します。client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {"api_key": "your_brave_api_key"},
    },
)
セッションとユーザーの管理Julep は、永続的なインタラクションのための堅牢なセッション管理を提供します。session = client.sessions.create(
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
ドキュメントの統合と検索エージェントのドキュメントを簡単に管理および検索できます。# Upload a document
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
For more advanced features and detailed usage, please refer to our [Advanced Features Documentation](https://docs.julep.ai/advanced-features).統合Julep は、AI エージェントの機能を拡張するさまざまな統合をサポートしています。利用可能な統合とサポートされている引数のリストは次のとおりです。勇敢な検索setup:
  api_key: string  # The API key for Brave Search

arguments:
  query: string  # The search query for searching with Brave

output:
  result: string  # The result of the Brave Search
ブラウザベースsetup:
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
スパイダーsetup:
  spider_api_key: string  # The API key for Spider

arguments:
  url: string             # The URL for which to fetch data
  mode: string            # The type of crawlers (default: "scrape")
  params: dict            # (Optional) The parameters for the Spider API

output:
  documents: list         # The documents returned from the spider
天気setup:
  openweathermap_api_key: string  # The API key for OpenWeatherMap

arguments:
  location: string                # The location for which to fetch weather data

output:
  result: string                  # The weather data for the specified location
ウィキペディアarguments:
  query: string           # The search query string
  load_max_docs: integer  # Maximum number of documents to load (default: 2)

output:
  documents: list         # The documents returned from the Wikipedia search
These integrations can be used within your tasks to extend the capabilities of your AI agents. For more detailed information on how to use these integrations in your workflows, please refer to our [Integrations Documentation](https://docs.julep.ai/integrations).SDKリファレンス[Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)[Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)APIリファレンスエージェント、タスク、実行の詳細については、包括的な API ドキュメントをご覧ください。[Agents API](https://api.julep.ai/api/docs#tag/agents)[Tasks API](https://api.julep.ai/api/docs#tag/tasks)[Executions API](https://api.julep.ai/api/docs#tag/executions)->> Test <<-
A simple update to text the translation github action