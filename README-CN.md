<sup>[English](/) | 中文翻译</sup>

<div align="center">
    <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=%E7%94%A8%E4%BA%8E%E6%9E%84%E5%BB%BA%E6%9C%89%E7%8A%B6%E6%80%81%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%BA%94%E7%94%A8%E7%9A%84%E5%BC%80%E6%BA%90%E5%B9%B3%E5%8F%B0&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&pattern=Solid&stargazers=1&theme=Dark" alt="julep" width="640" height="320" />
</div>

---

💸🤑 **宣布我们的赏金计划：** 帮助 Julep 社区修复错误并发布功能，即可获得报酬。更多详情[点击这里](https://github.com/julep-ai/julep/discussions/categories/bounty-program)。

---
## 在对话历史记录、支持任何LLM、代理式工作流、集成等方面开始您的项目。

<p align="center">
    <br />
    <a href="https://docs.julep.ai" rel="dofollow"><strong>探索文档 »</strong></a>
    <br />
  <br/>
    <a href="https://github.com/julep-ai/julep/issues/new">报告错误</a>
    ·
    <a href="https://github.com/julep-ai/julep/discussions/293">请求功能</a>
    ·
    <a href="https://discord.com/invite/JTSBGRZrzj">加入我们的Discord</a>
    ·
    <a href="https://x.com/julep_ai">X</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai">领英</a>
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

## 为什么选择 Julep？
我们构建了许多人工智能应用程序，并且了解评估数百种工具、技术和模型，然后使它们良好地配合在一起有多么困难。

**问题**
1. 具有记忆、知识和工具的LLM应用的门槛太高了。
2. 通过多代理框架进行代理行为的控制很难。

---
## 特性
- **设计时状态性**: 默认情况下管理对话历史记录。使用简单的标志 `remember` 和 `recall` 来调整是否保存或检索对话历史记录。
- **支持用户和代理**: 允许创建不同的用户 <-> 代理交互，如 `一个代理 <-> 多个用户`；`多个代理 <-> 一个用户`等。[了解更多](https://docs.julep.ai/concepts/)。
- **内置RAG**: 添加、删除和更新文档，为LLM提供关于用户或代理的上下文，具体取决于您的用例。[在此处阅读更多](https://docs.julep.ai/guides/build-a-retrieval-augmented-generation-rag-agent)。
- **内置90+工具**: 使用[Composio](https://docs.composio.dev/framework/julep/)本地连接您的AI应用到90+第三方应用程序。`toolset.handle_tool_calls(julep_client, session.id, response)` 将为您调用和处理工具！[查看示例](https://docs.julep.ai/guides/use-julep-with-composio)
- **本地优先**: Julep 可以使用 Docker Compose 部署到生产环境。对于 k8s 的支持即将推出！
- **动态切换LLM**: 更新代理以在OpenAI、Anthropic或Ollama之间切换LLM。同时保留状态。
- **为代理分配任务**: 定义异步执行的代理工作流，一个或多个代理无需担心超时或幻觉增多。[正在进行中](https://github.com/julep-ai/julep/discussions/387)

> (*) 即将推出！

---
## 指南
您可以在 [指南文档](https://docs.julep.ai/guides/) 中查看 Julep 的不同功能。
1. [简单的对话机器人](https://deepnote.com/app/julep-ai-761c/Julep-Mixers-4dfff09a-84f2-4278-baa3-d1a00b88ba26)
2. [搜索代理](https://docs.julep.ai/guides/)
3. [RAG 代理](https://docs.julep.ai/guides/build-a-retrieval-augmented-generation-rag-agent)
4. [使用 Composio 的 GitHub 代理](https://docs.julep.ai/guides/use-julep-with-composio)
5. [用于视觉的 GPT 4o](https://docs.julep.ai/guides/image-+-text-with-gpt-4o)

---


## 快速开始
### 选项1：使用 Julep 云
我们的托管平台处于测试版！

获取访问权限：
- 前往 https://platform.julep.ai
- 生成并添加您的 `JULEP_API_KEY` 到 `.env` 文件中

### 选项2：在本地安装和运行 Julep
前往 [自托管](https://docs.julep.ai/guides/self-hosting) 文档了解如何在本地运行 Julep！

### 安装

```
pip install julep
```

### 设置 `client`

```py
from julep import Client
from pprint import pprint
import textwrap
import os

base_url = os.environ.get("JULEP_API_URL")
api_key = os.environ.get("JULEP_API_KEY")

client = Client(api_key=api_key, base_url=base_url)
```

### 创建代理
代理是 LLM 设置的对象，例如模型、温度以及工具。

```py
agent = client.agents.create(
    name="Jessica",
    model="gpt-4",
    tools=[]    # 在此处定义工具
)
```

### 创建用户
用户是应用程序的用户对象。

为每个用户形成和保存记忆，许多用户可以与一个代理交谈。

```py
user = client.users.create(
    name="Anon",
    about="每天花8小时在笔记本电脑上的普通技术宅/女孩",
)
```

---

### 创建会话
一个 "用户" 和一个 "代理" 在一个 "会话" 中进行通信。系统提示在这里。
会话历史记录和摘要存储在一个 "会话" 中，该会话保存了对话历史记录。

会话范式允许许多用户与一个代理进行交互，并允许对话历史记录和记忆的分离。

```py
situation_prompt = """你是 Jessica。你是一个自命不凡的加州少年。 你基本上抱怨一切。 你住在洛杉矶的贝尔埃尔，必要时你会去科蒂斯高中上学。
"""
session = client.sessions.create(
    user_id=user.id, agent_id=agent.id, situation=situation_prompt
)
```

### 开始有状态的对话
`session.chat` 控制 "代理" 和 "用户" 之间的通信。

它有两个重要的参数;
- `recall`: 检索之前的对话和记忆。
- `remember`: 将当前的对话转换为内存存储。

要保持会话有状态，两者都需要设置为 `True`

```py
user_msg = "嗨，你觉得星巴克怎么样"
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

print("\n".join(textwrap.wrap(response.response[0][0].content, width=100)))
```

---

## API 和 SDK
要直接使用 API 或查看请求和响应格式、认证、可用端点等信息，请参阅 [API 文档](https://docs.julep.ai/api-reference/agents-api/agents-api)。

您也可以使用 [Postman 集合](https://god.gw.postman.com/run-collection/33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D33213061-a0a1e3a9-9681-44ae-a5c2-703912b32336%26entityType%3Dcollection%26workspaceId%3D183380b4-f2ac-44ef-b018-1f65dfc8256b) 进行参考。

### Python SDK

要安装 Python SDK，请运行：

```bash
pip install julep
```

有关使用 Python SDK 的更多信息，请参阅 [Python SDK 文档](https://docs.julep.ai/api-reference/python-sdk-docs)。


### TypeScript SDK
要使用 `npm` 安装 TypeScript SDK，请运行：

```bash
npm install @julep/sdk
```

有关使用 TypeScript SDK 的更多信息，请参阅 [TypeScript SDK 文档](https://docs.julep.ai/api-reference/js-sdk-docs)。

---

## 部署
查看 [自托管指南](https://docs.julep.ai/agents/self-hosting) 以自行托管平台。

如果您想将 Julep 部署到生产环境中，请 [与我们通话](https://cal.com/ishitaj/15min)！

我们将帮助您自定义平台并帮助您设置：
- 多租户
- 反向代理以及认证和授权
- 自托管 LLMs
- 等等

---

## 贡献
我们欢迎社区的贡献，以帮助改进和扩展 Julep AI 平台。请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 许可证
Julep AI 使用 Apache 2.0 许可证发布。通过使用、贡献或分发 Julep AI 平台，您同意此许可证的条款和条件。

---

## 联系和支持
如果您有任何问题，需要帮助，或想要联系 Julep AI 团队，请使用以下渠道：

- [Discord](https://discord.com/invite/JTSBGRZrzj)：加入我们的社区论坛，讨论想法，提出问题，并从其他 Julep AI 用户和开发团队中获取帮助。
- GitHub Issues：对于技术问题、错误报告和功能请求，请在 Julep AI GitHub 存储库上开启一个 issue。
- 电子邮件支持：如果您需要直接向我们的支持团队寻求帮助，请发送电子邮件至 hey@julep.ai，我们会尽快回复您。
- 关注 [X](https://twitter.com/julep_ai) & [LinkedIn](https://www.linkedin.com/company/julep-ai/)
- [与我们通话](https://cal.com/ishitaj/15min)：我们想了解您正在构建什么以及我们如何调整和优化 Julep 以帮助您构建下一个 AI 应用程序。
