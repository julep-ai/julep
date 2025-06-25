<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 目次</h3>

- [なぜJulepなのか？](#なぜjulepなのか)
- [はじめに](#はじめに)
- [ドキュメントと例](#ドキュメントと例)
- [コミュニティと貢献](#コミュニティと貢献)
- [ライセンス](#ライセンス)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<sup><div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  [Deutsch](https://www.readme-i18n.com/julep-ai/julep?lang=de) | 
  [Español](https://www.readme-i18n.com/julep-ai/julep?lang=es) | 
  [français](https://www.readme-i18n.com/julep-ai/julep?lang=fr) | 
  [日本語](https://www.readme-i18n.com/julep-ai/julep?lang=ja) | 
  [한국어](https://www.readme-i18n.com/julep-ai/julep?lang=ko) | 
  [Português](https://www.readme-i18n.com/julep-ai/julep?lang=pt) | 
  [Русский](https://www.readme-i18n.com/julep-ai/julep?lang=ru) | 
  [中文](https://www.readme-i18n.com/julep-ai/julep?lang=zh)
</div></sup>

<div align="center" id="top">
<img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Serverless%20AI%20Workflows%20for%20Data%20%26%20ML%20Teams&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" height=300 />

<br>
  <p>
   <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License" height="28"></a>
  </p>
  
  <h3 align="center">
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294015-47144047-25ab-417c-af1b-6746820a20ff.gif" width="60"></a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow"><img src="https://raw.githubusercontent.com/gist/IgnaceMaes/744cd9cf41ec6acf46fc8f4e9f370f86/raw/d16658c2945d30c8a953b35cb17dd7085111b46c/x-logo.svg" width="45"></a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294012-0a55e343-37ad-4b0f-924f-c8431d9d2483.gif" width="60"></a>

  </h3>
  
  <!-- <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3> -->
</div>

**今すぐJulepを試す：** **[Julepウェブサイト](https://julep.ai)** をご覧ください · **[Julepダッシュボード](https://dashboard.julep.ai)** で始める (無料APIキー) · **[ドキュメント](https://docs.julep.ai/introduction/julep)** を読む

<img src="https://raw.githubusercontent.com/anasalatasiuni/gif/main/white-line.gif">

## なぜJulepなのか？

Julepは、単純なプロンプトのチェーンをはるかに超えた**エージェントベースのAIワークフロー**を構築するためのオープンソースプラットフォームです。大規模言語モデル（LLM）とツールを使用して複雑な多段階プロセスを**インフラストラクチャの管理なしに**オーケストレーションできます。Julepを使用すると、**過去のやり取りを記憶し**、分岐ロジック、ループ、並列実行、外部APIとの統合を備えた洗練されたタスクを処理するAIエージェントを作成できます。要するに、Julepは*「AIエージェントのためのFirebase」*として機能し、スケールでのインテリジェントワークフローのための堅牢なバックエンドを提供します。

**主要機能と利点：**

* **永続メモリ：** 会話を通じてコンテキストと長期記憶を維持するAIエージェントを構築し、時間をかけて学習と改善ができます。
* **モジュラーワークフロー：** 条件ロジック、ループ、エラーハンドリングを備えたモジュラーステップとして複雑なタスクを定義します（YAMLまたはコード）。Julepのワークフローエンジンが多段階プロセスと決定を自動的に管理します。
* **ツールオーケストレーション：** 外部ツールとAPI（Web検索、データベース、サードパーティサービスなど）をエージェントのツールキットの一部として簡単に統合します。Julepのエージェントはこれらのツールを呼び出して機能を拡張し、検索拡張生成などを可能にします。
* **並列・スケーラブル：** 効率性のために複数の操作を並列で実行し、Julepにスケーリングと並行処理を任せます。プラットフォームはサーバーレスなので、追加のDevOpsオーバーヘッドなしにワークフローをシームレスにスケールします。
* **信頼性のある実行：** 不具合を心配する必要はありません - Julepは組み込まれた再試行、自己修復ステップ、堅牢なエラーハンドリングを提供し、長時間実行タスクを軌道に乗せ続けます。また、進捗を追跡するためのリアルタイム監視とログも提供します。
* **簡単な統合：** **Python**と**Node.js**向けのSDK、またはスクリプト用のJulep CLIですぐに始められます。他のシステムに直接統合したい場合は、JulepのREST APIが利用可能です。

*AIロジックと創造性に集中し、重労働はJulepにお任せください！* <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">

<img src="https://raw.githubusercontent.com/anasalatasiuni/gif/main/white-line.gif">

## はじめに
<p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="APIキーを取得" height="28">
    </a>
    <span>&nbsp;</span>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=logo=gitbook&logoColor=white" alt="ドキュメント" height="28">
    </a>
  </p>
Julepの起動と実行は簡単です：

1. **サインアップとAPIキー：** まず、[Julepダッシュボード](https://dashboard.julep.ai)にサインアップしてAPIキーを取得します（SDK呼び出しの認証に必要）。
2. **SDKのインストール：** お好みの言語でJulep SDKをインストールします：

   * <img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="20"> **Python:** `pip install julep`
   * <img src="https://user-images.githubusercontent.com/74038190/212257454-16e3712e-945a-4ca2-b238-408ad0bf87e6.gif" width="20"> **Node.js:** `npm install @julep/sdk` (または `yarn add @julep/sdk`)
3. **エージェントの定義：** SDKまたはYAMLを使用してエージェントとそのタスクワークフローを定義します。例えば、エージェントのメモリ、使用できるツール、ステップバイステップのタスクロジックを指定できます。（詳細なウォークスルーについては、ドキュメントの**[クイックスタート](https://docs.julep.ai/introduction/quick-start)**を参照してください。）
4. **ワークフローの実行：** SDKを通じてエージェントを呼び出してタスクを実行します。Julepプラットフォームがクラウドでワークフロー全体をオーケストレーションし、状態、ツール呼び出し、LLMインタラクションを管理します。エージェントの出力を確認し、ダッシュボードで実行を監視し、必要に応じて反復できます。

これで完了です！最初のAIエージェントを数分で起動して実行できます。完全なチュートリアルについては、ドキュメント内の**[クイックスタートガイド](https://docs.julep.ai/introduction/quick-start)**をご確認ください。

> **注意：** Julepはワークフローとエージェントを管理するためのコマンドラインインターface（CLI）も提供しています（現在Pythonのベータ版）。ノーコードアプローチを好む場合や一般的なタスクをスクリプト化したい場合は、詳細について[Julep CLIドキュメント](https://docs.julep.ai/responses/quickstart#cli-installation)を参照してください。

<img src="https://raw.githubusercontent.com/anasalatasiuni/gif/main/white-line.gif">

## ドキュメントと例


さらに深く学びたいですか？**[Julepドキュメント](https://docs.julep.ai)**は、コアコンセプト（エージェント、タスク、セッション、ツール）から高度なトピック（エージェントメモリ管理やアーキテクチャの内部構造）まで、プラットフォームを習得するために必要なすべてをカバーしています。主要なリソースには以下があります：

* **[コンセプトガイド](https://docs.julep.ai/concepts/)：** Julepのアーキテクチャ、セッションとメモリの仕組み、ツールの使用、長い会話の管理などについて学びます。
* **[API・SDK リファレンス](https://docs.julep.ai/api-reference/)：** JulepをアプリケーションNに統合するためのすべてのSDKメソッドとREST APIエンドポイントの詳細なリファレンスを見つけます。
* **[チュートリアル](https://docs.julep.ai/tutorials/)：** 実際のアプリケーション構築のためのステップバイステップガイド（例：Webを検索するリサーチエージェント、旅行計画アシスタント、カスタム知識を持つチャットボット）。
* **[クックブックレシピ](https://github.com/julep-ai/julep/tree/dev/cookbooks)：** 既製のワークフローとエージェントの例については**Julep Cookbook**を探索してください。これらのレシピは一般的なパターンと使用例を示しています - 例から学ぶ素晴らしい方法です。*サンプルエージェント定義については、このリポジトリの[`cookbooks/`](https://github.com/julep-ai/julep/tree/dev/cookbooks)ディレクトリを参照してください。*

<img src="https://raw.githubusercontent.com/anasalatasiuni/gif/main/white-line.gif">

<img src="https://raw.githubusercontent.com/anasalatasiuni/gif/main/white-line.gif">

## コミュニティと貢献

成長する開発者とAI愛好家のコミュニティに参加しましょう！参加とサポートを得る方法をいくつか紹介します：

* **Discordコミュニティ：** 質問やアイデアがありますか？[公式Discordサーバー](https://discord.gg/7H5peSN9QP)での会話に参加して、Julepチームや他のユーザーとチャットしましょう。トラブルシューティングのお手伝いや新しい使用例のブレインストーミングを喜んでサポートします。
* **GitHub ディスカッションとイシュー：** バグ報告、機能要求、実装詳細の議論には、GitHubを自由にご利用ください。貢献したい場合は[**good first issues**](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)をチェックしてください - あらゆる種類の貢献を歓迎します。
* **貢献：** コードや改善を貢献したい場合は、始め方について[貢献ガイド](CONTRIBUTING.md)を参照してください。すべてのPRとフィードバックを感謝します。協力することで、Julepをさらに良くすることができます！

*プロのヒント： <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/e379a33a-b428-4385-b44f-3da16e7bac9f" width="35"> リポジトリにスターを付けて最新情報を入手してください - 新機能と例を継続的に追加しています。*    

<br/>

あなたの貢献は、大きいものも小さいものも、私たちにとって価値があります。一緒に素晴らしいものを構築しましょう！    <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">
 <img src="https://user-images.githubusercontent.com/74038190/216125640-2783ebd5-e63e-4ed1-b491-627a40b24850.png" width="20">

<h4>素晴らしい貢献者たち：</h4>

<a href="https://github.com/julep-ai/julep/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=julep-ai/julep" />
</a>

<br/>

## ライセンス

Julepは**Apache 2.0ライセンス**の下で提供されており、これは自分のプロジェクトで自由に使用できることを意味します。詳細については[LICENSE](LICENSE)ファイルを参照してください。Julepでの構築をお楽しみください！