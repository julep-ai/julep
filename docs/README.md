---
description: Get started with Julep
layout:
  title:
    visible: true
  description:
    visible: false
  tableOfContents:
    visible: true
  outline:
    visible: false
  pagination:
    visible: true
---

# Introduction

Julep is a platform for developing stateful and functional LLM-powered applications.

## Why Julep?

We've built a lot of AI apps and understand how difficult it is to evaluate hundreds of tools, techniques, and models, and then make them work well together.

**The Problems**

1. The barrier to making LLM apps with memory, knowledge & tools is too high.
2. Agentic behavior is hard to control when done through multi-agent frameworks.

{% embed url="https://youtu.be/LhQMBAehL_Q" %}

## Features

* **Statefulness By Design**: Manages context by default. Uses [CozoDB](https://cozodb.org/) to save & retrieve conversation history, OpenAPI specification tools & documents.
* **Support for Users & Agents**: Allows creating different user <--> agent interactions like `One Agent <-> Many Users`;  etc. Read more: [Broken link](broken-reference "mention")&#x20;
* **Use and switch between any LLMs anytime**: Switch and use different LLMs, providers, and models, self-hosted or otherwise.
* **90+ tools built-in**: Connect your AI app to 150+ third-party applications using [Composio](https://docs.composio.dev/framework/julep/) natively.
* **Production-ready**: Julep comes ready to be deployed to production using Docker Compose. Support for k8s coming soon!
* **GitHub Actions-like workflows for tasks**: Define agentic workflows to be executed asynchronously with one or more without worrying about timeouts or multiplying hallucinations. (coming soon!)
