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

We've built a lot of AI apps and understand how difficult it is to evaluate hundreds of tools, techniques, and models, and then make them work well together. In our early days, we built sales bots for Shopify stores and had to repeat this process several times.

Even for simple apps you have to:

* pick the right language model for your use case
* pick the right framework
* pick the right embedding model
* choose the vector store and RAG pipeline
* build integrations&#x20;
* tweak all of the parameters (temp, penalty, max tokens, similarity thresholds, chunk size, and so on)&#x20;
* write and iterate on prompts for them to work
* and repeat this whole process when a new framework, model or integration comes out next week

This is so tiring and cumbersome. We want to build a better way that "just works" so you can build your _AI app 10x faster with 0 decision burden_**.**



{% embed url="https://www.youtube.com/watch?v=4VMMN--oMO8" %}
A short intro to Julep
{% endembed %}

## Features

* **Statefulness By Design**: Build AI apps without needing to write code to embed, save, and retrieve conversation history. Deals with context windows by using CozoDB; a transactional, relational-graph-vector database.
* **Automatic Function Calling**: Julep deals with calling the function, parsing the response, retrying in case of failures, and passing the response into the context.
* **Production-ready**: Julep comes ready to be deployed to production using Docker Compose. Support for k8s coming soon!
* \***Cron-like asynchronous functions**: Support for functions to be executed periodically and asynchronously.
* \***90+ tools built-in**: Connect your AI app to 150+ third-party applications using [Composio](https://composio.dev/) natively.
* \***Use and switch between any LLMs anytime**: Switch and use different LLMs, providers, and models, self-hosted or otherwise by changing only _one line of code_
