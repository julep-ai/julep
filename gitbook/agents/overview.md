---
description: Launching soon!
---

# Overview

## What are Agents?

An Agent is a program that uses foundational language models to carry out complex tasks. It is provided with a task, described in natural language and a set of tools to aid in completing said tasks.

## How does an Agent work?

The agents on Julep AI platform work through a series of steps

1. **Analyse the Request**: The agent begins by analysing the request and selecting the appropriate tools automatically.&#x20;
2. **Plan Execution**: It then creates a plan, a list of steps to execute to accomplish the task.&#x20;
3. **Execute Steps**: The agent executes the next step by working with the required tools.&#x20;
4. **Analyse Results**: After each action, the agent analyses the result of the execution.

Strictly speaking, an agent is actually just a software pattern that codifies complex task handling as a sequence of `ANALYZE -> PLAN -> EXECUTION.`

***

## Agent components

### Agents

At the heart of Julep AI are the _Agents_—autonomous applications designed to perform tasks using advanced language models. Each agent possesses a unique identity, defined by characteristics such as name, description, metadata, and a set of instructions. They function by planning actions, choosing tools, and executing steps towards achieving specific goals.

### Memories and Scoping

Agents in Julep AI have a nuanced memory system, storing and recalling _Memories_ in three categories:&#x20;

* Episodic (events)
* Implicit (beliefs)
* Semantic (facts and information).&#x20;

They are akin to a human's recollection of past experiences and acquired knowledge and their design was influenced by ideas from contemporary cognitive science.

Memories allow agents to continuously learn from user engagements and task executions. They enhance its ability to adapt and respond effectively over time, significantly personalising the user experience.

Memories are specific to a given user, allowing agents to provide personalised interactions and retain crucial context from previous engagements but also maintaining privacy and granular control.

### Sessions

_Sessions_ are interactive scenarios where a user engages with an agent in a conversational format, with the agent responding in real-time.&#x20;

A user can basically "talk" to an agent inside a session where the responses are expected to be immediately returned. The agent can access memories, follow sophisticated prompts and run _Instant Tools_ (tools that have predictable latency and can be executed mid-inference).

For longer and more complex actions, you can use _Tasks_ which allow for long-running operations and have access to more powerful tools like _API Calls_, a _Web Browser_, etc at the expense of being run asynchronously. Sessions can invoke tasks by the same agent autonomously but don't wait for completion of the task.

### Tasks, Scheduling and Runs

Tasks are more complex operations that may run over an extended period, involving multiple steps and tools. While sessions are for immediate interaction, tasks are structured to handle long-term objectives, acting as automated workflows.

Every task is essentially a State Machine definition where the LLM dynamically decides the transitions of the states. In order to invoke a task, one can either use the API or by creating a _Scheduled Task_ which defines a fixed timestamp, timer or an interval that automatically invokes the task. The agents can initiate tasks at predetermined times or intervals, ensuring timely execution of operations without manual intervention.

Each execution of a session or task is a Run, with its own unique run\_id. Runs track the progress of agents' actions, managing transitions and maintaining state, critical for monitoring and continuity.
