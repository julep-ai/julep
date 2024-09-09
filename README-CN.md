<sup>[English](README.md) | 中文翻译</sup>

<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Open-source%20platform%20for%20building%20stateful%20AI%20apps&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
</div>

<h2 align="center">
使用有状态代理、复杂工作流和集成工具构建强大的AI应用程序
</h2>

  <p align="center">
    <br />
    <a href="https://docs.julep.ai" rel="dofollow"><strong>探索文档 »</strong></a>
    <br />
  <br/>
    <a href="https://github.com/julep-ai/julep/issues/new">报告Bug</a>
    ·
    <a href="https://github.com/julep-ai/julep/discussions/293">请求功能</a>
    ·
    <a href="https://discord.com/invite/JTSBGRZrzj">加入我们的Discord</a>
    ·
    <a href="https://x.com/julep_ai">X</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai">LinkedIn</a>

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

## 🚀 即将发布：v0.4 Alpha

<div align="center">
  <img src=".github/i-have-an-announcement.gif" alt="Announcing v0.4 Alpha">
</div>

我们很高兴地宣布v0.4目前处于alpha阶段！此版本带来了重大改进和新功能。敬请期待正式发布。

要全面了解Julep的核心概念和即将推出的功能，请查看我们的[详细概念指南](docs/julep-concepts.md)。

寻找之前的版本？您可以在这里找到[v0.3 README](v0.3_README.md)。

---

## 为什么选择Julep？
我们构建了许多AI应用程序，并深知创建具有多个代理和工作流的复杂、有状态应用程序的挑战。

**问题**
1. 构建具有记忆、知识和工具的AI应用程序复杂且耗时。
2. 在AI应用程序中管理长时间运行的任务和复杂工作流具有挑战性。
3. 将多个工具和服务集成到AI应用程序中需要大量开发工作。

---
## 功能
- **有状态代理**：创建和管理具有内置对话历史和记忆的代理。
- **复杂工作流**：定义和执行具有分支、并行执行和错误处理的多步骤任务。
- **集成工具**：轻松将各种工具和外部服务整合到您的AI应用程序中。
- **灵活的会话管理**：支持代理和用户之间的各种交互模式，如一对多和多对一。
- **内置RAG**：添加、删除和更新文档以为您的代理提供上下文。
- **异步任务执行**：在后台运行长时间运行的任务，具有状态管理和可恢复性。
- **多模型支持**：在保持状态的同时切换不同的语言模型（OpenAI、Anthropic、Ollama）。
- **任务系统**：定义和执行具有并行处理和错误处理的复杂多步骤工作流。

---
## 快速入门
### 选项1：使用Julep云
我们的托管平台目前处于Beta阶段！ 

要获取访问权限：
- 前往https://platform.julep.ai
- 在`.env`中生成并添加您的`JULEP_API_KEY`

### 选项2：在本地安装并运行Julep
前往[自托管](https://docs.julep.ai/guides/self-hosting)文档，了解如何在本地运行Julep！

### 安装

```bash
pip install julep
```

### 设置`client`

```python
from julep import Client
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

### 创建代理
代理是将LLM设置（如模型、温度）以及工具范围的对象。

```python
agent = client.agents.create(
    name="Jessica",
    model="gpt-4",
    tools=[],    # 在此处定义工具
    about="A helpful AI assistant",
    instructions=["Be polite", "Be concise"]
)
```

### 创建用户
用户是应用程序用户的对象。

记忆是为每个用户形成并保存的，多个用户可以与一个代理交谈。

```python
user = client.users.create(
    name="Anon",
    about="Average nerdy techbro/girl spending 8 hours a day on a laptop",
)
```

### 创建会话
"用户"和"代理"在"会话"中进行交互。系统提示在此处。

```python
situation_prompt = """You are Jessica, a helpful AI assistant. 
You're here to assist the user with any questions or tasks they might have."""
session = client.sessions.create(
    user_id=user.id,
    agent_id=agent.id,
    situation=situation_prompt
)
```

### 开始有状态对话
`session.chat`控制"代理"和"用户"之间的通信。

它有两个重要参数；
- `recall`：检索先前的对话和记忆。
- `remember`：将当前对话回合保存到记忆存储中。

要保持会话状态，两者都需要为`True`

```python
user_msg = "Hey Jessica, can you help me with a task?"
response = client.sessions.chat(
    session_id=session.id,
    messages=[
        {
            "role": "user",
            "content": user_msg,
            "name": "Anon",
        }
    ],
    recall=True,
    remember=True,
)

print(response.response[0][0].content)
```

---

## 核心概念

### 代理（Agent）
Julep中的代理是应用程序的主要协调者。它由GPT-4或Claude等基础模型支持，可以使用工具、文档并执行复杂任务。

### 用户（User）
Julep中的用户代表应用程序的最终用户。他们可以与会话关联，并拥有自己的文档和元数据。

### 会话（Session）
会话管理用户和代理之间的交互。它们维护对话历史和上下文。

### 工具（Tool）
工具是代理可以用来执行特定操作或检索信息的函数。

### 文档（Doc）
文档是可以与代理或用户关联的文本片段集合，用于上下文检索。

### 任务（Task）
任务是可以由代理定义和执行的复杂多步骤工作流。

### 执行（Execution）
执行是已经以某些输入启动的任务实例。它在进行过程中经历各种状态。

---

## API和SDK

要直接使用API或查看请求和响应格式、身份验证、可用端点等，请参阅[API文档](https://docs.julep.ai/api-reference/agents-api/agents-api)

### Python SDK

要安装Python SDK，运行：

```bash
pip install julep
```

有关使用Python SDK的更多信息，请参阅[Python SDK文档](https://docs.julep.ai/api-reference/python-sdk-docs)。

### TypeScript SDK
要使用`npm`安装TypeScript SDK，运行：

```bash
npm install @julep/sdk
```

有关使用TypeScript SDK的更多信息，请参阅[TypeScript SDK文档](https://docs.julep.ai/api-reference/js-sdk-docs)。

---

## 部署
查看[自托管指南](https://docs.julep.ai/agents/self-hosting)以自行托管平台。

如果您想将Julep部署到生产环境，[让我们安排一次通话](https://cal.com/ishitaj/15min)！

我们将帮助您定制平台并帮助您设置：
- 多租户
- 反向代理以及身份验证和授权
- 自托管LLMs
- 等等

---
## 贡献
我们欢迎社区的贡献，以帮助改进和扩展Julep AI平台。请查看我们的[贡献指南](CONTRIBUTING.md)以获取更多关于如何开始的信息。

---
## 许可证
Julep AI根据Apache 2.0许可证发布。有关更多详细信息，请参阅[LICENSE](LICENSE)文件。

---
## 联系和支持
如果您有任何问题、需要帮助或想与Julep AI团队联系，请使用以下渠道：

- [Discord](https://discord.com/invite/JTSBGRZrzj)：加入我们的社区论坛，讨论想法、提问并从其他Julep AI用户和开发团队获得帮助。
- GitHub Issues：对于技术问题、错误报告和功能请求，请在Julep AI GitHub仓库上提出issue。
- 电子邮件支持：如果您需要我们支持团队的直接帮助，请发送电子邮件至hey@julep.ai，我们会尽快回复您。
- 在[X](https://twitter.com/julep_ai)和[LinkedIn](https://www.linkedin.com/company/julep-ai/)上关注我们获取最新更新
- [安排一次通话](https://cal.com/ishitaj/15min)：我们想了解您正在构建的内容，以及我们如何调整和优化Julep以帮助您构建下一个AI应用程序。
