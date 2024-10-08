# Core Concepts in Julep

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


Julep is a powerful backend system for managing agent execution. It provides several key components that work together to create flexible and intelligent applications. Here are the core concepts:

## Agent

An Agent in Julep is the main orchestrator of your application. Agents are backed by foundation models like GPT4 or Claude and use interaction history to determine their next actions. Key features include:

- Long-lived interactions in sessions
- Integration with system or user-defined tools
- Access to agent-level documents for auto-retrieval
- Ability to define and execute multi-step workflows (tasks)

## User

Users in Julep can be associated with sessions. They are used to scope memories formed by agents and can hold metadata for reference in sessions or task executions.

## Session

Sessions are the main workhorse for Julep apps:
- They facilitate interactions with agents
- Each session maintains its own context
- Can have one or more agents and zero or more users
- Allows control over context overflow handling

## Tool

Tools in Julep are programmatic interfaces that foundation models can "call" with inputs to achieve a goal. They can be:
1. User-defined functions
2. System tools (upcoming)
3. Built-in integrations (upcoming)
4. Webhooks & API calls (upcoming)

## Doc

Docs are collections of text snippets (with planned image support) indexed into a built-in vector database. They can be scoped to an agent or a user and are automatically recalled in sessions when relevant.

## Task

Tasks in Julep are Github Actions-style workflows that define long-running, multi-step actions. They allow for complex operations by defining steps and have access to all Julep integrations.

## Execution

An Execution is an instance of a Task that has been started with some input. It can be in various states (e.g., queued, running, awaiting input, succeeded, failed) and follows a specific state transition model.

These core concepts form the foundation of Julep's functionality, allowing for the creation of sophisticated, context-aware applications with powerful agent capabilities.