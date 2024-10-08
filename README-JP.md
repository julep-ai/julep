<sup>[English](README.md) | [中文翻译](/README-CN.md) | 日本語</sup>

<div align="center">
 <img src = "https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20building%20multi-step%20agent%20workflows.&font=Raleway&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&theme=Light" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow"><strong>ドキュメントを探索する</strong></a>
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

*****

> [!TIP]
> 👨‍💻 devfest.aiイベントに参加されましたか？私たちの[Discord](https://discord.com/invite/JTSBGRZrzj)に参加して、以下の詳細をご確認ください。

<details>
<summary><b>🌟 コントリビューターとDevFest.AI参加者の皆様へ：</b></summary>

## 🌟 コントリビューター募集！

Julepプロジェクトに新しいコントリビューターを歓迎します！スタートに役立つ「初心者向けの問題」をいくつか作成しました。以下は、貢献する方法です：

1. [CONTRIBUTING.md](CONTRIBUTING.md)ファイルを確認して、貢献のガイドラインを確認してください。
2. [初心者向けの問題](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)を閲覧して、興味のあるタスクを見つけてください。
3. 質問がある場合や助けが必要な場合は、[Discord](https://discord.com/invite/JTSBGRZrzj)チャンネルでお気軽にお問い合わせください。

あなたの貢献、大きいものでも小さいものでも、私たちにとっては貴重です。一緒に素晴らしいものを作りましょう！🚀

### 🎉 DevFest.AI 2024年10月

エキサイティングなニュース！2024年10月中、DevFest.AIに参加します！🗓️

- このイベント中にJulepに貢献し、素晴らしいJulepのグッズや景品を獲得するチャンスを得ましょう！🎁
- 世界中の開発者と一緒にAIリポジトリに貢献し、素晴らしいイベントに参加しましょう。
- この素晴らしいイニシアチブを組織してくれたDevFest.AIに大きな感謝を！

> [!TIP]
> 楽しみに参加する準備はできましたか？**[ツイートして参加を開始](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)**し、コーディングを始めましょう！🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary><h3>📖 Table of Contents</h3></summary>

- [紹介](#%E7%B4%B9%E4%BB%8B)
- [特徴](#%E7%89%B9%E5%BE%B4)
- [インストール](#%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB)
- [クイックスタートガイド](#%E3%82%AF%E3%82%A4%E3%83%83%E3%82%AF%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%88%E3%82%AC%E3%82%A4%E3%83%89)
  - [ステップ1：Julepをインポートする](#%E3%82%B9%E3%83%86%E3%83%83%E3%83%971julep%E3%82%92%E3%82%A4%E3%83%B3%E3%83%9D%E3%83%BC%E3%83%88%E3%81%99%E3%82%8B)
  - [ステップ2：エージェントを初期化する](#%E3%82%B9%E3%83%86%E3%83%83%E3%83%972%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E3%82%92%E5%88%9D%E6%9C%9F%E5%8C%96%E3%81%99%E3%82%8B)
  - [ステップ3：エージェントとチャットする](#%E3%82%B9%E3%83%86%E3%83%83%E3%83%973%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E3%81%A8%E3%83%81%E3%83%A3%E3%83%83%E3%83%88%E3%81%99%E3%82%8B)
  - [ステップ4：多段階タスクを作成する](#%E3%82%B9%E3%83%86%E3%83%83%E3%83%974%E5%A4%9A%E6%AE%B5%E9%9A%8E%E3%82%BF%E3%82%B9%E3%82%AF%E3%82%92%E4%BD%9C%E6%88%90%E3%81%99%E3%82%8B)
  - [ステップ5：タスクを実行する](#%E3%82%B9%E3%83%86%E3%83%83%E3%83%975%E3%82%BF%E3%82%B9%E3%82%AF%E3%82%92%E5%AE%9F%E8%A1%8C%E3%81%99%E3%82%8B)
- [概念](#%E6%A6%82%E5%BF%B5)
  - [エージェント](#%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88)
  - [ユーザー](#%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC)
  - [セッション](#%E3%82%BB%E3%83%83%E3%82%B7%E3%83%A7%E3%83%B3)
  - [タスク](#%E3%82%BF%E3%82%B9%E3%82%AF)
  - [ツール](#%E3%83%84%E3%83%BC%E3%83%AB)
  - [ドキュメント](#%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88)
  - [実行](#%E5%AE%9F%E8%A1%8C)
- [タスクの理解](#%E3%82%BF%E3%82%B9%E3%82%AF%E3%81%AE%E7%90%86%E8%A7%A3)
  - [ワークフローステップの種類](#%E3%83%AF%E3%83%BC%E3%82%AF%E3%83%95%E3%83%AD%E3%83%BC%E3%82%B9%E3%83%86%E3%83%83%E3%83%97%E3%81%AE%E7%A8%AE%E9%A1%9E)
- [高度な機能](#%E9%AB%98%E5%BA%A6%E3%81%AA%E6%A9%9F%E8%83%BD)
  - [エージェントにツールを追加する](#%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E3%81%AB%E3%83%84%E3%83%BC%E3%83%AB%E3%82%92%E8%BF%BD%E5%8A%A0%E3%81%99%E3%82%8B)
  - [セッションとユーザーの管理](#%E3%82%BB%E3%83%83%E3%82%B7%E3%83%A7%E3%83%B3%E3%81%A8%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC%E3%81%AE%E7%AE%A1%E7%90%86)
  - [ドキュメントの統合と検索](#%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%E3%81%AE%E7%B5%B1%E5%90%88%E3%81%A8%E6%A4%9C%E7%B4%A2)
- [SDKリファレンス](#sdk%E3%83%AA%E3%83%95%E3%82%A1%E3%83%AC%E3%83%B3%E3%82%B9)
- [APIリファレンス](#api%E3%83%AA%E3%83%95%E3%82%A1%E3%83%AC%E3%83%B3%E3%82%B9)
- [例とチュートリアル](#%E4%BE%8B%E3%81%A8%E3%83%81%E3%83%A5%E3%83%BC%E3%83%88%E3%83%AA%E3%82%A2%E3%83%AB)
- [貢献](#%E8%B2%A2%E7%8C%AE)
- [サポートとコミュニティ](#%E3%82%B5%E3%83%9D%E3%83%BC%E3%83%88%E3%81%A8%E3%82%B3%E3%83%9F%E3%83%A5%E3%83%8B%E3%83%86%E3%82%A3)
- [ライセンス](#%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9)
- [謝辞](#%E8%AC%9D%E8%BE%9E)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## 紹介

Julepは、カスタマイズ可能なワークフローを持つ持続可能なAIエージェントを作成するためのオープンソースプラットフォームです。柔軟性と使いやすさに重点を置いて、AI駆動のアプリケーションを開発、管理、展開するためのツールを提供します。

Julepを使用すると、次のことができます：
- 複数のインタラクションにわたってコンテキストと状態を保持するAIエージェントを迅速に開発する
- AIエージェントに合わせた洗練されたワークフローを設計および実行する
- さまざまなツールやAPIをAIワークフローにシームレスに統合する
- 持続的なセッションとユーザーインタラクションを簡単に管理する

チャットボットの開発、タスクの自動化、または複雑なAIアシスタントの構築を行う場合でも、Julepはアイデアを迅速かつ効率的に現実に変えるために必要な柔軟性と機能を提供します。

<!-- TODO: スクリーンキャストを追加 -->

<details>
<summary>ここに簡単なPythonの例があります：</summary>

<!-- TODO: READMEにタスクの実行を示すgifを追加 -->

<pre><code class="language-python">
from julep import Julep, AsyncJulep

# 🔑 Julepクライアントを初期化する
#     または、非同期操作のためにAsyncJulepを使用する
client = Julep(api_key="your_api_key")

##################
## 🤖 エージェント 🤖 ##
##################

# 研究エージェントを作成する
agent = client.agents.create(
    name="Research Agent",
    model="claude-3.5-sonnet",
    about="You are a research agent designed to handle research inquiries.",
)

# 🔍 エージェントにウェブ検索ツールを追加する
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",  # Pythonの有効な変数名である必要があります
    description="Use this tool to research inquiries.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {
            "api_key": "your_brave_api_key",
        },
    },
)

#################
## 💬 チャット 💬 ##
#################

# エージェントとのインタラクティブなチャットセッションを開始する
session = client.sessions.create(
    agent_id=agent.id,
    context_overflow="adaptive",  # 🧠 必要に応じてJulepがコンテキストウィンドウを動的に計算します
)

# 🔄 チャットループ
while (user_input := input("You: ")) != "exit":
    response = client.sessions.chat(
        session_id=session.id,
        message=user_input,
    )

    print("Agent: ", response.choices[0].message.content)


#################
## 📋 タスク 📋 ##
#################

# エージェントのための定期的な研究タスクを作成する
task = client.tasks.create(
    agent_id=agent.id,
    name="Research Task",
    description="Research the given topic every 24 hours.",
    #
    # 🛠️ タスク固有のツール
    tools=[
        {
            "name": "send_email",
            "description": "Send an email to the user with the results.",
            "api_call": {
                "method": "post",
                "url": "https://api.sendgrid.com/v3/mail/send",
                "headers": {"Authorization": "Bearer YOUR_SENDGRID_API_KEY"},
            },
        }
    ],
    #
    # 🔢 タスクの主なステップ
    main=[
        #
        # ステップ1：トピックを調査する
        {
            # `_`（アンダースコア）変数は前のステップの出力を指します
            # ここでは、ユーザーからのトピック入力を指します
            "prompt": "Look up topic '{{_.topic}}' and summarize the results.",
            "tools": [{"ref": {"name": "web_search"}}],  # 🔍 エージェントのウェブ検索ツールを使用する
            "unwrap": True,
        },
        #
        # ステップ2：研究結果を含むメールを送信する
        {
            "tool": "send_email",
            "arguments": {
                "subject": "Research Results",
                "body": "'Here are the research results for today: ' + _.content",
                "to": "inputs[0].email",  # ユーザーの入力からメールを参照する
            },
        },
        #
        # ステップ3：繰り返す前に24時間待つ
        {"sleep": "24 * 60 * 60"},
    ],
)

# 🚀 定期的なタスクを開始する
client.executions.create(task_id=task.id, input={"topic": "Python"})

# 🔁 これにより、タスクは24時間ごとに実行され、
#    "Python"のトピックを調査し、
#    結果をユーザーのメールに送信します
</code></pre>
</details>


## 特徴

Julepは、カスタマイズ可能なワークフローを持つ持続可能なAIエージェントの構築プロセスを簡素化します。主な特徴は次のとおりです：

- **持続可能なAIエージェント**：複数のインタラクションにわたってコンテキストを保持するAIエージェントを作成および管理します。
- **カスタマイズ可能なワークフロー**：タスクを使用して複雑な多段階のAIワークフローを設計します。
- **ツール統合**：さまざまなツールやAPIをAIワークフローにシームレスに統合します。
- **ドキュメント管理**：エージェントのためのドキュメントを効率的に管理および検索します。
- **セッション管理**：継続的なインタラクションのための持続的なセッションを処理します。
- **柔軟な実行**：ワークフローでの並行処理、条件ロジック、およびエラー処理をサポートします。

## インストール

Julepを始めるには、[npm](https://www.npmjs.com/package/@julep/sdk)または[pip](https://pypi.org/project/julep/)を使用してインストールします：

```bash
npm install @julep/sdk
```

または

```bash
pip install julep
```

> [!TIP]
> ~~APIキーを[こちら](https://app.julep.ai/api-keys)から取得してください。~~
>  
> ベータ版の間、APIキーを取得するには[Discord](https://discord.com/invite/JTSBGRZrzj)でお問い合わせください。

## クイックスタートガイド

### ステップ1：Julepをインポートする

まず、Julep SDKをプロジェクトにインポートします：

```javascript
const Julep = require('@julep/sdk');
```

または

```python
from julep import AsyncJulep
```

### ステップ2：エージェントを初期化する

基本設定で新しいエージェントを作成します：

```javascript
const julep = new Julep({ apiKey: 'your-api-key' });

const agent = await julep.agents.create({
  name: 'ResearchAssistant',
  model: 'gpt-4-turbo',
  about: "You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
});
```

または

```python
client = AsyncJulep(api_key="your_api_key")

agent = await client.agents.create(
    name="Storytelling Agent",
    model="gpt-4-turbo",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)
```

### ステップ3：エージェントとチャットする

エージェントとのインタラクティブなチャットセッションを開始します：

```javascript
const session = await julep.sessions.create({
  agentId: agent.id,
}); 

// エージェントにメッセージを送信する
const response = await julep.sessions.chat({
  sessionId: session.id,
  message: 'Hello, can you tell me a story?',
});

console.log(response);
```

または

```python
session = await client.sessions.create(agent_id=agent.id)

# エージェントにメッセージを送信する
response = await client.sessions.chat(
    session_id=session.id,
    message="Hello, can you tell me a story?",
)

print(response)
``` 


### ステップ4：多段階タスクを作成する

入力されたアイデアに基づいてストーリーを作成し、パネル化されたコミックストリップを生成する多段階タスクを定義しましょう：

```python
# 🛠️ エージェントに画像生成ツール（DALL·E）を追加する
await client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_dalle_api_key",
        },
    },
)

# 📋 タスク
# アイデアを受け取り、ストーリーと4コマ漫画を作成するタスクを作成する
task = await client.tasks.create(
    agent_id=agent.id,
    name="Story and Comic Creator",
    description="Create a story based on an idea and generate a 4-panel comic strip illustrating the story.",
    main=[
        # ステップ1：ストーリーを生成し、4つのパネルに要約する
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": (
                        "Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip. "
                        "Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story."
                    ),
                },
            ],
            "unwrap": True,
        },
        # ステップ2：パネルの説明とストーリーを抽出する
        {
            "evaluate": {
                "story": "_.split('1. ')[0].strip()",
                "panels": "re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)",
            }
        },
        # ステップ3：画像生成ツールを使用して各パネルの画像を生成する
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
        # ステップ4：ストーリーのキャッチーなタイトルを生成する
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": "Based on the story below, generate a catchy title.\n\nStory: {{outputs[1].story}}",
                },
            ],
            "unwrap": True,
        },
        # ステップ5：ストーリー、生成された画像、およびタイトルを返す
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
> これのnode.jsバージョンは似ています。

### ステップ5：タスクを実行する

```python
# 🚀 アイデアを入力してタスクを実行する
execution = await client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 ストーリーとコミックパネルが生成される様子を見守る
await client.executions.stream(execution_id=execution.id)
```

この例は、カスタムツールを持つエージェントを作成し、複数のステップを持つ複雑なタスクを定義し、それを実行してクリエイティブな出力を生成する方法を示しています。

<!-- TODO: READMEにタスクの実行を示すgifを追加 -->

> [!TIP]
> もう一つのnode.jsの例は[こちら](example.ts)またはpythonの例は[こちら](example.py)にあります。

## 概念

Julepは、強力なAIワークフローを作成するために連携するいくつかの主要な技術コンポーネントに基づいて構築されています：

### エージェント
タスクを実行し、ユーザーと対話する大規模な言語モデル（LLM）に支えられたAIエンティティ。エージェントはJulepのコア機能ユニットです。

```mermaid
graph TD
    Agent[Agent] --> LLM[Large Language Model]
    Agent --> Tasks[Tasks]
    Agent --> Users[Users]
    Tasks --> Tools[Tools]
```

### ユーザー
エージェントと対話するエンティティ。ユーザーはセッションに関連付けられ、独自のメタデータを持つことができ、個別の対話が可能になります。

```mermaid
graph LR
    User[User] --> Sessions[Sessions]
    Sessions --> Agents[Agents]
    Sessions --> Metadata[Metadata]
```

### セッション
エージェントとユーザーの間の有状態の対話。セッションは複数の交換にわたってコンテキストを保持し、コンテキスト管理やオーバーフロー処理などの異なる動作に対して構成できます。

```mermaid
graph LR
    Sessions[Sessions] --> Agents[Agents]
    Sessions --> Users[Users]
    Sessions --> ContextManagement[Context Management]
    Sessions --> OverflowHandling[Overflow Handling]
```

### タスク
エージェントが実行できる多段階のプログラムワークフロー。タスクは複雑な操作を定義し、プロンプト、ツール呼び出し、条件ロジックなどのさまざまなタイプのステップを含むことができます。

```mermaid
graph TD
    Tasks[Tasks] --> Steps[Workflow Steps]
    Steps --> Prompt[Prompt]
    Steps --> ToolCalls[Tool Calls]
    Steps --> ConditionalLogic[Conditional Logic]
```

### ツール
エージェントの能力を拡張する統合。ツールはユーザー定義の関数、システムツール、またはサードパーティのAPI統合である可能性があります。これにより、エージェントはテキスト生成を超えたアクションを実行できます。

```mermaid
graph LR
    Tools[Tools] --> UserDefinedFunctions[User-Defined Functions]
    Tools --> SystemTools[System Tools]
    Tools --> ThirdPartyAPIs[Third-Party APIs]
```

### ドキュメント
エージェントまたはユーザーに関連付けることができるテキストまたはデータオブジェクト。ドキュメントはベクトル化され、エージェントの対話中にセマンティック検索と取得を可能にするベクトルデータベースに保存されます。

```mermaid
graph LR
    Documents[Documents] --> VectorDatabase[Vector Database]
    Documents --> SemanticSearch[Semantic Search]
    Documents --> AgentsOrUsers[Agents or Users]
```

### 実行
特定の入力で開始されたタスクのインスタンス。実行には独自のライフサイクルと状態マシンがあり、長時間実行されるプロセスの監視、管理、および再開が可能です。

```mermaid
graph LR
    Executions[Executions] --> Tasks[Tasks]
    Executions --> Lifecycle[Lifecycle]
    Executions --> Monitoring[Monitoring]
    Executions --> Management[Management]
    Executions --> Resumption[Resumption]
```

これらの概念とその相互作用の詳細な説明については、[概念ドキュメント](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md)を参照してください。

## タスクの理解

タスクはJulepのワークフローシステムのコアです。これにより、エージェントが実行できる複雑な多段階のAIワークフローを定義できます。タスクコンポーネントの概要は次のとおりです：

- **名前と説明**：各タスクには、簡単に識別できるように一意の名前と説明があります。
- **主要なステップ**：タスクのコアであり、実行されるアクションのシーケンスを定義します。
- **ツール**：タスク実行中にエージェントの能力を拡張するオプションの統合。

### ワークフローステップの種類

Julepのタスクには、さまざまな種類のステップを含めることができます：

1. **プロンプト**：AIモデルにメッセージを送信し、応答を受け取ります。
   ```python
   {"prompt": "Analyze the following data: {{data}}"}
   ```

2. **ツール呼び出し**：統合されたツールまたはAPIを実行します。
   ```python
   {"tool": "web_search", "arguments": {"query": "Latest AI developments"}}
   ```

3. **評価**：計算を実行するか、データを操作します。
   ```python
   {"evaluate": {"average_score": "sum(scores) / len(scores)"}}
   ```

4. **条件ロジック**：条件に基づいてステップを実行します。
   ```python
   {"if": "score > 0.8", "then": [...], "else": [...]}
   ```

5. **ループ**：データを反復処理するか、ステップを繰り返します。
   ```python
   {"foreach": {"in": "data_list", "do": [...]}}
   ```

| ステップ名          | 説明                                                                                      | 入力                                                |
|--------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **プロンプト**         | AIモデルにメッセージを送信し、応答を受け取ります。                                           | プロンプトテキストまたはテンプレート                              |
| **ツール呼び出し**      | 統合されたツールまたはAPIを実行します。                                                               | ツール名と引数                              |
| **評価**       | 計算を実行するか、データを操作します。                                                         | 評価する式または変数                |
| **入力待ち** | 入力が受信されるまでワークフローを一時停止します。                                                          | 必要なユーザーまたはシステム入力                    |
| **ログ**            | 指定された値またはメッセージを記録します。                                                                | 記録するメッセージまたは値                              |
| **埋め込み**          | テキストを特定の形式またはシステムに埋め込みます。                                                    | 埋め込むテキストまたはコンテンツ                             |
| **検索**         | クエリに基づいてドキュメント検索を実行します。                                                     | 検索クエリ                                         |
| **取得**            | キー値ストアから値を取得します。                                                        | キー識別子                                       |
| **設定**            | キー値ストアのキーに値を割り当てます。                                                   | 割り当てるキーと値                              |
| **並列**       | 複数のステップを並行して実行します。                                                                  | 同時に実行するステップのリスト              |
| **反復**        | コレクションを反復処理し、各アイテムに対してステップを実行します。                                      | 反復するコレクションまたはリスト                   |
| **マップリデュース**      | コレクションをマップし、式に基づいて結果をリデュースします。                            | マップおよびリデュースするコレクションと式             |
| **条件分岐**        | 条件に基づいてステップを実行します。                                           | 評価する条件                                |
| **スイッチ**         | 複数の条件に基づいてステップを実行します。スイッチケース文に似ています。                  | 複数の条件と対応するステップ          |
| **生成**          | サブワークフローを実行し、その完了を待ちます。                                                     | サブワークフロー識別子と入力データ                |
| **エラー**          | エラーメッセージを指定してエラーを処理します。                                                   | エラーメッセージまたは処理指示               |
| **スリープ**          | 指定された期間ワークフローを一時停止します。                                                    | 期間（秒、分など）                    |
| **リターン**         | ワークフローから値を返します。                                                                | 返す値                                       |

各ステップタイプの詳細情報と高度な使用法については、[タスクドキュメント](https://docs.julep.ai/tasks)を参照してください。

## 高度な機能

Julepは、AIワークフローを強化するための高度な機能を提供します：

### エージェントにツールを追加する

外部ツールやAPIを統合してエージェントの能力を拡張します：

```python
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "google",
        "method": "search",
        "setup": {"api_key": "your_google_api_key"},
    },
)
```

### セッションとユーザーの管理

Julepは、持続的なインタラクションのための強力なセッション管理を提供します：

```python
session = client.sessions.create(
    agent_id=agent.id,
    user_id="user123",
    context_overflow="adaptive"
)

# 同じセッションで会話を続ける
response = client.sessions.chat(
    session_id=session.id,
    message="Follow up on our previous conversation."
)
```

### ドキュメントの統合と検索

エージェントのためのドキュメントを簡単に管理および検索します：

```python
# ドキュメントをアップロードする
document = client.documents.create(
    file="path/to/document.pdf",
    metadata={"category": "research_paper"}
)

# ドキュメントを検索する
results = client.documents.search(
    query="AI advancements",
    filter={"category": "research_paper"}
)
```

高度な機能と詳細な使用法については、[高度な機能ドキュメント](https://docs.julep.ai/advanced-features)を参照してください。

## SDKリファレンス

- [Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)
- [Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)

## APIリファレンス

エージェント、タスク、および実行について詳しく学ぶために、包括的なAPIドキュメントを探索してください：

- [エージェントAPI](https://api.julep.ai/api/docs#tag/agents)
- [タスクAPI](https://api.julep.ai/api/docs#tag/tasks)
- [実行API](https://api.julep.ai/api/docs#tag/executions)

## 例とチュートリアル

提供された例を基にして始めるのに役立つ例のプロジェクトとチュートリアルを見つけてください：

- [例のプロジェクト](https://github.com/julep-ai/julep/tree/main/examples)
- [チュートリアル](https://docs.julep.ai/tutorials)

## 貢献

プロジェクトへの貢献を歓迎します！貢献方法と行動規範を学びましょう：

- [貢献ガイドライン](https://github.com/julep-ai/julep/blob/main/CONTRIBUTING.md)
- [行動規範](https://github.com/julep-ai/julep/blob/main/CODE_OF_CONDUCT.md)

## サポートとコミュニティ

コミュニティに参加して、助けを得たり、質問したり、アイデアを共有したりしましょう：

- [Discord](https://discord.com/invite/JTSBGRZrzj)
- [GitHub Discussions](https://github.com/julep-ai/julep/discussions)
- [Twitter](https://twitter.com/julep_ai)

## ライセンス

このプロジェクトは[Apache License 2.0](https://github.com/julep-ai/julep/blob/main/LICENSE)の下でライセンスされています。

## 謝辞

貴重なリソースと貢献を提供してくれたすべての貢献者とオープンソースコミュニティに感謝します。
