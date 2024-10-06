<sup>[English](README.md) | 中文 | [日本語](README-JP.md)</sup>

<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Build%20AI%20agents%20and%20workflows%20with%20a%20simple%20API&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow"><strong>探索文档</strong></a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">领英</a>
</p>


<p align="center">
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM 版本"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - 版本"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker 镜像版本"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub 许可证"></a>
</p>

*****

> [!TIP]
> 👨‍💻 来参加 devfest.ai 活动？加入我们的 [Discord](https://discord.com/invite/JTSBGRZrzj) 并查看下方详情。

<details>
<summary><b>🌟 贡献者和 DevFest.AI 参与者：</b></summary>

## 🌟 诚邀贡献者！

我们很高兴欢迎新的贡献者加入 Julep 项目！我们创建了几个"适合新手的问题"来帮助您入门。以下是您可以贡献的方式：

1. 查看我们的 [CONTRIBUTING.md](CONTRIBUTING.md) 文件，了解如何贡献的指南。
2. 浏览我们的[适合新手的问题](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)，找到一个您感兴趣的任务。
3. 如果您有任何问题或需要帮助，请随时在我们的 [Discord](https://discord.com/invite/JTSBGRZrzj) 频道上联系我们。

您的贡献，无论大小，对我们都很宝贵。让我们一起创造令人惊叹的东西吧！🚀

### 🎉 DevFest.AI 2024年10月

激动人心的消息！我们将在整个2024年10月参与 DevFest.AI 活动！🗓️

- 在此活动期间为 Julep 做出贡献，有机会赢得超棒的 Julep 周边和礼品！🎁
- 加入来自世界各地的开发者，为 AI 仓库做出贡献并参与精彩的活动。
- 非常感谢 DevFest.AI 组织这个fantastic的活动！

> [!TIP]
> 准备好加入这场盛会了吗？**[发推文开始参与](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)**，让我们开始编码吧！🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary><b>📖 Table of Contents</b></summary>

- [简介](#%E7%AE%80%E4%BB%8B)
- [特性](#%E7%89%B9%E6%80%A7)
- [安装](#%E5%AE%89%E8%A3%85)
- [快速入门指南](#%E5%BF%AB%E9%80%9F%E5%85%A5%E9%97%A8%E6%8C%87%E5%8D%97)
- [概念](#%E6%A6%82%E5%BF%B5)
- [理解任务](#%E7%90%86%E8%A7%A3%E4%BB%BB%E5%8A%A1)
- [高级功能](#%E9%AB%98%E7%BA%A7%E5%8A%9F%E8%83%BD)
- [SDK 参考](#sdk-%E5%8F%82%E8%80%83)
- [API 参考](#api-%E5%8F%82%E8%80%83)
- [示例和教程](#%E7%A4%BA%E4%BE%8B%E5%92%8C%E6%95%99%E7%A8%8B)
- [贡献](#%E8%B4%A1%E7%8C%AE)
- [支持和社区](#%E6%94%AF%E6%8C%81%E5%92%8C%E7%A4%BE%E5%8C%BA)
- [许可证](#%E8%AE%B8%E5%8F%AF%E8%AF%81)
- [致谢](#%E8%87%B4%E8%B0%A2)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## 简介

Julep 是一个开源平台，用于创建具有可定制工作流的持久 AI 代理。它提供了开发、管理和部署 AI 驱动应用程序的工具，注重灵活性和易用性。

使用 Julep，您可以：
- 快速开发能够在多次交互中保持上下文和状态的 AI 代理
- 设计和执行针对您的 AI 代理定制的复杂工作流
- 无缝集成各种工具和 API 到您的 AI 工作流中
- 轻松管理持久会话和用户交互

无论您是在开发聊天机器人、自动化任务，还是构建复杂的 AI 助手，Julep 都能为您提供所需的灵活性和功能，帮助您快速高效地将想法转化为现实。

<!-- TODO: 添加一个屏幕录像 -->

<details>
<summary>这里有一个简单的 Python 示例：</summary>

<!-- TODO: 在 README 中添加展示任务执行过程的 gif -->

<pre><code class="language-python">
from julep import Julep, AsyncJulep

# 🔑 初始化 Julep 客户端
#     或者使用 AsyncJulep 进行异步操作
client = Julep(api_key="your_api_key")

##################
## 🤖 代理 🤖 ##
##################

# 创建一个研究代理
agent = client.agents.create(
    name="研究代理",
    model="claude-3.5-sonnet",
    about="您是一个设计用于处理研究查询的研究代理。",
)

# 🔍 为代理添加工具
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",  # 应该是有效的 Python 变量名
    description="使用此工具进行研究查询。",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {
            "api_key": "your_brave_api_key",
        },
    },
)

#################
## 💬 聊天 💬 ##
#################

# 与代理开始交互式聊天会话
session = client.sessions.create(
    agent_id=agent.id,
    context_overflow="adaptive",  # 🧠 Julep 将在需要时动态计算上下文窗口
)

# 🔄 聊天循环
while (user_input := input("您：")) != "退出":
    response = client.sessions.chat(
        session_id=session.id,
        message=user_input,
    )

    print("代理：", response.choices[0].message.content)


#################
## 📋 任务 📋 ##
#################

# 为代理创建一个周期性研究任务
task = client.tasks.create(
    agent_id=agent.id,
    name="研究任务",
    description="每24小时研究给定的主题。",
    #
    # 🛠️ 任务特定工具
    tools=[
        {
            "name": "send_email",
            "description": "向用户发送包含结果的电子邮件。",
            "api_call": {
                "method": "post",
                "url": "https://api.sendgrid.com/v3/mail/send",
                "headers": {"Authorization": "Bearer YOUR_SENDGRID_API_KEY"},
            },
        }
    ],
    #
    # 🔢 任务主要步骤
    main=[
        #
        # 步骤 1：研究主题
        {
            # `_`（下划线）变量指向上一步的输出
            # 这里，它指向用户输入的主题
            "prompt": "查找主题 '{{_.topic}}' 并总结结果。",
            "tools": [{"ref": {"name": "web_search"}}],  # 🔍 使用代理的网络搜索工具
            "unwrap": True,
        },
        #
        # 步骤 2：发送包含研究结果的电子邮件
        {
            "tool": "send_email",
            "arguments": {
                "subject": "研究结果",
                "body": "'以下是今天的研究结果：' + _.content",
                "to": "inputs[0].email",  # 引用用户输入的电子邮件
            },
        },
        #
        # 步骤 3：等待 24 小时后重复
        {"sleep": "24 * 60 * 60"},
    ],
)

# 🚀 启动周期性任务
client.executions.create(task_id=task.id, input={"topic": "Python"})

# 🔁 这将每 24 小时运行一次任务，
#    研究 "Python" 主题，并
#    将结果发送到用户的电子邮件
</code></pre>
</details>

## 特性

Julep 简化了构建具有可定制工作流的持久 AI 代理的过程。主要特性包括：

- **持久 AI 代理**：创建和管理能够在多次交互中保持上下文的 AI 代理。
- **可定制工作流**：使用任务（Tasks）设计复杂的多步骤 AI 工作流。
- **工具集成**：无缝集成各种工具和 API 到您的 AI 工作流中。
- **文档管理**：高效管理和搜索代理的文档。
- **会话管理**：处理持久会话以实现连续交互。
- **灵活执行**：支持工作流中的并行处理、条件逻辑和错误处理。

## 安装

要开始使用 Julep，请使用 [npm](https://www.npmjs.com/package/@julep/sdk) 或 [pip](https://pypi.org/project/julep/) 安装：

```bash
npm install @julep/sdk
```

或

```bash
pip install julep
```

> [!TIP]
> 在测试阶段，您可以通过 [Discord](https://discord.com/invite/JTSBGRZrzj) 获取 API 密钥。

## 快速入门指南

### 步骤 1：导入 Julep

首先，将 Julep SDK 导入到您的项目中：

```javascript
const Julep = require('@julep/sdk');
```

或

```python
from julep import AsyncJulep
```

### 步骤 2：初始化代理

使用基本设置创建一个新代理：

```javascript
const julep = new Julep({ apiKey: 'your-api-key' });

const agent = await julep.agents.create({
  name: '研究助手',
  model: 'gpt-4-turbo',
  about: "您是一个创意讲故事代理，能够根据想法创作引人入胜的故事并生成漫画面板。",
});
```

或

```python
client = AsyncJulep(api_key="your_api_key")

agent = await client.agents.create(
    name="讲故事代理",
    model="gpt-4-turbo",
    about="您是一个创意讲故事代理，能够根据想法创作引人入胜的故事并生成漫画面板。",
)
```

### 步骤 3：与代理聊天

与代理开始交互式聊天会话：

```javascript
const session = await julep.sessions.create({
  agentId: agent.id,
}); 

// 向代理发送消息
const response = await julep.sessions.chat({
  sessionId: session.id,
  message: '你好，能给我讲个故事吗？',
});

console.log(response);
```

或

```python
session = await client.sessions.create(agent_id=agent.id)

# 向代理发送消息
response = await client.sessions.chat(
    session_id=session.id,
    message="你好，能给我讲个故事吗？",
)

print(response)
```

### 步骤 4：创建多步骤任务

让我们定义一个多步骤任务，根据输入的想法创建故事并生成分镜漫画：

```python
# 🛠️ 为代理添加图像生成工具（DALL·E）
await client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="使用此工具根据描述生成图像。",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_dalle_api_key",
        },
    },
)

# 📋 任务
# 创建一个任务，接受一个想法并创建故事和 4 格漫画
task = await client.tasks.create(
    agent_id=agent.id,
    name="故事和漫画创作器",
    description="根据一个想法创作故事并生成 4 格漫画来说明故事。",
    main=[
        # 步骤 1：生成故事并将其概括为 4 个面板
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "您是 {{agent.name}}。{{agent.about}}"
                },
                {
                    "role": "user",
                    "content": (
                        "基于想法 '{{_.idea}}'，写一个适合 4 格漫画的短故事。"
                        "提供故事和一个编号列表，包含 4 个简短描述，每个描述对应一个面板，说明故事中的关键时刻。"
                    ),
                },
            ],
            "unwrap": True,
        },
        # 步骤 2：提取面板描述和故事
        {
            "evaluate": {
                "story": "_.split('1. ')[0].strip()",
                "panels": "re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)",
            }
        },
        # 步骤 3：使用图像生成器工具为每个面板生成图像
        {
            "foreach": {
                "in": "_.panels",
                "do": {
                    "tool": "image_generator",
                    "arguments": {
                        "description": "_",
                    },
                },
            },
        },
        # 步骤 4：为故事生成一个吸引人的标题
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "您是 {{agent.name}}。{{agent.about}}"
                },
                {
                    "role": "user",
                    "content": "根据以下故事，生成一个吸引人的标题。\n\n故事：{{outputs[1].story}}",
                },
            ],
            "unwrap": True,
        },
        # 步骤 5：返回故事、生成的图像和标题
        {
            "return": {
                "title": "outputs[3]",
                "story": "outputs[1].story",
                "comic_panels": "[output.image.url for output in outputs[2]]",
            }
        },
    ],
)
```

> [!TIP]
> Node.js 版本的代码类似。

### 步骤 5：执行任务

```python
# 🚀 执行任务，输入一个想法
execution = await client.executions.create(
    task_id=task.id,
    input={"idea": "一只学会飞翔的猫"}
)

# 🎉 观看故事和漫画面板的生成过程
await client.executions.stream(execution_id=execution.id)
```

这个例子展示了如何创建一个带有自定义工具的代理，定义一个复杂的多步骤任务，并执行它以生成创意输出。

<!-- TODO: 在 README 中添加展示任务执行过程的 gif -->

> [!TIP]
> 您可以在[这里](example.ts)找到另一个 Node.js 示例，或在[这里](example.py)找到 Python 示例。

## 概念

Julep 建立在几个关键的技术组件之上，这些组件协同工作以创建强大的 AI 工作流：

### 代理
由大型语言模型（LLM）支持的 AI 实体，执行任务并与用户交互。代理是 Julep 的核心功能单元。

```mermaid
graph TD
    Agent[代理] --> LLM[大型语言模型]
    Agent --> Tasks[任务]
    Agent --> Users[用户]
    Tasks --> Tools[工具]
```

### 用户
与代理交互的实体。用户可以与会话关联，并拥有自己的元数据，允许个性化交互。

```mermaid
graph LR
    User[用户] --> Sessions[会话]
    Sessions --> Agents[代理]
    Sessions --> Metadata[元数据]
```

### 会话
代理和用户之间的有状态交互。会话在多次交换中保持上下文，可以配置不同的行为，包括上下文管理和溢出处理。

```mermaid
graph LR
    Sessions[会话] --> Agents[代理]
    Sessions --> Users[用户]
    Sessions --> ContextManagement[上下文管理]
    Sessions --> OverflowHandling[溢出处理]
```

### 任务
代理可以执行的多步骤、程序化工作流。任务定义复杂操作，可以包括各种类型的步骤，如提示、工具调用和条件逻辑。

```mermaid
graph TD
    Tasks[任务] --> Steps[工作流步骤]
    Steps --> Prompt[提示]
    Steps --> ToolCalls[工具调用]
    Steps --> ConditionalLogic[条件逻辑]
```

### 工具
扩展代理能力的集成。工具可以是用户定义的函数、系统工具或第三方 API 集成。它们允许代理执行超出文本生成的操作。

```mermaid
graph LR
    Tools[工具] --> UserDefinedFunctions[用户定义函数]
    Tools --> SystemTools[系统工具]
    Tools --> ThirdPartyAPIs[第三方 API]
```

### 文档
可以与代理或用户关联的文本或数据对象。文档被向量化并存储在向量数据库中，在代理交互期间实现语义搜索和检索。

```mermaid
graph LR
    Documents[文档] --> VectorDatabase[向量数据库]
    Documents --> SemanticSearch[语义搜索]
    Documents --> AgentsOrUsers[代理或用户]
```

### 执行
已经用特定输入启动的任务实例。执行有自己的生命周期和状态机，允许监控、管理和恢复长时间运行的进程。

```mermaid
graph LR
    Executions[执行] --> Tasks[任务]
    Executions --> Lifecycle[生命周期]
    Executions --> Monitoring[监控]
    Executions --> Management[管理]
    Executions --> Resumption[恢复]
```

有关这些概念及其交互的更详细解释，请参阅我们的[概念文档](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md)。

## 理解任务

任务是 Julep 工作流系统的核心。它们允许您定义复杂的多步骤 AI 工作流，供您的代理执行。以下是任务组件的简要概述：

- **名称和描述**：每个任务都有唯一的名称和描述，便于识别。
- **主要步骤**：任务的核心，定义了要执行的操作序列。
- **工具**：可选的集成，在任务执行期间扩展代理的能力。

### 工作流步骤类型

Julep 中的任务可以包含各种类型的步骤：

1. **提示**：向 AI 模型发送消息并接收响应。
   ```python
   {"prompt": "分析以下数据：{{data}}"}
   ```

2. **工具调用**：执行集成的工具或 API。
   ```python
   {"tool": "web_search", "arguments": {"query": "最新 AI 发展"}}
   ```

3. **评估**：执行计算或操作数据。
   ```python
   {"evaluate": {"average_score": "sum(scores) / len(scores)"}}
   ```

4. **条件逻辑**：基于条件执行步骤。
   ```python
   {"if": "score > 0.8", "then": [...], "else": [...]}
   ```

5. **循环**：遍历数据或重复步骤。
   ```python
   {"foreach": {"in": "data_list", "do": [...]}}
   ```

| 步骤类型 | 描述 | 输入 |
|---------|------|------|
| **提示** | 向 AI 模型发送消息并接收响应。 | 提示文本或模板 |
| **工具调用** | 执行集成的工具或 API。 | 工具名称和参数 |
| **评估** | 执行计算或操作数据。 | 要评估的表达式或变量 |
| **等待输入** | 暂停工作流直到收到输入。 | 任何所需的用户或系统输入 |
| **日志** | 记录指定的值或消息。 | 要记录的消息或值 |
| **嵌入** | 将文本嵌入到特定格式或系统中。 | 要嵌入的文本或内容 |
| **搜索** | 基于查询执行文档搜索。 | 搜索查询 |
| **获取** | 从键值存储中检索值。 | 键标识符 |
| **设置** | 在键值存储中为键分配值。 | 要分配的键和值 |
| **并行** | 并行运行多个步骤。 | 要同时执行的步骤列表 |
| **遍历** | 遍历集合并为每个项目执行步骤。 | 要遍历的集合或列表 |
| **映射归约** | 对集合进行映射并基于表达式归约结果。 | 要映射和归约的集合和表达式 |
| **如果-否则** | 基于条件执行步骤。 | 要评估的条件 |
| **开关** | 基于多个条件执行步骤，类似于 switch-case 语句。 | 多个条件和相应的步骤 |
| **生成** | 运行子工作流并等待其完成。 | 子工作流标识符和输入数据 |
| **错误** | 通过指定错误消息来处理错误。 | 错误消息或处理指令 |
| **睡眠** | 暂停工作流指定的持续时间。 | 持续时间（秒、分钟等） |
| **返回** | 从工作流返回值。 | 要返回的值 |

有关每种步骤类型的详细信息和高级用法，请参阅我们的[任务文档](https://docs.julep.ai/tasks)。

## 高级功能

Julep 提供了一系列高级功能来增强您的 AI 工作流：

### 为代理添加工具

通过集成外部工具和 API 来扩展代理的能力：

```python
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="搜索网络以获取信息。",
    integration={
        "provider": "google",
        "method": "search",
        "setup": {"api_key": "your_google_api_key"},
    },
)
```

### 管理会话和用户

Julep 为持久交互提供了强大的会话管理：

```python
session = client.sessions.create(
    agent_id=agent.id,
    user_id="user123",
    context_overflow="adaptive"
)

# 在同一会话中继续对话
response = client.sessions.chat(
    session_id=session.id,
    message="继续我们之前的对话。"
)
```

### 文档集成和搜索

轻松管理和搜索代理的文档：

```python
# 上传文档
document = client.documents.create(
    file="path/to/document.pdf",
    metadata={"category": "research_paper"}
)

# 搜索文档
results = client.documents.search(
    query="AI 进展",
    filter={"category": "research_paper"}
)
```

有关更多高级功能和详细用法，请参阅我们的[高级功能文档](https://docs.julep.ai/advanced-features)。

## SDK 参考

- [Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)
- [Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)

## API 参考

探索我们全面的 API 文档，了解更多关于代理、任务和执行的信息：

- [代理 API](https://api.julep.ai/api/docs#tag/agents)
- [任务 API](https://api.julep.ai/api/docs#tag/tasks)
- [执行 API](https://api.julep.ai/api/docs#tag/executions)

## 示例和教程

发现示例项目和教程，帮助您入门并基于提供的示例进行构建：

- [示例项目](https://github.com/julep-ai/julep/tree/main/examples)
- [教程](https://docs.julep.ai/tutorials)

## 贡献

我们欢迎对项目的贡献！了解如何贡献以及我们的行为准则：

- [贡献指南](https://github.com/julep-ai/julep/blob/main/CONTRIBUTING.md)
- [行为准则](https://github.com/julep-ai/julep/blob/main/CODE_OF_CONDUCT.md)

## 支持和社区

加入我们的社区，获取帮助、提问和分享您的想法：

- [Discord](https://discord.com/invite/JTSBGRZrzj)
- [GitHub 讨论](https://github.com/julep-ai/julep/discussions)
- [Twitter](https://twitter.com/julep_ai)

## 许可证

本项目采用 [Apache License 2.0](https://github.com/julep-ai/julep/blob/main/LICENSE) 许可。

## 致谢

我们要感谢所有贡献者和开源社区为他们宝贵的资源和贡献。
