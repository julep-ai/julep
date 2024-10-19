<sup>[English](README.md) | [中文翻译](README-CN.md) | [日本語翻訳](README-JA.md) | [French](README-FR.md)</sup>

<div align="center" id="top">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20AI%20agents%20and%20multi-step%20tasks&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&theme=Auto" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow">探索文档</a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">不和谐</a>
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

---

> [!注意]
> 👨‍💻 来参加 devfest.ai 活动了吗？加入我们的 [Discord](https://discord.com/invite/JTSBGRZrzj) 并查看以下详细信息。
>
> 从[此处](https://dashboard-dev.julep.ai)获取您的 API 密钥。

<details>
<summary><b>🌟 贡献者和 DevFest.AI 参与者</b>（点击展开）</summary>

## 🌟 招募贡献者！

我们很高兴欢迎新贡献者加入 Julep 项目！我们创建了几个“好的第一个问题”来帮助您入门。以下是您可以做出贡献的方式：

1. 查看我们的 [CONTRIBUTING.md](https://github.com/julep-ai/julep/blob/dev/CONTRIBUTING.md) 文件以获取有关如何贡献的指南。
2. 浏览我们的 [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) 以找到您感兴趣的任务。
3. 如果您有任何疑问或需要帮助，请随时通过我们的 [Discord](https://discord.com/invite/JTSBGRZrzj) 频道联系我们。

您的贡献，无论大小，对我们来说都是宝贵的。让我们一起创造一些了不起的东西！🚀

### 🎉 DevFest.AI 2024 年 10 月

令人兴奋的消息！我们将参加 2024 年 10 月的 DevFest.AI！🗓️

- 在本次活动期间为 Julep 做出贡献，就有机会赢得超棒的 Julep 商品和赃物！🎁
- 与来自世界各地的开发人员一起为 AI 资源库做出贡献并参与精彩的活动。
- 非常感谢 DevFest.AI 组织这次精彩的活动！

> [!提示]
> 准备好加入这场有趣的活动了吗？**[发推文表示你正在参与](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** 让我们开始编码吧！🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 目录</h3>

- [简介](#introduction)
- [主要特点](#key-features)
- [快速示例](#quick-example)
- [安装](#安装)
- [Python 快速入门 🐍](#python-quick-start-)
- [步骤 1：创建代理](#step-1-create-an-agent)
- [步骤 2：创建一个生成故事和漫画的任务](#step-2-create-a-task-that-generates-a-story-and-comic-strip)
- [步骤 3：执行任务](#step-3-execute-the-task)
- [步骤 4：与代理聊天](#step-4-chat-with-the-agent)
- [Node.js 快速入门🟩](#nodejs-quick-start-)
- [步骤 1：创建代理](#step-1-create-an-agent-1)
- [步骤 2：创建一个生成故事和漫画的任务](#step-2-create-a-task-that-generates-a-story-and-comic-strip-1)
- [步骤 3：执行任务](#step-3-execute-the-task-1)
- [步骤 4：与代理聊天](#step-4-chat-with-the-agent-1)
- [组件](#components)
- [心智模型](#mental-model)
- [概念](#concepts)
- [理解任务](#understanding-tasks)
- [工作流步骤的类型](#types-of-workflow-steps)
- [工具类型](#tool-types)
- [用户定义的`函数`](#user-defined-functions)
- [`系统` 工具](#system-tools)
- [内置 `integrations`](#built-in-integrations)
-[直接`api_calls`]（#direct-api_calls）
- [集成](#integrations)
- [其他功能](#other-features)
- [向代理添加工具](#adding-tools-to-agents)
- [管理会话和用户](#managing-sessions-and-users)
- [文档集成与搜索](#document-integration-and-search)
- [本地快速启动](#local-quickstart)
- [SDK 参考](#sdk-reference)
- [API 参考](#api-reference)
- [为什么 Julep 与 LangChain？](#why-julep-vs-langchain)
- [不同用例](#different-use-cases)
- [不同的外形尺寸](#different-form-factor)
- [总结](#in-summary)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

＃＃ 介绍

Julep 是一个用于创建 AI 代理的平台，这些代理可以记住过去的互动并执行复杂的任务。它提供长期记忆并管理多步骤流程。

Julep 支持创建多步骤任务，包括决策、循环、并行处理以及与众多外部工具和 API 的集成。

尽管许多 AI 应用程序仅限于简单、线性的提示和 API 调用链，并且分支很少，但 Julep 可以处理更复杂的场景，这些场景包括：

- 有多个步骤，
- 根据模型输出做出决策，
- 产生并行分支，
- 使用多种工具，并且
- 长时间运行。

> [!提示]
> 想象一下，您想要构建一个 AI 代理，它不仅可以回答简单的问题，还可以处理复杂的任务、记住过去的交互，甚至可能使用其他工具或 API。这就是 Julep 的作用所在。阅读 [了解任务](#understanding-tasks) 了解更多信息。

## 主要特点

1. 🧠 **持久 AI 代理**：在长期交互​​中记住上下文和信息。
2. 💾 **状态会话**：跟踪过去的互动以获得个性化回应。
3. 🔄 **多步骤任务**：通过循环和决策构建复杂的多步骤流程。
4. ⏳ **任务管理**：处理可以无限期运行的长时间运行的任务。
5.🛠️**内置工具**：在您的任务中使用内置工具和外部 API。
6. 🔧 **自我修复**：Julep 将自动重试失败的步骤、重新发送消息，并确保您的任务顺利运行。
7. 📚 **RAG**：使用 Julep 的文档存储构建一个用于检索和使用您自己的数据的系统。

![功能](https://github.com/user-attachments/assets/4355cbae-fcbd-4510-ac0d-f8f77b73af70)

> [!提示]
> Julep 非常适合需要超越简单的提示响应模型的 AI 用例的应用程序。

快速示例

想象一下一个可以执行以下操作的研究 AI 代理：

1. **选择一个主题**，
2. 针对该主题提出 100 个搜索查询，
3. 同时进行网页搜索，
4. **总结**结果，
5. 将**摘要发送至 Discord**。

> [!注意]
> 在 Julep 中，这将是一项单独的任务<b>80行代码</b>然后运行<b>完全托管</b>全部独立完成。所有步骤都在 Julep 自己的服务器上执行，您无需动手。

这是一个有效的例子：

```yaml
name: Research Agent

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
        api_key: BSAqES7dj9d...  # dummy key

  - name: discord_webhook
    type: api_call
    api_call:
      url: https://eobuxj02se0n.m.pipedream.net  # dummy requestbin
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
    parallelism: 10

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
    settings:
      model: gpt-4o-mini

  # Send the summary to Discord
  - tool: discord_webhook
    arguments:
      content: |-
        f'''
        **Research Summary for {inputs[0].topic}**

        {_}
        '''
```

在这个例子中，Julep 将自动管理并行执行，重试失败的步骤，重新发送 API 请求，并保持任务可靠运行直到完成。

> 这在 30 秒内运行并返回以下输出：

<details>
<summary><b>人工智能研究摘要</b> <i>（点击展开）</i></summary>

> **人工智能研究摘要**
> 
>###人工智能（AI）研究成果摘要
> 
> #### 简介
> 近年来，人工智能 (AI) 领域取得了重大进展，其特点是方法和技术的发展，使机器能够感知环境、从数据中学习并做出决策。本摘要主要关注从与 AI 相关的各种研究成果中获得的见解。
> 
> #### 主要发现
> 
> 1. **人工智能的定义和范围**：
> - 人工智能被定义为计算机科学的一个分支，专注于创建能够执行需要类似人类智能的任务的系统，包括学习、推理和解决问题（维基百科）。
>——它涵盖了各种子领域，包括机器学习、自然语言处理、机器人和计算机视觉。
> 
> 2. **影响与应用**：
> - AI 技术正在融入众多领域，提高效率和生产力。应用范围从自动驾驶汽车和医疗诊断到客户服务自动化和财务预测（OpenAI）。
> - 谷歌致力于让人工智能造福每个人，这凸显了其通过增强各个平台的用户体验（谷歌人工智能）显著改善日常生活的潜力。
> 
> 3. **道德考虑**：
> - 关于人工智能的伦理影响的讨论一直在进行中，包括对隐私、偏见和决策过程中的责任的担忧。强调需要一个确保安全和负责任地使用人工智能技术的框架（OpenAI）。
> 
> 4. **学习机制**：
> - AI 系统利用不同的学习机制，例如监督学习、无监督学习和强化学习。这些方法允许 AI 通过从过去的经验和数据中学习来提高性能（维基百科）。
> - 监督学习和无监督学习之间的区别至关重要；监督学习依赖于标记数据，而无监督学习则识别没有预定义标签的模式（无监督）。
> 
> 5. **未来方向**：
> - 未来人工智能的发展预计将专注于增强人工智能系统的可解释性和透明度，确保它们能够提供合理的决策和行动（OpenAI）。
> - 人们还在努力使人工智能系统更易于访问和用户友好，鼓励不同人群和行业更广泛地采用它（谷歌人工智能）。
> 
> #### 结论
> 人工智能代表着跨多个领域的变革力量，有望重塑行业并改善生活质量。然而，随着其能力的扩展，解决随之而来的伦理和社会影响至关重要。技术专家、伦理学家和政策制定者之间的持续研究和合作对于驾驭人工智能的未来格局至关重要。

</details>

＃＃ 安装

要开始使用 Julep，请使用 [npm](https://www.npmjs.com/package/@julep/sdk) 或 [pip](https://pypi.org/project/julep/) 安装它：

**Node.js**：
```bash
npm install @julep/sdk

# or

bun add @julep/sdk
```

**Python**：
```bash
pip install julep
```

> [!注意]
> 从[此处](https://dashboard-dev.julep.ai)获取您的 API 密钥。
>
> 虽然我们处于测试阶段，但您也可以通过 [Discord](https://discord.com/invite/JTSBGRZrzj) 联系，以解除 API 密钥的速率限制。

> [!提示]
> 💻 你是“向我展示代码！”的那种人吗？我们创建了大量的烹饪书供您入门。**查看 [烹饪书](https://github.com/julep-ai/julep/tree/dev/cookbooks)** 以浏览示例。
>
> 💡 您还可以在 Julep 的基础上构建许多想法。**查看[想法列表](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** 以获取一些灵感。

## Python 快速入门🐍

```python
### Step 0: Setup

import time
import yaml
from julep import Julep # or AsyncJulep

client = Julep(api_key="your_julep_api_key")

### Step 1: Create an Agent

agent = client.agents.create(
    name="Storytelling Agent",
    model="claude-3.5-sonnet",
    about="You are a creative storyteller that crafts engaging stories on a myriad of topics.",
)

### Step 2: Create a Task that generates a story and comic strip

task_yaml = """
name: Storyteller
description: Create a story based on an idea.

tools:
  - name: research_wikipedia
    integration:
      provider: wikipedia
      method: search

main:
  # Step 1: Generate plot idea
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', generate a list of 5 plot ideas. Go crazy and be as creative as possible. Return your output as a list of long strings inside ```yaml 标签位于您的回复末尾。
展开：true

- 评价：
情节想法：load_yaml（_.split（'```yaml')[1].split('```')[0].strip())

# 第二步：从情节思路中提取研究领域
- 迅速的：
- 角色：系统
内容：您是 {{agent.name}}。{{agent.about}}
- 角色：用户
内容: >
以下是一些故事情节的想法：
{% 表示 _.plot_ideas 中的想法 %}
- {{主意}}
{% 结束 %}

为了发展故事情节，我们需要研究情节思路。
我们应该研究什么？写下你认为有趣的情节想法的维基百科搜索查询。
将输出作为 yaml 列表返回```yaml tags at the end of your response.
    unwrap: true
    settings:
      model: gpt-4o-mini
      temperature: 0.7

  - evaluate:
      research_queries: load_yaml(_.split('```yaml')[1].split('```')[0].strip())

  # Step 3: Research each plot idea
  - foreach:
      in: _.research_queries
      do:
        tool: research_wikipedia
        arguments:
          query: _

  - evaluate:
      wikipedia_results: 'NEWLINE.join([f"- {doc.metadata.title}: {doc.metadata.summary}" for item in _ for doc in item.documents])'

  # Step 4: Think and deliberate
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: |-
          Before we write the story, let's think and deliberate. Here are some plot ideas:
          {% for idea in outputs[1].plot_ideas %}
          - {{idea}}
          {% endfor %}
          
          Here are the results from researching the plot ideas on Wikipedia:
          {{_.wikipedia_results}}

          Think about the plot ideas critically. Combine the plot ideas with the results from Wikipedia to create a detailed plot for a story.
          Write down all your notes and thoughts.
          Then finally write the plot as a yaml object inside ```yaml 标签位于响应末尾。yaml 对象应具有以下结构：

          ```yaml
          title: "<string>"
          characters:
          - name: "<string>"
            about: "<string>"
          synopsis: "<string>"
          scenes:
          - title: "<string>"
            description: "<string>"
            characters:
            - name: "<string>"
              role: "<string>"
            plotlines:
            - "<string>"```

确保 yaml 有效，且角色和场景不为空。还要注意分号和编写 yaml 的其他问题。
展开：true

- 评价：
情节：“load_yaml（_.split（'```yaml')[1].split('```')[0].strip())”
"""

任务 = 客户端.任务.创建（
agent_id=代理.id，
**yaml.safe_load（任务_yaml）
)

### 步骤 3：执行任务

执行 = 客户端.执行.创建（
任务ID=任务ID，
输入={“idea”：“一只学飞的猫”}
)

# 🎉 观看故事和漫画面板的生成
while (result := client.executions.get(execution.id)).status 不在 ['成功', '失败'] 中：
打印（结果.状态，结果.输出）
时间.睡眠(1)

# 📦执行完成后，检索结果
如果 result.status ==“成功”：
打印（结果.输出）
别的：
引发异常（结果.错误）
```

You can find the full python example [here](example.py).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Node.js Quick Start 🟩

### Step 1: Create an Agent

```JavaScript的
// 步骤 0：设置
const dotenv = require（'dotenv'）；
const { Julep } = require('@julep/sdk');
const yaml = require（'yaml'）；

dotenv.配置（）；

const 客户端 = new Julep（{ apiKey：process.env.JULEP_API_KEY， 环境：process.env.JULEP_ENVIRONMENT || “生产” }）；

/* 步骤 1：创建代理 */

异步函数 createAgent() {
const 代理 = 等待客户端.代理.创建（{
名称：“讲故事特工”，
模型：“claude-3.5-sonnet”，
关于：“您是一位富有创意的讲故事者，能够就无数主题创作引人入胜的故事。”，
  });
回報代理；
}

/* 步骤 2：创建一个生成故事和漫画的任务 */

const taskYaml = `
名称：讲故事的人
描述：根据一个想法创建一个故事。

工具：
- 名称：research_wikipedia
一体化：
提供者：维基百科
方法：搜索

主要的：
# 步骤 1：产生情节想法
- 迅速的：
- 角色：系统
内容：您是 {{agent.name}}。{{agent.about}}
- 角色：用户
内容: >
根据想法“{{_.idea}}”，生成 5 个情节想法的列表。尽情发挥你的想象力和创造力。将输出作为响应末尾的 \`\`\`yaml 标签内的长字符串列表返回。
展开：true

- 评价：
plot_ideas：load_yaml（_.split（'\`\`\`yaml'）[1].split（'\`\`\`'）[0].strip（））

# 第二步：从情节思路中提取研究领域
- 迅速的：
- 角色：系统
内容：您是 {{agent.name}}。{{agent.about}}
- 角色：用户
内容: >
以下是一些故事情节的想法：
{% 表示 _.plot_ideas 中的想法 %}
- {{主意}}
{% 结束 %}

为了发展故事情节，我们需要研究情节思路。
我们应该研究什么？写下你认为有趣的情节想法的维基百科搜索查询。
将您的输出作为 yaml 列表返回到响应末尾的 \`\`\`yaml 标签内。
展开：true
设置：
型号：gpt-4o-mini
温度：0.7

- 评价：
research_queries：load_yaml（_.split（'\`\`\`yaml'）[1].split（'\`\`\`'）[0].strip（））

# 步骤 3：研究每个情节构思
- foreach：
在：_.research_queries
做：
工具：research_wikipedia
参数：
询问： _

- 评价：
wikipedia_results：'NEWLINE.join（[f“- {doc.metadata.title}：{doc.metadata.summary}”用于 item in _ for doc in item.documents]）'

# 第 4 步：思考和深思
- 迅速的：
- 角色：系统
内容：您是 {{agent.name}}。{{agent.about}}
- 角色：用户
内容：|-
在写故事之前，让我们先思考一下。以下是一些情节构思：
{% for idea in output[1].plot_ideas %}
- {{主意}}
{% 结束 %}

以下是在维基百科上研究情节思路的结果：
{{_.wikipedia_results}}

认真思考故事情节。将故事情节与维基百科搜索结果相结合，为故事创建详细情节。
写下你所有的笔记和想法。
最后，将图表作为 yaml 对象写入响应末尾的 \`\`\`yaml 标签内。yaml 对象应具有以下结构：

\`\`\`yaml
标题： ”<string>"
人物：
- 姓名： ”<string>"
关于： ”<string>"
概要：”<string>"
场景：
- 标题： ”<string>"
描述： ”<string>"
人物：
- 姓名： ”<string>"
角色： ”<string>"
故事情节：
-”<string>“\`\`\`

确保 yaml 有效，且角色和场景不为空。还要注意分号和编写 yaml 的其他问题。
展开：true

- 评价：
情节：“load_yaml（_。split（'\`\`\`yaml'）[1].split（'\`\`\`'）[0].strip（））”
`;

异步函数 createTask（agentId）{
const task = await 客户端.tasks.create(
代理人编号，
yaml.解析（taskYaml）
（英文）：
返回任务；
}

/* 步骤 3：执行任务 */

异步函数 executeTask (taskId) {
const 执行 = 等待客户端.执行.创建（taskId，{
输入：{ 想法：“一只学飞的猫” }
  });

// 🎉 观看故事和漫画面板的生成
while (真) {
const result = 等待客户端.executions.get（execution.id）;
控制台.log（结果.状态，结果.输出）；

if (result.status === '成功' || result.status === '失败') {
// 📦执行完成后，检索结果
如果 (result.status === "成功") {
控制台.log（结果.输出）；
} 别的 {
抛出新的错误（result.error）；
      }
休息;
    }

等待新的 Promise（resolve => setTimeout（resolve，1000））；
  }
}

// 运行示例的主函数
异步函数 main() {
尝试 {
const agent = await createAgent();
const task = await createTask(agent.id);
等待执行任务（任务id）；
} 捕获 (错误) {
console.error("发生错误：", error);
  }
}

main().then(() => console.log("完成")).catch(console.error);
```

You can find the full Node.js example [here](example.js).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

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

   - You can use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.

2. **Julep Backend Service:**

   - The SDK communicates with the Julep backend over the network.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.

## Concepts

Julep is built on several key technical components that work together to create powerful AI workflows:

```美人鱼
图 TD
用户[用户] ==> 会话[会话]
会话-->代理[代理]
代理-->任务[任务]
代理——> LLM[大型语言模型]
任务 --> 工具[工具]
代理人 --> 文件[文件]
文档 --> VectorDB[矢量数据库]
任务 --> 执行[执行]

classDef 客户端填充：#9ff，描边：#333，描边宽度：1px；
用户客户端类；

classDef 核心填充：#f9f，描边：#333，描边宽度：2px；
类代理、任务、会话核心；
```

- **Agents**: AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users.
- **Users**: Entities that interact with agents through sessions.
- **Sessions**: Stateful interactions between agents and users, maintaining context across multiple exchanges.
- **Tasks**: Multi-step, programmatic workflows that agents can execute, including various types of steps like prompts, tool calls, and conditional logic.
- **Tools**: Integrations that extend an agent's capabilities, including user-defined functions, system tools, or third-party API integrations.
- **Documents**: Text or data objects associated with agents or users, vectorized and stored for semantic search and retrieval.
- **Executions**: Instances of tasks that have been initiated with specific inputs, with their own lifecycle and state machine.


<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Understanding Tasks

Tasks are the core of Julep's workflow system. They allow you to define complex, multi-step AI workflows that your agents can execute. Here's a brief overview of task components:

- **Name, Description and Input Schema**: Each task has a unique name and description for easy identification. An input schema (optional) that is used to validate the input to the task.
- **Main Steps**: The core of a task, defining the sequence of actions to be performed. Each step can be a prompt, tool call, evaluate, wait_for_input, log, get, set, foreach, map_reduce, if-else, switch, sleep, or return. (See [Types of Workflow Steps](#types-of-workflow-steps) for more details)
- **Tools**: Optional integrations that extend the capabilities of your agent during task execution.

### Lifecycle of a Task

You create a task using the Julep SDK and specify the main steps that the agent will execute. When you execute a task, the following lifecycle happens:

```美人鱼
顺序图
参与者 D 作为您的代码
参与者 C 作为 Julep 客户
参与者 S 担任 Julep 服务器

D->>C：创建任务
C->>S：提交执行
注意 S：执行任务
S 注释：管理状态
S-->>C：执行事件
C-->>D：进度更新
S->>C：执行完成
C->>D：最终结果
```

### Types of Workflow Steps

Tasks in Julep can include various types of steps, allowing you to create complex and powerful workflows. Here's an overview of the available step types:

#### Common Steps

<table>
<tr>
    <th>Name</th>
    <th>About</th>
    <th>Syntax</th>
</tr>
<tr>
<td> <b>Prompt</b> </td>
<td>
Send a message to the AI model and receive a response
<br><br><b>Note:</b> The prompt step uses Jinja templates and you can access context variables in them.
</td>

<td>

```yaml
- prompt: "分析以下数据：{{agent.name}}" # <-- 这是一个 jinja 模板
```

```yaml
- 迅速的：
- 角色：系统
内容：“您是 {{agent.name}}。 {{agent.about}}”
- 角色：用户
内容：“分析以下数据：{{_.data}}”
```

</td>
</tr>
<tr>
<td> <b>Tool Call</b> </td>
<td>
Execute an integrated tool or API that you have previously declared in the task.
<br><br><b>Note:</b> The tool call step uses Python expressions inside the arguments.

</td>

<td>

```yaml
- 工具：web_search
参数：
查询：“最新的 AI 发展”#<- 这是一个 Python 表达式（注意引号）
num_results: len(_.topics) # <-- 用于访问列表长度的 Python 表达式
```

</td>
</tr>
<tr>
<td> <b>Evaluate</b> </td>
<td>
Perform calculations or manipulate data
<br><br><b>Note:</b> The evaluate step uses Python expressions.
</td>

<td>

```yaml
- 评价：
平均分数：总分（分数）/长度（分数）
```

</td>
</tr>
<tr>
<td> <b>Wait for Input</b> </td>
<td>
Pause workflow until input is received. It accepts an `info` field that can be used by your application to collect input from the user.

<br><br><b>Note:</b> The wait_for_input step is useful when you want to pause the workflow and wait for user input e.g. to collect a response to a prompt.

</td>

<td>

```yaml
-等待输入：
信息：
消息：'“请提供有关 {_.required_info} 的其他信息。”' # <-- 用于访问上下文变量的 python 表达式
```

</td>
</tr>
<tr>
<td> <b>Log</b> </td>
<td>
Log a specified value or message.

<br><br><b>Note:</b> The log step uses Jinja templates and you can access context variables in them.

</td>

<td>

```yaml
- log：“项目 {{_.item_id}} 的处理已完成”#<-- jinja 模板用于访问上下文变量
```

</td>
</tr>
</table>

#### Key-Value Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Get</b> </td>
<td>
Retrieve a value from the execution's key-value store.

</td>

<td>

```yaml
- 获取：用户偏好
```

</td>
</tr>
<tr>
<td> <b>Set</b> </td>
<td>
Assign a value to a key in the execution's key-value store.

<br><br><b>Note:</b> The set step uses Python expressions.
</td>

<td>

```yaml
- 放：
user_preference: '"dark_mode"' # <-- python 表达式
```

</td>
</tr>
</table>

#### Iteration Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Foreach</b> </td>
<td>
Iterate over a collection and perform steps for each item

</td>

<td>

```yaml
- foreach：
in: _.data_list # <-- 用于访问上下文变量的 python 表达式
做：
- log: "处理项目 {{_.item}}" # <-- jinja 模板访问上下文变量
```

</td>
</tr>
<tr>
<td> <b>Map-Reduce</b> </td>
<td>
Map over a collection and reduce the results

</td>

<td>

```yaml
- 映射_减少：
over: _.numbers # <-- 用于访问上下文变量的 python 表达式
地图：
- 评价：
平方：“_ ** 2”
reduce：results + [_] # <--（可选）python 表达式以减少结果。如果省略，则为默认值。
```

```yaml
- 映射_减少：
结束：_.topics
地图：
- 提示：写一篇关于{{__}}的文章
并行度：10
```

</td>
</tr>
<tr>
<td> <b>Parallel</b> </td>
<td>
Run multiple steps in parallel

</td>

<td>

```yaml
- 平行线：
- 工具：web_search
参数：
查询：“AI 新闻”
- 工具：weather_check
参数：
地点：“纽约”
```

</td>
</tr>
</table>

#### Conditional Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>If-Else</b> </td>
<td>
Conditional execution of steps

</td>

<td>

```yaml
- if: _.score > 0.8 # <-- python 表达式
然后：
- 日志：取得高分
别的：
- 错误：分数需要提高
```

</td>
</tr>
<tr>
<td> <b>Switch</b> </td>
<td>
Execute steps based on multiple conditions

</td>

<td>

```yaml
- 转变：
- 案例：_.category =='A'
然后：
- 日志：“A 类处理”
- 案例：_.category =='B'
然后：
- 日志：“B类处理”
- case: _ # 默认情况
然后：
- 错误：未知类别
```

</td>
</tr>
</table>

#### Other Control Flow

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Sleep</b> </td>
<td>
Pause the workflow for a specified duration

</td>

<td>

```yaml
- 睡觉：
秒：30
# 分钟：1
#小时数：1
#天数：1
```

</td>
</tr>
<tr>
<td> <b>Return</b> </td>
<td>
Return a value from the workflow

<br><br><b>Note:</b> The return step uses Python expressions.

</td>

<td>

```yaml
- 返回：
result: '“任务成功完成”' #<-- python 表达式
时间：datetime.now().isoformat() # <-- python 表达式
```

</td>
</tr>
<tr>
<td> <b>Yield</b> </td>
<td>
Run a subworkflow and await its completion

</td>

<td>

```yaml
- 屈服：
工作流程：process_data
参数：
输入数据：_.raw_data # <-- python 表达式
```

</td>
</tr>
</tr>
<tr>
<td> <b>Error</b> </td>
<td>
Handle errors by specifying an error message

</td>

<td>

```yaml
- 错误：“提供的输入无效”#<-- 仅限字符串
```

</td>
</tr>
</table>

Each step type serves a specific purpose in building sophisticated AI workflows. This categorization helps in understanding the various control flows and operations available in Julep tasks.

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Tool Types

Agents can be given access to a number of "tools" -- any programmatic interface that a foundation model can "call" with a set of inputs to achieve a goal. For example, it might use a `web_search(query)` tool to search the Internet for some information.

Unlike agent frameworks, julep is a _backend_ that manages agent execution. Clients can interact with agents using our SDKs. julep takes care of executing tasks and running integrations.

Tools in julep can be one of:
1. **User-defined `functions`**: These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. They need to be handled by the client. The workflow will pause until the client calls the function and gives the results back to julep.
2. **`system` tools**: Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.
3. **`integrations`**: Built-in third party tools that can be used to extend the capabilities of your agents.
4. **`api_calls`**: Direct api calls during workflow executions as tool calls.

### User-defined `functions`

These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. An example:

```yaml
名称：示例系统工具任务
描述：使用系统调用列出代理

工具：
- 名称：send_notification
描述：向用户发送通知
类型：函数
功能：
参数：
类型：对象
特性：
文本：
类型：字符串
描述：通知内容

主要的：
- 工具：send_notification
参数：
内容：'“hi”'#<--python 表达式
```

Whenever julep encounters a _user-defined function_, it pauses, giving control back to the client and waits for the client to run the function call and give the results back to julep.

> [!TIP]
> **Example cookbook**: [cookbooks/13-Error_Handling_and_Recovery.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/13-Error_Handling_and_Recovery.py)

### `system` tools

Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.  

`system` tools are built into the backend. They get executed automatically when needed. They do _not_ require any action from the client-side.

For example,

```yaml
名称：示例系统工具任务
描述：使用系统调用列出代理

工具：
- 名称：list_agent_docs
描述：列出给定代理的所有文档
类型：系统
系统：
资源：代理
子资源：doc
操作：列表

主要的：
- 工具：list_agents
参数：
限制：10 #<-- python 表达式
```

#### Available `system` resources and operations

- `agent`:
  - `list`: List all agents.
  - `get`: Get a single agent by id.
  - `create`: Create a new agent.
  - `update`: Update an existing agent.
  - `delete`: Delete an existing agent.

- `user`:
  - `list`: List all users.
  - `get`: Get a single user by id.
  - `create`: Create a new user.
  - `update`: Update an existing user.
  - `delete`: Delete an existing user.

- `session`:
  - `list`: List all sessions.
  - `get`: Get a single session by id.
  - `create`: Create a new session.
  - `update`: Update an existing session.
  - `delete`: Delete an existing session.
  - `chat`: Chat with a session.
  - `history`: Get the chat history with a session.

- `task`:
  - `list`: List all tasks.
  - `get`: Get a single task by id.
  - `create`: Create a new task.
  - `update`: Update an existing task.
  - `delete`: Delete an existing task.

- `doc` (subresource for `agent` and `user`):
  - `list`: List all documents.
  - `create`: Create a new document.
  - `delete`: Delete an existing document.
  - `search`: Search for documents.

Additional operations available for some resources:
- `embed`: Embed a resource (specific resources not specified in the provided code).
- `change_status`: Change the status of a resource (specific resources not specified in the provided code).
- `chat`: Chat with a resource (specific resources not specified in the provided code).
- `history`: Get the chat history with a resource (specific resources not specified in the provided code).
- `create_or_update`: Create a new resource or update an existing one (specific resources not specified in the provided code).

Note: The availability of these operations may vary depending on the specific resource and implementation details.

> [!TIP]
> **Example cookbook**: [cookbooks/10-Document_Management_and_Search.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/10-Document_Management_and_Search.py)

### Built-in `integrations`

Julep comes with a number of built-in integrations (as described in the section below). `integration` tools are directly executed on the julep backend. Any additional parameters needed by them at runtime can be set in the agent/session/user's `metadata` fields.

See [Integrations](#integrations) for details on the available integrations.

> [!TIP]
> **Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)


### Direct `api_calls`

julep can also directly make api calls during workflow executions as tool calls. Same as `integration`s, additional runtime parameters are loaded from `metadata` fields.

For example,

```yaml
名称：示例 api_call 任务
工具：
- 类型：api_call
名字：你好
API调用：
方法：GET
网址：https://httpbin.org/get

主要的：
- 工具：你好
参数：
json：
测试：_.input#<--python 表达式
```

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Integrations

Julep supports various integrations that extend the capabilities of your AI agents. Here's a list of available integrations and their supported arguments:

<table>

<tr>
<td> <b>Brave Search</b> </td>
<td>

```yaml
设置：
api_key: string # Brave Search 的 API 密钥

参数：
query: string # 使用 Brave 搜索的搜索查询

输出：
result: string # Brave Search 的结果
```

</td>

<td>

**Example cookbook**: [cookbooks/03-SmartResearcher_With_WebSearch.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/03-SmartResearcher_With_WebSearch.ipynb)

</td>
</tr>
<tr>
<td> <b>BrowserBase</b> </td>
<td>

```yaml
设置：
api_key: string # BrowserBase 的 API 密钥
project_id: string # BrowserBase 的项目 ID
session_id: string #（可选）BrowserBase 的会话 ID

参数：
urls: list[string] # 使用 BrowserBase 加载的 URL

输出：
documents: list # 从 URL 加载的文档
```

</td>

</tr>
<tr>
<td> <b>Email</b> </td>
<td>

```yaml
设置：
host: string # 电子邮件服务器的主机
port: integer # 电子邮件服务器的端口
用户：string#电子邮件服务器的用户名
password: string # 邮件服务器的密码

参数：
to: string # 要发送电子邮件到的电子邮件地址
from: string # 发送电子邮件的电子邮件地址
subject: string # 电子邮件的主题
body: string # 电子邮件正文

输出：
success: boolean # 邮件是否发送成功
```

</td>

<td>

**Example cookbook**: [cookbooks/00-Devfest-Email-Assistant.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/00-Devfest-Email-Assistant.ipynb)

</td>
</tr>
<tr>
<td> <b>Spider</b> </td>
<td>

```yaml
设置：
spider_api_key: string # Spider 的 API 密钥

参数：
url: string # 获取数据的 URL
mode: string # 爬虫的类型（默认值：“scrape”）
params: dict # （可选）Spider API 的参数

输出：
documents: list # 蜘蛛返回的文档
```

</td>

<td>

**Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)

</td>
</tr>
<tr>
<td> <b>Weather</b> </td>
<td>

```yaml
设置：
openweathermap_api_key: string # OpenWeatherMap 的 API 密钥

参数：
location: string # 获取天气数据的位置

输出：
result: string # 指定位置的天气数据
```

</td>

<td>

**Example cookbook**: [cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb)

</td>
</tr>
</tr>
<tr>
<td> <b>Wikipedia</b> </td>
<td>

```yaml
参数：
query: string # 搜索查询字符串
load_max_docs：整数#要加载的最大文档数（默认值：2）

输出：
documents: list # 从 Wikipedia 搜索返回的文档
```

</td>

<td>

**Example cookbook**: [cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb)

</td>
</tr>
</table>

For more details, refer to our [Integrations Documentation](#integrations).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Other Features

Julep offers a range of advanced features to enhance your AI workflows:

### Adding Tools to Agents

Extend your agent's capabilities by integrating external tools and APIs:

```Python
客户端.代理.工具.创建（
agent_id=代理.id，
名称="web_search",
description="在网络上搜索信息。",
积分={
“提供者”：“勇敢”，
“方法”：“搜索”，
“设置”：{“api_key”：“你的brave_api_key”}，
}，
)
```

### Managing Sessions and Users

Julep provides robust session management for persistent interactions:

```Python
会话 = 客户端.会话.创建（
agent_id=代理.id，
用户 ID=用户 ID，
context_overflow="自适应"
)

# 在同一会话中继续对话
响应 = 客户端.会话.聊天（
session_id=会话id，
消息=[
      {
“角色”：“用户”，
"content": "跟进之前的对话。"
      }
    ]
)
```

### Document Integration and Search

Easily manage and search through documents for your agents:

```Python
# 上传文档
文档 = 客户端.代理.docs.创建（
title="人工智能进步",
content="人工智能正在改变世界...",
元数据={“category”：“research_paper”}
)

# 搜索文档
结果 = 客户端.代理.docs.搜索（
text="AI 进步",
metadata_filter={“category”：“research_paper”}
)
```

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

＃＃ 参考

### SDK 参考

- **Node.js** [SDK 参考](https://github.com/julep-ai/node-sdk/blob/main/api.md) | [NPM 包](https://www.npmjs.com/package/@julep/sdk)
- **Python** [SDK 参考](https://github.com/julep-ai/python-sdk/blob/main/api.md) | [PyPI 包](https://pypi.org/project/julep/)

### API 参考

浏览我们的 API 文档以了解有关代理、任务和执行的更多信息：

- [代理 API](https://dev.julep.ai/api/docs#tag/agents)
- [任务 API]（https://dev.julep.ai/api/docs#tag/tasks）
- [执行 API](https://dev.julep.ai/api/docs#tag/executions)

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## 本地快速启动

**要求**：

- 安装了最新的docker compose

**步骤**：

1. `git 克隆 https://github.com/julep-ai/julep.git`
2. `cd julep`
3. `docker 卷创建 cozo_backup`
4. `docker 卷创建 cozo_data`
5. `cp .env.example .env # <-- 编辑此文件`
6. `docker compose --env-file .env --profile temporary-ui --profile single-tenant --profile self-hosted-db up --build`

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>


*****

## Julep 和 LangChain 等有什么区别？

### 不同的用例

可以将 LangChain 和 Julep 视为 AI 开发堆栈中具有不同重点的工具。

LangChain 非常适合创建提示序列和管理与 LLM 的交互。它拥有庞大的生态系统，包含大量预构建的集成，如果您想快速启动和运行某些功能，这会非常方便。LangChain 非常适合涉及线性提示链和 API 调用的简单用例。

另一方面，Julep 更侧重于构建持久的 AI 代理，这些代理可以在长期交互​​中保持上下文。当您需要涉及多步骤任务、条件逻辑以及在代理流程中直接与各种工具或 API 集成的复杂工作流时，它会大放异彩。它从头开始设计，以管理持久会话和复杂的工作流。

如果您想构建一个需要执行以下操作的复杂 AI 助手，请使用 Julep：

- 跟踪几天或几周内的用户互动。
- 执行计划任务，例如发送每日摘要或监控数据源。
- 根据之前的互动或存储的数据做出决策。
- 作为其工作流程的一部分与多个外部服务进行交互。

然后 Julep 提供支持所有这些的基础设施，而无需您从头开始构建。

### 不同的外形尺寸

Julep 是一个**平台**，其中包括用于描述工作流的语言、用于运行这些工作流的服务器以及用于与平台交互的 SDK。要使用 Julep 构建某些东西，您需要在“YAML”中编写工作流描述，然后在云中运行工作流。

Julep 专为繁重、多步骤和长时间运行的工作流程而构建，并且工作流程的复杂程度没有限制。

LangChain 是一个**库**，其中包含一些工具和一个用于构建线性提示和工具链的框架。为了使用 LangChain 构建某些东西，您通常需要编写 Python 代码来配置和运行要使用的模型链。

对于涉及线性提示和 API 调用链的简单用例，LangChain 可能足够并且能够更快地实现。

＃＃＃ 总之

当您需要在无状态或短期环境中管理 LLM 交互和提示序列时，请使用 LangChain。

当您需要一个具有高级工作流功能、持久会话和复杂任务编排的状态代理的强大框架时，请选择 Julep。

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>
