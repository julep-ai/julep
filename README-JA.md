<sup>[English](README.md) | [中文翻译](README-CN.md) | [日本語翻訳](README-JA.md) | [French](README-FR.md)</sup>

<div align="center" id="top">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20AI%20agents%20and%20multi-step%20tasks&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&theme=Auto" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow">ドキュメントを見る</a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">不和</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">リンクトイン</a>
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
> 👨‍💻 devfest.ai イベントに参加しませんか? [Discord](https://discord.com/invite/JTSBGRZrzj) に参加して、以下の詳細を確認してください。
>
> API キーを [こちら](https://dashboard-dev.julep.ai) から取得します。

<details>
<summary><b>🌟 貢献者とDevFest.AI参加者</b>（クリックして拡大）</summary>

## 🌟 貢献者を募集します!

Julep プロジェクトに新しい貢献者を迎えられることを嬉しく思います。プロジェクトを始めるのに役立つ「最初の良い問題」をいくつか作成しました。貢献する方法は次のとおりです。

1. 貢献方法に関するガイドラインについては、[CONTRIBUTING.md](https://github.com/julep-ai/julep/blob/dev/CONTRIBUTING.md) ファイルをご覧ください。
2. [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) を参照して、興味のあるタスクを見つけます。
3. ご質問やご不明な点がございましたら、[Discord](https://discord.com/invite/JTSBGRZrzj) チャンネルまでお気軽にお問い合わせください。

あなたの貢献は、大小を問わず私たちにとって貴重です。一緒に素晴らしいものを作りましょう！🚀

### 🎉 DevFest.AI 2024年10月

嬉しいニュースです！2024 年 10 月を通して DevFest.AI に参加します！🗓️

- このイベント中に Julep に貢献すると、素晴らしい Julep のグッズや景品を獲得するチャンスが得られます! 🎁
- 世界中の開発者とともに AI リポジトリに貢献し、素晴らしいイベントに参加しましょう。
- この素晴らしい取り組みを企画してくださった DevFest.AI に心から感謝します。

> [!ヒント]
> 楽しみに参加する準備はできましたか? **[参加することをツイート](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)**して、コーディングを始めましょう! 🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table of Contents</h3>

- [主な特徴](#%E4%B8%BB%E3%81%AA%E7%89%B9%E5%BE%B4)
- [簡単な例](#%E7%B0%A1%E5%8D%98%E3%81%AA%E4%BE%8B)
- [インストール](#%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB)
- [Python クイックスタート 🐍](#python-%E3%82%AF%E3%82%A4%E3%83%83%E3%82%AF%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%88-)
- [Node.js Quick Start 🟩](#nodejs-quick-start-)
  - [Step 1: Create an Agent](#step-1-create-an-agent)
- [Components](#components)
  - [Mental Model](#mental-model)
- [Concepts](#concepts)
- [Understanding Tasks](#understanding-tasks)
  - [Lifecycle of a Task](#lifecycle-of-a-task)
  - [Types of Workflow Steps](#types-of-workflow-steps)
- [Tool Types](#tool-types)
  - [User-defined `functions`](#user-defined-functions)
  - [`system` tools](#system-tools)
  - [Built-in `integrations`](#built-in-integrations)
  - [Direct `api_calls`](#direct-api_calls)
- [Integrations](#integrations)
- [Other Features](#other-features)
  - [Adding Tools to Agents](#adding-tools-to-agents)
  - [Managing Sessions and Users](#managing-sessions-and-users)
  - [Document Integration and Search](#document-integration-and-search)
  - [SDK リファレンス](#sdk-%E3%83%AA%E3%83%95%E3%82%A1%E3%83%AC%E3%83%B3%E3%82%B9)
  - [API リファレンス](#api-%E3%83%AA%E3%83%95%E3%82%A1%E3%83%AC%E3%83%B3%E3%82%B9)
- [ローカルクイックスタート](#%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E3%82%AF%E3%82%A4%E3%83%83%E3%82%AF%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%88)
- [Julep と LangChain などの違いは何ですか?](#julep-%E3%81%A8-langchain-%E3%81%AA%E3%81%A9%E3%81%AE%E9%81%95%E3%81%84%E3%81%AF%E4%BD%95%E3%81%A7%E3%81%99%E3%81%8B)
  - [さまざまなユースケース](#%E3%81%95%E3%81%BE%E3%81%96%E3%81%BE%E3%81%AA%E3%83%A6%E3%83%BC%E3%82%B9%E3%82%B1%E3%83%BC%E3%82%B9)
  - [異なるフォームファクタ](#%E7%95%B0%E3%81%AA%E3%82%8B%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0%E3%83%95%E3%82%A1%E3%82%AF%E3%82%BF)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

＃＃ 導入

Julep は、過去のやり取りを記憶し、複雑なタスクを実行できる AI エージェントを作成するためのプラットフォームです。長期記憶を提供し、複数ステップのプロセスを管理します。

Julep を使用すると、意思決定、ループ、並列処理、多数の外部ツールや API との統合を組み込んだ複数ステップのタスクを作成できます。

多くの AI アプリケーションは、最小限の分岐によるプロンプトと API 呼び出しの単純な線形チェーンに制限されていますが、Julep は次のようなより複雑なシナリオを処理できるように構築されています。

- 複数のステップがある、
- モデルの出力に基づいて意思決定を行う
- 平行枝を生成し、
- たくさんのツールを使い、
- 長時間走る。

> [!ヒント]
> 単純な質問に答えるだけでなく、複雑なタスクを処理し、過去のやり取りを記憶し、場合によっては他のツールや API も使用できる AI エージェントを構築したいとします。そこで Julep の出番です。詳細については、[タスクの理解](#understanding-tasks) をお読みください。

## 主な特徴

1. 🧠 **永続的な AI エージェント**: 長期にわたるやり取りを通じてコン​​テキストと情報を記憶します。
2. 💾 **ステートフル セッション**: 過去のやり取りを追跡して、パーソナライズされた応答を提供します。
3. 🔄 **複数ステップのタスク**: ループと意思決定を含む複雑な複数ステップのプロセスを構築します。
4. ⏳ **タスク管理**: 無期限に実行される可能性のある長時間実行タスクを処理します。
5. 🛠️ **組み込みツール**: タスクで組み込みツールと外部 API を使用します。
6. 🔧 **自己修復**: Julep は失敗したステップを自動的に再試行し、メッセージを再送信し、タスクがスムーズに実行されるようにします。
7. 📚 **RAG**: Julep のドキュメント ストアを使用して、独自のデータを取得して使用するためのシステムを構築します。

![機能](https://github.com/user-attachments/assets/4355cbae-fcbd-4510-ac0d-f8f77b73af70)

> [!ヒント]
> Julep は、単純なプロンプト応答モデルを超えた AI ユースケースを必要とするアプリケーションに最適です。

## 簡単な例

次のことができる研究 AI エージェントを想像してください。

1. **トピックを選ぶ**、
2. そのトピックについて**100個の検索クエリを考え出す**
3. ウェブ検索を並行して実行する
4. 結果を**要約**します。
5. **要約を Discord に送信**します。

> [!注意]
> Julepでは、これは単一のタスクになります<b>80行のコード</b>そして走る<b>完全に管理された</b>すべて自動的に行われます。すべての手順は Julep の独自のサーバー上で実行されるため、何もする必要はありません。

実際の例を次に示します。

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
        api_key: BSAqES7dj9d... # dummy key

  - name: discord_webhook
    type: api_call
    api_call:
      url: https://eobuxj02se0n.m.pipedream.net # dummy requestbin
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

この例では、Julep は並列実行を自動的に管理し、失敗したステップを再試行し、API リクエストを再送信し、タスクが完了するまで確実に実行し続けます。

> これは 30 秒以内に実行され、次の出力を返します。

<details>
<summary><b>AIに関する研究概要</b> <i>（クリックして拡大）</i></summary>

> **AIに関する研究概要**
>
> ### 人工知能（AI）に関する研究成果の概要
>
> #### はじめに
>
> 人工知能 (AI) の分野は近年、機械が環境を認識し、データから学習し、意思決定を行える方法とテクノロジーの開発により、大きな進歩を遂げています。この概要では、AI に関連するさまざまな研究結果から得られた洞察に主に焦点を当てています。
>
> #### 主な調査結果
>
> 1. **AIの定義と範囲**:
>
> - AI は、学習、推論、問題解決など、人間のような知能を必要とするタスクを実行できるシステムの作成に重点を置いたコンピューター サイエンスの分野として定義されています (Wikipedia)。
> - 機械学習、自然言語処理、ロボット工学、コンピュータービジョンなど、さまざまなサブフィールドを網羅しています。
>
> 2. **影響と応用**:
>
> - AI テクノロジーはさまざまな分野に統合され、効率性と生産性を向上させています。その応用範囲は、自律走行車やヘルスケア診断から顧客サービスの自動化や財務予測まで多岐にわたります (OpenAI)。
> - AI をすべての人にとって有益なものにするという Google の取り組みは、さまざまなプラットフォームでユーザー エクスペリエンスを強化することで日常生活を大幅に改善する可能性を強調しています (Google AI)。
>
> 3. **倫理的配慮**:
>
> - プライバシー、偏見、意思決定プロセスの説明責任に関する懸念など、AI の倫理的影響に関する議論が続いています。AI 技術の安全で責任ある使用を保証するフレームワークの必要性が強調されています (OpenAI)。
>
> 4. **学習メカニズム**:
>
> - AI システムは、教師あり学習、教師なし学習、強化学習などのさまざまな学習メカニズムを活用します。これらの方法により、AI は過去の経験やデータから学習することで、時間の経過とともにパフォーマンスを向上させることができます (Wikipedia)。
> - 教師あり学習と教師なし学習の区別は重要です。教師あり学習はラベル付きデータに依存しますが、教師なし学習は事前定義されたラベルなしでパターンを識別します (教師なし)。
>
> 5. **今後の方向性**:
> - 今後の AI 開発では、AI システムの解釈可能性と透明性を高め、正当な判断と行動を提供できるようにすることに重点が置かれると予想されます (OpenAI)。
> - AI システムをよりアクセスしやすく、ユーザーフレンドリーなものにし、さまざまな人口統計や業界での幅広い導入を促進する動きもあります (Google AI)。
>
> #### 結論
>
> AI は複数の領域に変革をもたらす力を持ち、産業の再構築や生活の質の向上が期待されています。しかし、AI の機能が拡大するにつれて、倫理的および社会的影響に対処することが極めて重要になります。AI の将来像を見据えるには、技術者、倫理学者、政策立案者による継続的な研究と協力が不可欠です。

</details>

## インストール

Julep を使い始めるには、[npm](https://www.npmjs.com/package/@julep/sdk) または [pip](https://pypi.org/project/julep/) を使用してインストールします。

**Node.js**:

```bash
npm install @julep/sdk

# or

bun add @julep/sdk
```

**Python**:

```bash
pip install julep
```

> [!注意]
> API キーを [こちら](https://dashboard-dev.julep.ai) から取得します。
>
> ベータ版では、[Discord](https://discord.com/invite/JTSBGRZrzj) に連絡して、API キーのレート制限を解除することもできます。

> [!ヒント]
> 💻 あなたは「コードを見せてください!™」タイプの人ですか? 始めるにあたって役立つクックブックを多数作成しました。**[クックブック](https://github.com/julep-ai/julep/tree/dev/cookbooks)** をチェックして、例を参照してください。
>
> 💡 Julep をベースに構築できるアイデアもたくさんあります。**[アイデアのリスト](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** をチェックして、インスピレーションを得てください。

## Python クイックスタート 🐍

````python
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
          Based on the idea '{{_.idea}}', generate a list of 5 plot ideas. Go crazy and be as creative as possible. Return your output as a list of long strings inside ```応答の最後に yaml タグを追加します。
アンラップ: true

- 評価する：
plot_ideas: load_yaml(_.split('```yaml')[1].split('```')[0].ストリップ())

# ステップ2: プロットのアイデアから研究分野を抽出する
- プロンプト：
- 役割: システム
内容: あなたは {{agent.name}} です。 {{agent.about}}
- 役割: ユーザー
内容: >
ストーリーのプロットのアイデアをいくつか紹介します。
{% for idea in _.plot_ideas %}
- {{アイデア}}
{% endfor %}

ストーリーを展開するには、プロットのアイデアをリサーチする必要があります。
何を研究すべきでしょうか? 興味深いと思うプロットのアイデアについて、Wikipedia の検索クエリを書き留めてください。
出力をyamlリストとして返します```yaml tags at the end of your response.
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
          Then finally write the plot as a yaml object inside ```レスポンスの最後に yaml タグを追加します。yaml オブジェクトの構造は次のようになります。

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

yaml が有効であり、文字とシーンが空でないことを確認してください。また、セミコロンや yaml の記述に関するその他の注意点にも注意してください。
アンラップ: true

- 評価する：
プロット: "load_yaml(_.split('```yaml')[1].split('```')[0].strip())"
"""

タスク = client.tasks.create(
エージェントID=エージェントID、
**yaml.safe_load(タスクyaml)
)

### ステップ3: タスクを実行する

実行 = client.executions.create(
タスクID=タスクID、
input={"idea": "飛ぶことを学ぶ猫"}
)

# 🎉 ストーリーと漫画パネルが生成される様子をご覧ください
while (result := client.executions.get(execution.id)).status が ['succeeded', 'failed'] の範囲外です:
print(結果.ステータス、結果.出力)
時間.睡眠(1)

# 📦 実行が完了したら、結果を取得します
result.status == "成功"の場合:
print(結果.出力)
それ以外：
例外(結果.エラー)を発生させる
````

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

```ジャバスクリプト
// ステップ 0: セットアップ
dotenv は、次のコードで定義されます。
Julep の SDK を実装するには、次の手順に従ってください。
yaml を require します。

config() を呼び出します。

constクライアント = 新しいジュレップ({
APIキー: process.env.JULEP_API_KEY、
環境: process.env.JULEP_ENVIRONMENT || "production",
});

/* ステップ 1: エージェントを作成する */

非同期関数createAgent() {
const エージェント = クライアント.エージェント.作成を待機します({
名前: 「ストーリーテリングエージェント」
モデル: "claude-3.5-sonnet",
について：
「あなたは、さまざまなトピックについて魅力的なストーリーを作り上げることができる創造的なストーリーテラーです。」
  });
返品エージェント;
}

/* ステップ 2: ストーリーと漫画を生成するタスクを作成する */

const タスクYaml = `
名前: ストーリーテラー
説明: アイデアに基づいてストーリーを作成します。

ツール:
- 名前: research_wikipedia
統合：
提供元: wikipedia
方法: 検索

主要：
# ステップ1: プロットのアイデアを生み出す
- プロンプト：
- 役割: システム
内容: あなたは {{agent.name}} です。 {{agent.about}}
- 役割: ユーザー
内容: >
アイデア「{{_.idea}}」に基づいて、5 つのプロット アイデアのリストを生成します。自由に創造的に考えてください。出力は、応答の最後に \`\`\`yaml タグ内の長い文字列のリストとして返されます。
アンラップ: true

- 評価する：
plot_ideas: load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

# ステップ2: プロットのアイデアから研究分野を抽出する
- プロンプト：
- 役割: システム
内容: あなたは {{agent.name}} です。 {{agent.about}}
- 役割: ユーザー
内容: >
ストーリーのプロットのアイデアをいくつか紹介します。
{% for idea in _.plot_ideas %}
- {{アイデア}}
{% endfor %}

ストーリーを展開するには、プロットのアイデアをリサーチする必要があります。
何を研究すべきでしょうか? 興味深いと思うプロットのアイデアについて、Wikipedia の検索クエリを書き留めてください。
応答の最後に、\`\`\`yaml タグ内の yaml リストとして出力を返します。
アンラップ: true
設定：
モデル: gpt-4o-mini
温度: 0.7

- 評価する：
リサーチクエリ: load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

# ステップ3: 各プロットのアイデアをリサーチする
- 各:
in: _.research_queries
する：
ツール: research_wikipedia
引数:
クエリ: _

- 評価する：
wikipedia_results: 'NEWLINE.join([f"- {doc.metadata.title}: {doc.metadata.summary}" for item in _ for doc in item.documents])'

# ステップ4: 考えて熟考する
- プロンプト：
- 役割: システム
内容: あなたは {{agent.name}} です。 {{agent.about}}
- 役割: ユーザー
内容: |-
物語を書く前に、考え、熟考してみましょう。ここにいくつかのプロットのアイデアがあります:
{% 出力[1].plot_ideas のアイデア %}
- {{アイデア}}
{% endfor %}

Wikipedia でプロットのアイデアを調査した結果は次のとおりです。
{{_.wikipedia_results}}

プロットのアイデアを批判的に考えます。プロットのアイデアと Wikipedia の結果を組み合わせて、ストーリーの詳細なプロットを作成します。
メモや考えをすべて書き留めてください。
最後に、レスポンスの最後にある \`\`\`yaml タグ内に yaml オブジェクトとしてプロットを記述します。yaml オブジェクトの構造は次のようになります。

\`\`\`yaml
タイトル： "<string>"
文字:
- 名前： "<string>"
について： "<string>"
概要: "<string>"
シーン:
- タイトル： "<string>"
説明： "<string>"
文字:
- 名前： "<string>"
役割： "<string>"
ストーリーライン:
            - "<string>「\`\`\`

yaml が有効であり、文字とシーンが空でないことを確認してください。また、セミコロンや yaml の記述に関するその他の注意点にも注意してください。
アンラップ: true

- 評価する：
プロット: "load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())"
`;

非同期関数createTask(agentId) {
const タスク = client.tasks.create(agentId, yaml.parse(taskYaml)) を待機します。
タスクを返す。
}

/* ステップ 3: タスクを実行する */

非同期関数executeTask(taskId) {
const 実行 = クライアントの実行の作成を待機します(taskId、{
入力: { アイデア: 「飛ぶことを学ぶ猫」 },
  });

// 🎉 ストーリーと漫画パネルが生成される様子をご覧ください
（真）の間{
const 結果 = client.executions.get(execution.id); を待機します。
console.log(結果のステータス、結果の出力);

if (result.status === "成功" || result.status === "失敗") {
// 📦 実行が終了したら、結果を取得します
if (result.status === "成功") {
console.log(結果の出力);
} それ以外 {
新しいエラーをスローします(result.error);
      }
壊す;
    }

新しい Promise((resolve) => setTimeout(resolve, 1000)) を待機します。
  }
}

// 例を実行するためのメイン関数
非同期関数main() {
試す {
const エージェント = createAgent() を待機します。
const タスク = createTask(agent.id);
タスクの実行を待機します(task.id);
} キャッチ（エラー）{
console.error("エラーが発生しました:", error);
  }
}

主要（）
.then(() => console.log("完了"))
.catch(コンソール.エラー);
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

```マーメイド
グラフTD
ユーザー[ユーザー] ==> セッション[セッション]
セッション --> エージェント[エージェント]
エージェント --> タスク[タスク]
エージェント --> LLM[大規模言語モデル]
タスク --> ツール[ツール]
エージェント --> ドキュメント[ドキュメント]
ドキュメント --> VectorDB[ベクターデータベース]
タスク --> 実行[実行]

classDef client fill:#9ff、stroke:#333、stroke-width:1px;
クラス User クライアント;

classDef core fill:#f9f、stroke:#333、stroke-width:2px;
クラス Agent、Tasks、Session コア;
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

```マーメイド
シーケンス図
参加者Dをあなたのコードとして
参加者C（ジュレップクライアント）
参加者Sはジュレップサーバーとして

D->>C: タスクの作成
C->>S: 実行を送信
Sの上のメモ: タスクの実行
Sに関する注意: 状態の管理
S-->>C: 実行イベント
C-->>D: 進捗状況の更新
S->>C: 実行完了
C->>D: 最終結果
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

```ヤム
- プロンプト: 「次のデータを分析してください: {{agent.name}}」 # <-- これは jinja テンプレートです
```

```ヤム
- プロンプト：
- 役割: システム
内容: 「あなたは {{agent.name}} です。 {{agent.about}}」
- 役割: ユーザー
内容: 「次のデータを分析します: {{_.data}}」
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

```ヤム
- ツール: web_search
引数:
クエリ: '"最新の AI 開発"' # <-- これは Python 式です (引用符に注意してください)
num_results: len(_.topics) # <-- リストの長さにアクセスするための Python 式
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

```ヤム
- 評価する：
average_score: 合計(スコア) / 長さ(スコア)
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

```ヤム
- 入力待ち:
情報：
メッセージ: '"{_.required_info} に関する追加情報を提供してください。"' # <-- コンテキスト変数にアクセスするための Python 式
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

```ヤム
- ログ: "アイテム {{_.item_id}} の処理が完了しました" # <-- コンテキスト変数にアクセスするための jinja テンプレート
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

```ヤム
- 取得: user_preference
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

```ヤム
- セット：
user_preference: '"dark_mode"' # <-- python 式
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

```ヤム
- 各:
in: _.data_list # <-- コンテキスト変数にアクセスするための Python 式
する：
- ログ: "アイテム {{_.item}} を処理しています" # <-- コンテキスト変数にアクセスするための jinja テンプレート
```

</td>
</tr>
<tr>
<td> <b>Map-Reduce</b> </td>
<td>
Map over a collection and reduce the results

</td>

<td>

```ヤム
- マップリデュース:
over: _.numbers # <-- コンテキスト変数にアクセスするための Python 式
地図：
- 評価する：
二乗: "_ ** 2"
Reduce: 結果 + [_] # <-- (オプション) 結果を削減する Python 式。省略した場合、これがデフォルトになります。
```

```ヤム
- マップリデュース:
以上: _.topics
地図：
- プロンプト: {{_}} に関するエッセイを書く
並列度: 10
```

</td>
</tr>
<tr>
<td> <b>Parallel</b> </td>
<td>
Run multiple steps in parallel

</td>

<td>

```ヤム
- 平行：
- ツール: web_search
引数:
クエリ: 「AI ニュース」
- ツール: weather_check
引数:
場所: '"ニューヨーク"'
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

```ヤム
- if: _.score > 0.8 # <-- Python 式
それから：
- ログ: 高得点を達成
それ以外：
- エラー: スコアの改善が必要です
```

</td>
</tr>
<tr>
<td> <b>Switch</b> </td>
<td>
Execute steps based on multiple conditions

</td>

<td>

```ヤム
- スイッチ:
- ケース: _.category == 'A'
それから：
- ログ: 「カテゴリー A 処理」
- ケース: _.category == 'B'
それから：
- ログ: 「カテゴリー B 処理」
- case: _ # デフォルトのケース
それから：
- エラー: 不明なカテゴリ
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

```ヤム
- 寝る：
秒: 30
分数: 1
時間数: 1
日数: 1
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

```ヤム
- 戻る：
結果: '"タスクは正常に完了しました"' # <-- Python 式
time: datetime.now().isoformat() # <-- python 式
```

</td>
</tr>
<tr>
<td> <b>Yield</b> </td>
<td>
Run a subworkflow and await its completion

</td>

<td>

```ヤム
- 収率：
ワークフロー: process_data
引数:
input_data: _.raw_data # <-- Python式
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

```ヤム
- エラー:「無効な入力が提供されています」# <-- 文字列のみ
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

```ヤム
名前: システムツールタスクの例
説明: システムコールを使用してエージェントを一覧表示する

ツール:
- 名前: send_notification
説明: ユーザーに通知を送信する
タイプ: 関数
関数：
パラメータ:
タイプ: オブジェクト
プロパティ:
文章：
タイプ: 文字列
説明: 通知の内容

主要：
- ツール: send_notification
引数:
内容: '"hi"' # <-- Python 式
```

Whenever julep encounters a _user-defined function_, it pauses, giving control back to the client and waits for the client to run the function call and give the results back to julep.

> [!TIP] > **Example cookbook**: [cookbooks/13-Error_Handling_and_Recovery.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/13-Error_Handling_and_Recovery.py)

### `system` tools

Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.

`system` tools are built into the backend. They get executed automatically when needed. They do _not_ require any action from the client-side.

For example,

```ヤム
名前: システムツールタスクの例
説明: システムコールを使用してエージェントを一覧表示する

ツール:
- 名前: list_agent_docs
説明: 指定されたエージェントのすべてのドキュメントを一覧表示します
タイプ: システム
システム：
リソース: エージェント
サブリソース: doc
操作: リスト

主要：
- ツール: list_agents
引数:
制限: 10 # <-- Python式
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

> [!TIP] > **Example cookbook**: [cookbooks/10-Document_Management_and_Search.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/10-Document_Management_and_Search.py)

### Built-in `integrations`

Julep comes with a number of built-in integrations (as described in the section below). `integration` tools are directly executed on the julep backend. Any additional parameters needed by them at runtime can be set in the agent/session/user's `metadata` fields.

See [Integrations](#integrations) for details on the available integrations.

> [!TIP] > **Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)

### Direct `api_calls`

julep can also directly make api calls during workflow executions as tool calls. Same as `integration`s, additional runtime parameters are loaded from `metadata` fields.

For example,

```ヤム
名前: api_callタスクの例
ツール:
- タイプ: api_call
名前: こんにちは
API呼び出し:
メソッド: GET
URL: https://httpbin.org/get

主要：
- ツール: こんにちは
引数:
書式:
test: _.input # <-- Python式
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

```ヤム
設定：
api_key: 文字列 # Brave SearchのAPIキー

引数:
query: 文字列 # Braveで検索するための検索クエリ

出力：
result: 文字列 # Brave Searchの結果
```

</td>

<td>

**Example cookbook**: [cookbooks/03-SmartResearcher_With_WebSearch.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/03-SmartResearcher_With_WebSearch.ipynb)

</td>
</tr>
<tr>
<td> <b>BrowserBase</b> </td>
<td>

```ヤム
設定：
api_key: 文字列 # BrowserBaseのAPIキー
project_id: 文字列 # BrowserBase のプロジェクト ID
session_id: 文字列 # (オプション) BrowserBaseのセッションID

引数:
urls: list[string] # BrowserBaseで読み込むURL

出力：
ドキュメント: リスト # URLから読み込まれたドキュメント
```

</td>

</tr>
<tr>
<td> <b>Email</b> </td>
<td>

```ヤム
設定：
ホスト: 文字列 # メールサーバーのホスト
port: 整数 # メールサーバーのポート
user: 文字列 # メールサーバーのユーザー名
パスワード: 文字列 # メールサーバーのパスワード

引数:
to: 文字列 # メールを送信するメールアドレス
from: 文字列 # メールを送信するメールアドレス
subject: 文字列 # メールの件名
body: 文字列 # メールの本文

出力：
success: boolean # メールが正常に送信されたかどうか
```

</td>

<td>

**Example cookbook**: [cookbooks/00-Devfest-Email-Assistant.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/00-Devfest-Email-Assistant.ipynb)

</td>
</tr>
<tr>
<td> <b>Spider</b> </td>
<td>

```ヤム
設定：
spider_api_key: 文字列 # SpiderのAPIキー

引数:
url: 文字列 # データを取得するURL
mode: 文字列 # クローラーのタイプ (デフォルト: "scrape")
params: dict # (オプション) Spider APIのパラメータ

出力：
ドキュメント: リスト # スパイダーから返されたドキュメント
```

</td>

<td>

**Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)

</td>
</tr>
<tr>
<td> <b>Weather</b> </td>
<td>

```ヤム
設定：
openweathermap_api_key: 文字列 # OpenWeatherMapのAPIキー

引数:
location: 文字列 # 気象データを取得する場所

出力：
結果: 文字列 # 指定された場所の天気データ
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

```ヤム
引数:
query: 文字列 # 検索クエリ文字列
load_max_docs: 整数 # 読み込むドキュメントの最大数 (デフォルト: 2)

出力：
ドキュメント: リスト # Wikipedia 検索から返されたドキュメント
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

```パイソン
クライアント.エージェント.ツール.作成(
エージェントID=エージェントID、
名前="ウェブ検索",
description="Web で情報を検索します。",
統合={
「プロバイダー」：「勇敢な」、
"メソッド": "検索",
"セットアップ": {"api_key": "your_brave_api_key"},
    },
)
```

### Managing Sessions and Users

Julep provides robust session management for persistent interactions:

```パイソン
セッション = client.sessions.create(
エージェントID=エージェントID、
user_id=ユーザーID、
context_overflow="適応型"
)

# 同じセッションで会話を続ける
レスポンス = client.sessions.chat(
セッションID=セッションID、
メッセージ=[
      {
「役割」: 「ユーザー」、
"content": "前回の会話をフォローアップします。"
      }
    ]
)
```

### Document Integration and Search

Easily manage and search through documents for your agents:

```パイソン
# ドキュメントをアップロードする
ドキュメント = client.agents.docs.create(
title="AIの進歩",
content="AI は世界を変えています...",
メタデータ = {"カテゴリ": "研究論文"}
)

# ドキュメントを検索
結果 = client.agents.docs.search(
text="AIの進歩",
metadata_filter={"category": "研究論文"}
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

＃＃ 参照

### SDK リファレンス

- **Node.js** [SDK リファレンス](https://github.com/julep-ai/node-sdk/blob/main/api.md) | [NPM パッケージ](https://www.npmjs.com/package/@julep/sdk)
- **Python** [SDK リファレンス](https://github.com/julep-ai/python-sdk/blob/main/api.md) | [PyPI パッケージ](https://pypi.org/project/julep/)

### API リファレンス

エージェント、タスク、実行の詳細については、API ドキュメントをご覧ください。

- [エージェント API](https://dev.julep.ai/api/docs#tag/agents)
- [タスク API](https://dev.julep.ai/api/docs#tag/tasks)
- [実行API](https://dev.julep.ai/api/docs#tag/executions)

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## ローカルクイックスタート

**要件**：

- 最新の docker compose がインストールされている

**手順**:

1. `git clone https://github.com/julep-ai/julep.git`
2. `cd ジュレップ`
3. `docker volume create cozo_backup`
4. `docker volume create cozo_data`
5. `cp .env.example .env # <-- このファイルを編集します`
6. `docker compose --env-file .env --profile temporal-ui --profile single-tenant --profile self-hosted-db up --build`

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

---

## Julep と LangChain などの違いは何ですか?

### さまざまなユースケース

LangChain と Julep は、AI 開発スタック内で異なる重点を置いたツールと考えてください。

LangChain は、プロンプトのシーケンスを作成し、LLM とのやり取りを管理するのに最適です。多数の事前構築された統合を備えた大規模なエコシステムを備えているため、何かをすぐに起動して実行したい場合に便利です。LangChain は、プロンプトと API 呼び出しの線形チェーンを含む単純なユースケースに適しています。

一方、Julep は、長期的なインタラクションでコンテキストを維持できる永続的な AI エージェントの構築に重点を置いています。複数ステップのタスク、条件付きロジック、エージェントのプロセス内で直接さまざまなツールや API との統合を伴う複雑なワークフローが必要な場合に効果を発揮します。永続的なセッションと複雑なワークフローを管理するために、ゼロから設計されています。

以下のことが必要となる複雑な AI アシスタントの構築を考えている場合には、Julep を使用してください。

- 数日または数週間にわたってユーザーのインタラクションを追跡します。
- 毎日のサマリーの送信やデータ ソースの監視などのスケジュールされたタスクを実行します。
- 以前のやり取りや保存されたデータに基づいて決定を下します。
- ワークフローの一部として複数の外部サービスと対話します。

そして、Julep は、ゼロから構築する必要なく、これらすべてをサポートするインフラストラクチャを提供します。

### 異なるフォームファクタ

Julep は、ワークフローを記述するための言語、それらのワークフローを実行するためのサーバー、およびプラットフォームと対話するための SDK を含む **プラットフォーム** です。Julep で何かを構築するには、ワークフローの説明を `YAML` で記述し、クラウドでワークフローを実行します。

Julep は、負荷の高い、複数のステップから成る、長時間実行されるワークフロー向けに構築されており、ワークフローの複雑さに制限はありません。

LangChain は、プロンプトとツールの線形チェーンを構築するためのいくつかのツールとフレームワークを含む **ライブラリ** です。LangChain を使用して何かを構築するには、通常、使用するモデル チェーンを設定して実行する Python コードを記述します。

LangChain は、プロンプトと API 呼び出しの線形チェーンを含む単純なユースケースでは十分であり、実装も迅速です。

＃＃＃ 要約すれば

ステートレスまたは短期的なコンテキストで LLM インタラクションとプロンプト シーケンスを管理する必要がある場合は、LangChain を使用します。

高度なワークフロー機能、永続的なセッション、複雑なタスク オーケストレーションを備えたステートフル エージェント用の堅牢なフレームワークが必要な場合は、Julep を選択してください。

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>
