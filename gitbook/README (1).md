# Welcome!

## Making AI Apps is hard.

Production-ready AI applications follow the Pareto principle when it comes to engineering effort. The last 20% takes 80% of the effort. We faced a lot of _challenges_ building our own AI applications;

* Prompt Engineering
* Getting unfiltered responses from conversations
* Controlling hallucinations with accurate grounding
* Building [RAG](https://ai.meta.com/blog/retrieval-augmented-generation-streamlining-the-creation-of-intelligent-natural-language-processing-models/) pipelines (it's hard - No other reason why vector DBs would raise millions in funding)
* Unpredictable pricing and/or lack of transparency with agent platforms
* Growing context windows that lack automatic managements

Engineering teams need to handle ALL these _new_ problems alongside maintaining their own code base and developing their application.

***

## Introduction

Julep is aiming to be a more refined platform for creating AI products.

Julep AI is building an ecosystem to build better AI products: ​

1. Agents Platform, with memory, built-in integrations, long running context, etc ​
2. Fine-tuned models, with native function calling and extended function ​ These 2 products can help developers to;
   1. Control models
   2. Manage context
   3. Build agentic applications

Following an opinionated approach to building Agents and LLM apps, we aim to "bake-in" essential features in a platform to aid development speed to significantly improve the development experience speed-up the iteration process of launching an AI product.

***

## Our take on Agents

The core goal at Julep is to create a platform for building agents from a specification containing instructions and tools.

As we launch our Agents Platform, we aim to offer:

* Ability to orchestrate prompt, and hence execution of each step of execution
* Independent long running tasks
* Automatic context management
* Episodic and Semantic Memory

<figure><img src=".gitbook/assets/implicit_memory.excalidraw.png" alt=""><figcaption></figcaption></figure>

***

## Our take on Models

Language Models lay at the foundation of autonomous agents.  If an Agent is stateful specification of possible actions and instructions, then an LLM acts as the _finite state machine_ executor that executes those actions.

Predictable and controllable Model behaviour leads to predictable and controllable Agent behaviour.

Hence, a good developer experience in prompting and using the model for actual work use cases like RAG, conversations and function-calling (alpha) has been baked in to the `samantha-1-turbo` models.
