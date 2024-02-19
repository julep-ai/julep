# Welcome!

## Making AI Apps is hard.

Production level AI applications follow the Pareto principle when it comes to engineering effort. The last 20% takes 80% of the effort. We faced a lot of challenges building our own AI applications;

* Prompt engineering.
* Hassle to get unfiltered conversational responses.
* Hallucinations and accurate grounding.
* RAG is inherently hard. No other reason why vector DBs would raise millions in funding.
* Agentic / Assistant platforms often have unpredictable behaviour and low transparency.
* Agentic /  Assistant platform have unpredictable pricing.
* Ever-growing context windows lack automatic management.

Engineering teams need to handle ALL these _new_ problems alongside maintaining their own code base and developing their application.

***

## Introduction

Julep is aiming to be a more refined platform for creating AI products.

Following an opinionated approach to building Agents and LLM apps, we aim to "bake-in" essential features to significantly improve the development experience speed-up the iteration process of launching an AI product.

***

## Opinionated Agents

The core goal at Julep is to create a platform for building agents from a specification containing instructions and tools.

As we launch our Agents Platform, we aim to offer:

* Ability to orchestrate prompt, and hence execution of each step of execution
* Independent long running tasks
* Automatic context management
* Episodic and Semantic Memory

<figure><img src=".gitbook/assets/implicit_memory.excalidraw.png" alt=""><figcaption></figcaption></figure>

***

## Opinionated Models

Language Models lay at the foundation of autonomous agents.  If an Agent is stateful specification of possible actions and instructions, then an LLM acts as the _finite state machine_ executor that executes those actions.

Predictable and controllable Model behaviour leads to predictable and controllable Agent behaviour.

Hence, a good developer experience in prompting and using the model for actual work use cases like RAG, conversations and function-calling (alpha) has been baked in to the `samantha-1-turbo` models.
